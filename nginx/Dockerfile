# Только для docker-compose.prod.yml: envsubst + шаблон nginx.prod.conf.template
FROM nginx:1.27-alpine
RUN apk add --no-cache gettext
COPY docker-entrypoint-prod.sh /docker-entrypoint-prod.sh
RUN chmod +x /docker-entrypoint-prod.sh
ENTRYPOINT ["/docker-entrypoint-prod.sh"]
