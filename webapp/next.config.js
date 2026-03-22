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
 * Пробрасываем в Next только NEXT_PUBLIC_* из корневого .env (например NEXT_PUBLIC_API_URL для dev).
 * TELEGRAM_BOT_USERNAME — только на бэкенде; WebApp читает через /api/webapp/config/.
 */
const rootEnvPath = path.join(__dirname, "..", ".env");
const parsed = parseEnvFile(rootEnvPath);
const nextPublicFromRoot = Object.fromEntries(
  Object.entries(parsed).filter(([k]) => k.startsWith("NEXT_PUBLIC_")),
);
/** SSR (generateMetadata): из корневого .env при next dev на хосте; в Docker задаёт compose. Не кладём в env — не светим в клиентском бандле. */
if (parsed.BACKEND_INTERNAL_URL) {
  process.env.BACKEND_INTERNAL_URL = String(parsed.BACKEND_INTERNAL_URL).trim();
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: nextPublicFromRoot,
};

module.exports = nextConfig;
