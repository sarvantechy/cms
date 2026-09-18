#!/usr/bin/env bash
set -euo pipefail
export AWS_PAGER=""

AWS_PROFILE="dev"
AWS_REGION="ap-south-2"
INSTANCE_ID="i-0baf4f73e58afd63d"
S3_BUCKET="scoringbasket"
S3_PREFIX="4by4-cms/bootstrap"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

command -v jq >/dev/null || { echo "jq is required" >&2; exit 1; }
command -v aws >/dev/null || { echo "AWS CLI is required" >&2; exit 1; }

aws s3 cp "$REPO_ROOT/deployment/4by4-cms-demo.service" \
  "s3://$S3_BUCKET/$S3_PREFIX/4by4-cms-demo.service" \
  --profile "$AWS_PROFILE" --region "$AWS_REGION"
aws s3 cp "$REPO_ROOT/deployment/nginx-https.conf" \
  "s3://$S3_BUCKET/$S3_PREFIX/nginx-https.conf" \
  --profile "$AWS_PROFILE" --region "$AWS_REGION"

read -r -d '' REMOTE_SCRIPT <<'SCRIPT' || true
set -euo pipefail

APP_ROOT=/opt/4by4-cms
WEB_ROOT=/var/www/ias-cms
STATE_ROOT=/var/lib/4by4-cms
MEDIA_ROOT=$STATE_ROOT/media
BACKUP_ROOT=$STATE_ROOT/backups
VENV=$APP_ROOT/.venv
ENV_FILE=/etc/4by4-cms-demo.env
DATABASE_NAME=cms
MIGRATION_ROLE=cms_owner
RUNTIME_ROLE=cms_runtime
NGINX_CONFIG=/etc/nginx/conf.d/ias-cms.conf

command -v python3.12 >/dev/null
command -v psql >/dev/null
command -v pg_dump >/dev/null
command -v nginx >/dev/null
command -v aws >/dev/null

if ss -ltn | grep -q ':8005 '; then
  echo 'Port 8005 is already in use' >&2
  exit 1
fi

id cms-demo >/dev/null 2>&1 || useradd --system --home-dir "$APP_ROOT" --shell /sbin/nologin cms-demo
install -d -o root -g root -m 755 "$APP_ROOT" "$WEB_ROOT"
install -d -o cms-demo -g cms-demo -m 750 "$STATE_ROOT" "$MEDIA_ROOT"
install -d -o root -g cms-demo -m 750 "$BACKUP_ROOT"

if [[ ! -x "$VENV/bin/python" ]]; then
  python3.12 -m venv "$VENV"
fi
"$VENV/bin/pip" install --quiet --upgrade pip

if [[ ! -f "$ENV_FILE" ]]; then
  migration_password=$(openssl rand -hex 32)
  runtime_password=$(openssl rand -hex 32)
  secret_key=$(openssl rand -hex 48)

  sudo -u postgres psql --set=ON_ERROR_STOP=1 \
    --set=migration_password="$migration_password" \
    --set=runtime_password="$runtime_password" <<'SQL'
DO $roles$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cms_owner') THEN
    CREATE ROLE cms_owner LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cms_runtime') THEN
    CREATE ROLE cms_runtime LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS;
  END IF;
END
$roles$;
ALTER ROLE cms_owner PASSWORD :'migration_password';
ALTER ROLE cms_runtime PASSWORD :'runtime_password';
SQL

  if ! sudo -u postgres psql --tuples-only --no-align --command \
    "SELECT 1 FROM pg_database WHERE datname = '$DATABASE_NAME'" | grep -qx 1; then
    sudo -u postgres createdb --owner="$MIGRATION_ROLE" "$DATABASE_NAME"
  fi
  sudo -u postgres psql --set=ON_ERROR_STOP=1 --dbname="$DATABASE_NAME" <<'SQL'
ALTER SCHEMA public OWNER TO cms_owner;
GRANT CONNECT ON DATABASE cms TO cms_runtime;
GRANT USAGE ON SCHEMA public TO cms_runtime;
SQL

  umask 077
  cat >"$ENV_FILE" <<ENV
ENVIRONMENT=demo
DATABASE_URL=postgresql+psycopg://cms_owner:$migration_password@127.0.0.1:5432/cms
RUNTIME_DATABASE_URL=postgresql+psycopg://cms_runtime:$runtime_password@127.0.0.1:5432/cms
CMS_OWNER_PASSWORD=$migration_password
SECRET_KEY=$secret_key
CORS_ORIGINS=https://ias-cms.4by4softwares.com
MEDIA_STORAGE_PATH=/var/lib/4by4-cms/media
ENV
fi
chown root:cms-demo "$ENV_FILE"
chmod 640 "$ENV_FILE"

aws s3 cp s3://scoringbasket/4by4-cms/bootstrap/4by4-cms-demo.service \
  /etc/systemd/system/4by4-cms-demo.service --region ap-south-2
if [[ -f "$NGINX_CONFIG" ]]; then
  cp "$NGINX_CONFIG" "$BACKUP_ROOT/ias-cms.conf.pre-full-stack"
fi
aws s3 cp s3://scoringbasket/4by4-cms/bootstrap/nginx-https.conf \
  /tmp/ias-cms-nginx.conf --region ap-south-2
install -m 0644 /tmp/ias-cms-nginx.conf "$NGINX_CONFIG"
if ! nginx -t; then
  if [[ -f "$BACKUP_ROOT/ias-cms.conf.pre-full-stack" ]]; then
    install -m 0644 "$BACKUP_ROOT/ias-cms.conf.pre-full-stack" "$NGINX_CONFIG"
  fi
  nginx -t
  exit 1
fi
rm -f /tmp/ias-cms-nginx.conf
systemctl daemon-reload
systemctl enable 4by4-cms-demo.service
systemctl reload nginx

echo 'CMS demo bootstrap complete: isolated database, roles, environment, media, service, and ias-cms proxy are ready'
SCRIPT

ssm_params=$(jq -n --arg script "$REMOTE_SCRIPT" '{commands: [$script]}')
command_id=$(aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name AWS-RunShellScript \
  --parameters "$ssm_params" \
  --comment "4by4 CMS demo bootstrap" \
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
