"use client";

import { getInitData } from "./telegram";

const API_BASE =
  typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL
    ? process.env.NEXT_PUBLIC_API_URL
    : "http://localhost:8000";

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

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${WEBAPP_PREFIX}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: { ...getHeaders(), ...options.headers },
  });
  if (!res.ok) {
    const text = await res.text();
    let detail = text;
    try {
      const j = JSON.parse(text);
      detail = j.detail ?? text;
    } catch {
      // ignore
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

export async function createOrder(data: {
  full_name: string;
  address: string;
  phone: string;
}): Promise<{ id: number; total: string; status: string }> {
  return apiFetch("/orders/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
