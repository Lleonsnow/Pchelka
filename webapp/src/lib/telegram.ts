"use client";

export function getTelegramWebApp() {
  if (typeof window === "undefined") return null;
  return window.Telegram?.WebApp ?? null;
}

export function getInitData(): string {
  const twa = getTelegramWebApp();
  return twa?.initData ?? "";
}

export function getThemeParams() {
  const twa = getTelegramWebApp();
  return twa?.themeParams ?? {};
}

/** BackButton поддерживается начиная с 6.1; в 6.0 SDK пишет предупреждение в консоль. */
function isBackButtonSupported(): boolean {
  const twa = getTelegramWebApp();
  if (!twa?.BackButton) return false;
  const v = twa.version;
  if (v == null || v === "") return false;
  const n = parseFloat(v);
  return !Number.isNaN(n) && n >= 6.1;
}

export function setupBackButton(onClick: () => void) {
  if (!isBackButtonSupported()) return;
  try {
    const twa = getTelegramWebApp();
    twa!.BackButton.show();
    twa!.BackButton.onClick(onClick);
  } catch {
    // ignore
  }
}

export function hideBackButton() {
  if (!isBackButtonSupported()) return;
  try {
    getTelegramWebApp()?.BackButton?.hide();
  } catch {
    // ignore
  }
}

export function setupMainButton(text: string, onClick: () => void) {
  try {
    const twa = getTelegramWebApp();
    if (twa?.MainButton) {
      twa.MainButton.setText(text);
      twa.MainButton.onClick(onClick);
      twa.MainButton.show();
    }
  } catch {
    // MainButton может быть недоступен вне Telegram
  }
}

export function hideMainButton() {
  try {
    getTelegramWebApp()?.MainButton?.hide();
  } catch {
    // MainButton может быть недоступен вне Telegram
  }
}

export function notifyReady() {
  getTelegramWebApp()?.ready();
}
