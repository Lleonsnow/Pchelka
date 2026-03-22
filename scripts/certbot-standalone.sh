#!/usr/bin/env bash
# Первый выпуск сертификата, пока в ./ssl ещё нет fullchain.pem.
# Останавливает nginx (освобождает :80), поднимает certbot --standalone.
# Перед запуском: set -a && source .env && set +a  (нужны NGINX_SERVER_NAME, CERTBOT_EMAIL)
set -euo pipefail
cd "$(dirname "$0")/.."
: "${NGINX_SERVER_NAME:?Задайте NGINX_SERVER_NAME (один или несколько доменов через пробел)}"
: "${CERTBOT_EMAIL:?Задайте CERTBOT_EMAIL}"
DOMAIN_ARGS=()
for d in ${NGINX_SERVER_NAME}; do
  DOMAIN_ARGS+=(-d "$d")
done
docker compose -f docker-compose.prod.yml stop nginx 2>/dev/null || true
docker compose -f docker-compose.prod.yml run --rm -p 80:80 --profile certbot certbot certonly \
  --standalone \
  --preferred-challenges http \
  "${DOMAIN_ARGS[@]}" \
  --email "${CERTBOT_EMAIL}" \
  --agree-tos \
  --no-eff-email
docker compose -f docker-compose.prod.yml up -d nginx
