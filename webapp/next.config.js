const path = require("path");
const fs = require("fs");

/** Парсинг простого KEY=VAL (без многострочных значений). */
function parseEnvFile(filePath) {
  const result = {};
  if (!fs.existsSync(filePath)) return result;
  for (const line of fs.readFileSync(filePath, "utf8").split("\n")) {
    const t = line.trim();
    if (!t || t.startsWith("#")) continue;
    const eq = t.indexOf("=");
    if (eq === -1) continue;
    const key = t.slice(0, eq).trim();
    let val = t.slice(eq + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    result[key] = val;
  }
  return result;
}

/**
 * NEXT_PUBLIC_* из корневого .env + TELEGRAM_* для шаринга t.me (в Docker build args дублируют).
 */
const rootEnvPath = path.join(__dirname, "..", ".env");
const parsed = parseEnvFile(rootEnvPath);
const nextPublicFromRoot = Object.fromEntries(
  Object.entries(parsed).filter(([k]) => k.startsWith("NEXT_PUBLIC_")),
);
const telegramBotUser = (parsed.TELEGRAM_BOT_USERNAME || "").trim().replace(/^@/, "");
const telegramMiniappShort = (parsed.TELEGRAM_MINIAPP_SHORT_NAME || "").trim();
/** SSR (generateMetadata): из корневого .env при next dev на хосте; в Docker задаёт compose. Не кладём в env — не светим в клиентском бандле. */
if (parsed.BACKEND_INTERNAL_URL) {
  process.env.BACKEND_INTERNAL_URL = String(parsed.BACKEND_INTERNAL_URL).trim();
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    ...nextPublicFromRoot,
    NEXT_PUBLIC_TELEGRAM_BOT_USERNAME: telegramBotUser,
    NEXT_PUBLIC_TELEGRAM_MINIAPP_SHORT_NAME: telegramMiniappShort,
  },
};

module.exports = nextConfig;
