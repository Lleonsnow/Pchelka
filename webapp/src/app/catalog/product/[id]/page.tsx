"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { setupBackButton, hideBackButton } from "@/lib/telegram";
import { useAsyncData } from "@/lib/useAsyncData";
import { ProductDetailView } from "@/components/ProductDetailView";
import {
  getProduct,
  getCart,
  addToCart,
  updateCartItem,
  removeFromCart,
  type ProductDetail,
} from "@/lib/api";

export default function ProductPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);
  const [cartBusy, setCartBusy] = useState(false);

  const { data: product, loading, error, setError } = useAsyncData<ProductDetail>(
    () => getProduct(id),
    [id],
  );

  const { data: cart, setData: setCart } = useAsyncData(() => getCart(), [id]);

  const quantityInCart = useMemo(() => {
    const item = cart?.items.find((i) => i.product_id === id);
    return item?.quantity ?? 0;
  }, [cart, id]);

  useEffect(() => {
    setupBackButton(() => router.back());
    return () => hideBackButton();
  }, [router]);

  const handleAddToCart = useCallback(() => {
    if (!product || cartBusy) return;
    setCartBusy(true);
    addToCart(product.id, 1)
      .then(setCart)
      .catch((e) => {
        setError(e.message);
      })
      .finally(() => {
        setCartBusy(false);
      });
  }, [product, cartBusy, setCart, setError]);

  const handleCartDelta = useCallback(
    (delta: number) => {
      if (!product || cartBusy) return;
      const next = quantityInCart + delta;
      setCartBusy(true);
      const done = () => setCartBusy(false);
      if (next < 1) {
        removeFromCart(product.id)
          .then(setCart)
          .catch((e) => setError(e.message))
          .finally(done);
        return;
      }
      updateCartItem(product.id, next)
        .then(setCart)
        .catch((e) => setError(e.message))
        .finally(done);
    },
    [product, cartBusy, quantityInCart, setCart, setError],
  );

  if (error) {
    return (
      <div className="page page--product">
        <p className="error-msg">{error}</p>
      </div>
    );
  }

  if (loading || !product) {
    return (
      <div className="page page--product">
        <div className="loading">Загрузка…</div>
      </div>
    );
  }

  return (
    <div className="page page--product">
      <ProductDetailView
        product={product}
        quantityInCart={quantityInCart}
        cartBusy={cartBusy}
        onAddToCart={handleAddToCart}
        onCartDelta={handleCartDelta}
      />
    </div>
  );
}
