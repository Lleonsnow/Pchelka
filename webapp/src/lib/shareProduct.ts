"use client";

import { getWebAppConfig } from "./api";
import { getTelegramWebApp } from "./telegram";

let sharingCfgPromise: Promise<{ bot: string; miniappShort: string }> | null = null;

async function getSharingCfg(): Promise<{ bot: string; miniappShort: string }> {
  if (!sharingCfgPromise) {
    sharingCfgPromise = (async () => {
      try {
        const c = await getWebAppConfig();
        const norm = (s: string) =>
          String(s || "")
            .replace(/[\r\n\t]+/g, "")
            .trim();
        return {
          bot: norm(c.telegram_bot_username || "").replace(/^@/, ""),
          miniappShort: norm(c.miniapp_short_name || ""),
        };
      } catch {
        return { bot: "", miniappShort: "" };
      }
    })();
  }
  return sharingCfgPromise;
}

function sanitizeUrl(u: string): string {
  return u.replace(/[\r\n\t]+/g, "").trim();
}

/**
 * В Mini App шарим HTTPS-URL страницы товара — у Telegram нормальное превью (og из layout).
 * Иначе — t.me (WebApp short name или ?start= в чат с ботом).
 */
async function productEntryUrl(productId: number): Promise<string | null> {
  if (typeof window !== "undefined") {
    const origin = sanitizeUrl(window.location?.origin || "");
    if (origin && /^https?:\/\//i.test(origin)) {
      return sanitizeUrl(`${origin.replace(/\/$/, "")}/catalog/product/${productId}`);
    }
  }
  const { bot, miniappShort } = await getSharingCfg();
  if (bot && miniappShort) {
    return sanitizeUrl(`https://t.me/${bot}/${miniappShort}?startapp=product_${productId}`);
  }
  if (bot) {
    return sanitizeUrl(`https://t.me/${bot}?start=product_${productId}`);
  }
  if (typeof window !== "undefined") {
    return sanitizeUrl(`${window.location.origin}/catalog/product/${productId}`);
  }
  return null;
}

export type ShareProductResult = "telegram_picker" | "native_share" | "copied" | "noop";

export async function shareProductLink(
  productName: string,
  productId: number,
): Promise<ShareProductResult> {
  const urlToShare = sanitizeUrl(await productEntryUrl(productId) || "");
  if (!urlToShare) return "noop";

  /**
   * t.me/share/url с отдельными url + text даёт в чате две «голые» строки без единой карточки.
   * Одна ссылка в параметре url — клиент Telegram чаще показывает превью t.me и нормальный переход в бота.
   * Название передаём только в нативный share (title), не дублируем text+url.
   */
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
