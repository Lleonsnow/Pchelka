"use client";

import { getWebAppConfig } from "./api";
import { getTelegramWebApp } from "./telegram";

function normId(s: string | undefined): string {
  return String(s ?? "")
    .replace(/[\r\n\t]+/g, "")
    .trim()
    .replace(/^@/, "");
}

/** Сначала переменные из next.config (Docker build / локальный .env), затем API. */
async function getSharingCfg(): Promise<{ bot: string; miniappShort: string }> {
  const fromBuild = {
    bot: normId(process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME),
    miniappShort: normId(process.env.NEXT_PUBLIC_TELEGRAM_MINIAPP_SHORT_NAME),
  };
  if (fromBuild.bot) {
    return fromBuild;
  }
  try {
    const c = await getWebAppConfig();
    return {
      bot: normId(c.telegram_bot_username),
      miniappShort: normId(c.miniapp_short_name),
    };
  } catch {
    return { bot: "", miniappShort: "" };
  }
}

function sanitizeUrl(u: string): string {
  return u.replace(/[\r\n\t]+/g, "").trim();
}

/**
 * Ссылка на товар: только t.me (Mini App / чат с ботом), без голого HTTPS сайта —
 * чтобы не уводить людей во внешний браузер.
 */
async function productEntryUrl(productId: number): Promise<string | null> {
  const { bot, miniappShort } = await getSharingCfg();
  if (bot && miniappShort) {
    return sanitizeUrl(`https://t.me/${bot}/${miniappShort}?startapp=product_${productId}`);
  }
  if (bot) {
    return sanitizeUrl(`https://t.me/${bot}?start=product_${productId}`);
  }
  if (typeof window !== "undefined") {
    const origin = sanitizeUrl(window.location?.origin || "");
    if (origin && /^https?:\/\//i.test(origin)) {
      return sanitizeUrl(`${origin.replace(/\/$/, "")}/catalog/product/${productId}`);
    }
  }
  return null;
}

export type ShareProductResult = "telegram_picker" | "native_share" | "copied" | "noop";

export async function shareProductLink(
  productName: string,
  productId: number,
): Promise<ShareProductResult> {
  const urlToShare = sanitizeUrl((await productEntryUrl(productId)) || "");
  if (!urlToShare) return "noop";

  const shareParams = new URLSearchParams({ url: urlToShare });
  const shareHref = `https://t.me/share/url?${shareParams.toString()}`;

  const twa = getTelegramWebApp() as { openTelegramLink?: (u: string) => void } | null | undefined;

  if (twa?.openTelegramLink) {
    twa.openTelegramLink(shareHref);
    return "telegram_picker";
  }

  if (typeof navigator !== "undefined" && typeof navigator.share === "function") {
    const payload: ShareData = {
      title: productName.trim() || "Товар",
      url: urlToShare,
    };
    navigator.share(payload).catch(() => {});
    return "native_share";
  }

  if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
    const name = productName.replace(/[\r\n\t]+/g, " ").trim();
    const line = name ? `🛒 ${name} — ${urlToShare}` : urlToShare;
    void navigator.clipboard.writeText(line);
    return "copied";
  }

  return "noop";
}
