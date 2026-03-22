# Production: один этап — установка (включая dev для сборки), сборка, запуск next start.
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install && npm cache clean --force

COPY . .
# Тот же ключ на build и runtime (из .env / compose build args). openssl rand -base64 32
ARG NEXT_SERVER_ACTIONS_ENCRYPTION_KEY
ENV NEXT_SERVER_ACTIONS_ENCRYPTION_KEY=${NEXT_SERVER_ACTIONS_ENCRYPTION_KEY}
# Шаринг t.me в клиентском бандле (родительский .env в контексте build не виден)
ARG TELEGRAM_BOT_USERNAME=
ARG TELEGRAM_MINIAPP_SHORT_NAME=
ENV NEXT_PUBLIC_TELEGRAM_BOT_USERNAME=${TELEGRAM_BOT_USERNAME}
ENV NEXT_PUBLIC_TELEGRAM_MINIAPP_SHORT_NAME=${TELEGRAM_MINIAPP_SHORT_NAME}
RUN npm run build

ENV NODE_ENV=production
EXPOSE 3000
CMD ["npm", "run", "start"]
