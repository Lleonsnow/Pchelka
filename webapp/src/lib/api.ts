"use client";

import { getInitData, getTelegramWebApp } from "./telegram";

// При открытии с порта 3000 (HMR) — бэкенд на 8000. Иначе тот же домен (nginx/ngrok) или NEXT_PUBLIC_API_URL.
function getApiBase(): string {
  if (typeof window !== "undefined" && window.location.port === "3000") {
    return "http://localhost:8000";
  }
  if (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  return "";
}
const API_BASE = getApiBase();

const WEBAPP_PREFIX = "/api/webapp";

function getHeaders(): HeadersInit {
  const initData = getInitData();
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  if (initData) {
    (headers as Record<string, string>)["X-Telegram-Init-Data"] = initData;
  }
  return headers;
}

function isNetworkError(e: unknown): boolean {
  const msg = e instanceof Error ? e.message : String(e);
  return (
    msg === "Failed to fetch" ||
    msg === "Load failed" ||
    (e instanceof TypeError && msg.includes("fetch"))
  );
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${WEBAPP_PREFIX}${path}`;
  let res: Response;
  try {
    res = await fetch(url, {
      ...options,
      headers: { ...getHeaders(), ...options.headers },
    });
  } catch (e) {
    if (isNetworkError(e)) {
      throw new Error(
        "Не удалось подключиться к серверу. Проверьте интернет и настройку NEXT_PUBLIC_API_URL для Telegram."
      );
    }
    throw e;
  }
  if (!res.ok) {
    const text = await res.text();
    let detail = text;
    try {
      const j = JSON.parse(text);
      detail = j.detail ?? text;
    } catch {
      // ignore
    }
    if (res.status === 401 && (detail === "Unauthorized" || detail.toLowerCase().includes("unauthorized"))) {
      const hasTelegram = typeof window !== "undefined" && !!getTelegramWebApp();
      const hasInitData = typeof window !== "undefined" && !!getInitData();
      if (hasTelegram && !hasInitData) {
        throw new Error(
          "Сессия не передана. Откройте магазин через кнопку меню бота в Telegram (не по прямой ссылке в браузере)."
        );
      }
      throw new Error(
        "Не удалось войти. Убедитесь, что открыли магазин из того же бота. Если ошибка повторяется — проверьте BOT_TOKEN на сервере."
      );
    }
    throw new Error(detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export type Category = {
  id: number;
  name: string;
  slug: string;
  order: number;
  parent: number | null;
  children_count: number;
};

export type Product = {
  id: number;
  name: string;
  slug: string;
  price: string;
  category: number;
  image_url: string | null;
};

export type ProductDetail = Product & {
  description: string;
  image_urls: string[];
};

export type CartItem = {
  id: number;
  product_id: number;
  product_name: string;
  price: string;
  quantity: number;
  subtotal: string;
};

export type CartResponse = {
  items: CartItem[];
  total: string;
};

export type FaqItem = {
  id: number;
  question: string;
  answer: string;
  order: number;
};

export type WebAppConfig = {
  telegram_bot_username: string;
  /** Короткое имя из BotFather → t.me/bot/SHORT?startapp=… Пусто — шаринг через ?start= в чат с ботом. */
  miniapp_short_name: string;
};

/** Публичный конфиг WebApp (бот + short name Mini App). */
export async function getWebAppConfig(): Promise<WebAppConfig> {
  return apiFetch<WebAppConfig>("/config/");
}

/** Публичный список FAQ (доступен без авторизации). */
export async function getFaq(): Promise<FaqItem[]> {
  return apiFetch<FaqItem[]>("/faq/");
}

export type WebAppMe = {
  phone: string;
  first_name: string;
  last_name: string;
};

/** Телефон и имя из профиля (после контакта в боте). Требует X-Telegram-Init-Data. */
export async function getMe(): Promise<WebAppMe> {
  return apiFetch<WebAppMe>("/me/");
}

export async function getCategories(parentId?: number): Promise<Category[]> {
  const q = parentId != null ? `?parent_id=${parentId}` : "";
  return apiFetch<Category[]>(`/catalog/categories/${q}`);
}

export async function getProducts(categoryId?: number, search?: string): Promise<Product[]> {
  const params = new URLSearchParams();
  if (categoryId != null) params.set("category_id", String(categoryId));
  if (search) params.set("search", search);
  const q = params.toString() ? `?${params}` : "";
  return apiFetch<Product[]>(`/catalog/products/${q}`);
}

export async function getProduct(id: number): Promise<ProductDetail> {
  return apiFetch<ProductDetail>(`/catalog/products/${id}/`);
}

export async function getCart(): Promise<CartResponse> {
  return apiFetch<CartResponse>("/cart/");
}

export async function clearCart(): Promise<void> {
  return apiFetch<void>("/cart/", { method: "DELETE" });
}

export async function addToCart(productId: number, quantity = 1): Promise<CartResponse> {
  return apiFetch<CartResponse>("/cart/add/", {
    method: "POST",
    body: JSON.stringify({ product_id: productId, quantity }),
  });
}

export async function updateCartItem(productId: number, quantity: number): Promise<CartResponse> {
  return apiFetch<CartResponse>(`/cart/update/${productId}/`, {
    method: "PATCH",
    body: JSON.stringify({ quantity }),
  });
}

export async function removeFromCart(productId: number): Promise<CartResponse> {
  return apiFetch<CartResponse>(`/cart/remove/${productId}/`, { method: "DELETE" });
}

export type OrderListItem = {
  id: number;
  status: string;
  total: string;
  created_at: string;
};

export async function getOrders(): Promise<OrderListItem[]> {
  return apiFetch<OrderListItem[]>("/orders/");
}

export async function createOrder(data: {
  full_name: string;
  address: string;
  phone: string;
}): Promise<{ id: number; total: string; status: string }> {
  return apiFetch("/orders/create/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
