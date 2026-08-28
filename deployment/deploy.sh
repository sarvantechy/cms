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
release_id="$(date -u +%Y%m%d%H%M%S)"

command -v jq >/dev/null || { echo "jq is required" >&2; exit 1; }
command -v aws >/dev/null || { echo "AWS CLI is required" >&2; exit 1; }

npm --prefix "$REPO_ROOT/web" run build
npm --prefix "$REPO_ROOT/web" run lint

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

install -d -o root -g root -m 755 "\$WEB_ROOT" "\$BACKUP_ROOT"
if [[ -f "\$NGINX_CONFIG" ]]; then
  cp "\$NGINX_CONFIG" "\$BACKUP_ROOT/ias-cms.conf.\$RELEASE_ID"
fi

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

for path in / /login; do
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
