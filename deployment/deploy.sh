#!/usr/bin/env bash
set -euo pipefail
export AWS_PAGER=""

AWS_PROFILE="dev"
AWS_REGION="ap-south-2"
INSTANCE_ID="i-0baf4f73e58afd63d"
S3_BUCKET="scoringbasket"
S3_PREFIX="4by4-cms/releases"
DEMO_HOST="ias-cms.4by4softwares.com"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_VENV="$REPO_ROOT/.venv-build"
release_id="$(date -u +%Y%m%d%H%M%S)"

command -v jq >/dev/null || { echo "jq is required" >&2; exit 1; }
command -v aws >/dev/null || { echo "AWS CLI is required" >&2; exit 1; }

python3.12 -m venv "$BUILD_VENV"
"$BUILD_VENV/bin/pip" install --quiet --upgrade build
rm -rf "$REPO_ROOT/backend/dist"
"$BUILD_VENV/bin/python" -m build --wheel --outdir "$REPO_ROOT/backend/dist" "$REPO_ROOT/backend"
wheel_files=("$REPO_ROOT"/backend/dist/*.whl)
wheel_file="${wheel_files[0]}"
wheel_name=$(basename "$wheel_file")

npm --prefix "$REPO_ROOT/web" run build

aws s3 cp "$wheel_file" "s3://$S3_BUCKET/$S3_PREFIX/$release_id/backend/$wheel_name" --profile "$AWS_PROFILE" --region "$AWS_REGION"
aws s3 cp "$REPO_ROOT/backend/alembic.ini" "s3://$S3_BUCKET/$S3_PREFIX/$release_id/backend/alembic.ini" --profile "$AWS_PROFILE" --region "$AWS_REGION"
aws s3 sync "$REPO_ROOT/backend/alembic/" "s3://$S3_BUCKET/$S3_PREFIX/$release_id/backend/alembic/" --delete --exclude '__pycache__/*' --exclude '*.pyc' --profile "$AWS_PROFILE" --region "$AWS_REGION"
aws s3 sync "$REPO_ROOT/web/dist/" "s3://$S3_BUCKET/$S3_PREFIX/$release_id/web/" \
  --delete --exclude '.DS_Store' --profile "$AWS_PROFILE" --region "$AWS_REGION"
aws s3 cp "$REPO_ROOT/deployment/nginx-https.conf" \
  "s3://$S3_BUCKET/$S3_PREFIX/$release_id/nginx/4by4-cms.conf" \
  --profile "$AWS_PROFILE" --region "$AWS_REGION"

read -r -d '' REMOTE_SCRIPT <<SCRIPT || true
set -euo pipefail
WEB_ROOT=/var/www/ias-cms
NGINX_CONFIG=/etc/nginx/conf.d/ias-cms.conf
BACKUP_ROOT=/var/lib/4by4-cms/backups
RELEASE_ID=$release_id

aws s3 cp s3://$S3_BUCKET/$S3_PREFIX/$release_id/backend/$wheel_name /tmp/$wheel_name --region $AWS_REGION
/opt/4by4-cms/.venv/bin/pip install --quiet --force-reinstall /tmp/$wheel_name
rm -f /tmp/$wheel_name
aws s3 cp s3://$S3_BUCKET/$S3_PREFIX/$release_id/backend/alembic.ini /opt/4by4-cms/alembic.ini --region $AWS_REGION
aws s3 sync s3://$S3_BUCKET/$S3_PREFIX/$release_id/backend/alembic/ /opt/4by4-cms/alembic/ --delete --region $AWS_REGION

install -d -o root -g root -m 755 "\$WEB_ROOT"
install -d -o root -g cms-demo -m 750 "\$BACKUP_ROOT"
if [[ -f "\$NGINX_CONFIG" ]]; then
  cp "\$NGINX_CONFIG" "\$BACKUP_ROOT/ias-cms.conf.\$RELEASE_ID"
fi

set -a
source /etc/4by4-cms-demo.env
set +a
cd /opt/4by4-cms
backup_path="\$BACKUP_ROOT/\$RELEASE_ID.sql.gz"
PGPASSWORD="\$CMS_OWNER_PASSWORD" pg_dump --host=127.0.0.1 --port=5432 --username=cms_owner --dbname=cms | gzip >"\$backup_path"
aws s3 cp "\$backup_path" s3://$S3_BUCKET/4by4-cms/backups/\$RELEASE_ID/database.sql.gz --region $AWS_REGION
if [[ -d /var/lib/4by4-cms/media ]]; then
  tar -C /var/lib/4by4-cms -czf "\$BACKUP_ROOT/\$RELEASE_ID-media.tar.gz" media
  aws s3 cp "\$BACKUP_ROOT/\$RELEASE_ID-media.tar.gz" s3://$S3_BUCKET/4by4-cms/backups/\$RELEASE_ID/media.tar.gz --region $AWS_REGION
fi
./.venv/bin/alembic -c alembic.ini upgrade head
DEMO_SEED_PASSWORD='Demo@1234567' ./.venv/bin/python -m app.commands.onboard_tenants --seed-demo

aws s3 sync s3://$S3_BUCKET/$S3_PREFIX/$release_id/web/ "\$WEB_ROOT/" --delete --region $AWS_REGION
aws s3 cp s3://$S3_BUCKET/$S3_PREFIX/$release_id/web/index.html "\$WEB_ROOT/index.html" --region $AWS_REGION
aws s3 cp s3://$S3_BUCKET/$S3_PREFIX/$release_id/nginx/4by4-cms.conf /tmp/4by4-cms-nginx.conf --region $AWS_REGION

previous_config=/tmp/ias-cms.previous.conf
if [[ -f "\$NGINX_CONFIG" ]]; then
  cp "\$NGINX_CONFIG" "\$previous_config"
fi
install -m 0644 /tmp/4by4-cms-nginx.conf "\$NGINX_CONFIG"
if ! nginx -t; then
  if [[ -f "\$previous_config" ]]; then
    install -m 0644 "\$previous_config" "\$NGINX_CONFIG"
  else
    rm -f "\$NGINX_CONFIG"
  fi
  nginx -t
  exit 1
fi
systemctl reload nginx
rm -f /tmp/4by4-cms-nginx.conf "\$previous_config"

systemctl restart 4by4-cms-demo.service
systemctl is-active --quiet 4by4-cms-demo.service

for attempt in {1..10}; do
  if curl --fail --silent http://127.0.0.1:8005/health/live >/dev/null; then
    break
  fi
  if [[ "\$attempt" == "10" ]]; then
    journalctl -u 4by4-cms-demo.service -n 40 --no-pager
    exit 1
  fi
  sleep 1
done

for path in / /login /health/live; do
  curl --fail --silent --show-error --resolve $DEMO_HOST:443:127.0.0.1 "https://$DEMO_HOST\$path" >/dev/null
 done

echo "CMS demo release \$RELEASE_ID deployed at https://$DEMO_HOST"
SCRIPT

parameters=$(jq -n --arg script "$REMOTE_SCRIPT" '{commands: [$script]}')
command_id=$(aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name AWS-RunShellScript \
  --parameters "$parameters" \
  --comment "4by4 CMS demo deploy $release_id" \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION" \
  --query Command.CommandId \
  --output text)
aws ssm wait command-executed \
  --command-id "$command_id" \
  --instance-id "$INSTANCE_ID" \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION"
aws ssm get-command-invocation \
  --command-id "$command_id" \
  --instance-id "$INSTANCE_ID" \
  --profile "$AWS_PROFILE" \
  --region "$AWS_REGION" \
  --query '[Status,StandardOutputContent,StandardErrorContent]' \
  --output text
