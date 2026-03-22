#!/usr/bin/env bash
# Выпуск или продление через webroot (nginx уже слушает :80 с /.well-known/acme-challenge/).
# Перед запуском: set -a && source .env && set +a
set -euo pipefail
cd "$(dirname "$0")/.."
: "${CERTBOT_EMAIL:?Задайте CERTBOT_EMAIL}"
: "${NGINX_SERVER_NAME:?Задайте NGINX_SERVER_NAME}"
DOMAINS=()
for d in ${NGINX_SERVER_NAME}; do
  DOMAINS+=(-d "$d")
done
docker compose -f docker-compose.prod.yml --profile certbot run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  "${DOMAINS[@]}" \
  --email "${CERTBOT_EMAIL}" \
  --agree-tos \
  --no-eff-email
docker compose -f docker-compose.prod.yml exec nginx nginx -s reload 2>/dev/null || true
