#!/bin/sh
set -e
if [ -z "${NGINX_SERVER_NAME}" ]; then
  echo "NGINX_SERVER_NAME не задан (домен для server_name в .env)." >&2
  exit 1
fi
# Каталог certs: .../live/<SSL_LETSENCRYPT_HOST>/ (первый -d у certbot)
export SSL_LETSENCRYPT_HOST="${SSL_LETSENCRYPT_HOST:-$(echo "${NGINX_SERVER_NAME}" | awk '{print $1}')}"
envsubst '${NGINX_SERVER_NAME} ${SSL_LETSENCRYPT_HOST}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf
exec nginx -g 'daemon off;'
