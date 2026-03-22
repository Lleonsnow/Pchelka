"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ImageOff, Minus, Plus, Share2, ShoppingBag } from "lucide-react";
import type { ProductDetail } from "@/lib/api";
import { shareProductLink } from "@/lib/shareProduct";

type Props = {
  product: ProductDetail;
  /** Количество этой позиции в корзине (0 — только кнопка «В корзину»). */
  quantityInCart: number;
  cartBusy: boolean;
  onAddToCart: () => void;
  onCartDelta: (delta: number) => void;
};

export function ProductDetailView({
  product,
  quantityInCart,
  cartBusy,
  onAddToCart,
  onCartDelta,
}: Props) {
  const images = (product.image_urls ?? [])
    .map((s) => (typeof s === "string" ? s.replace(/[\r\n\t]+/g, "").trim() : ""))
    .filter(Boolean);
  const trackRef = useRef<HTMLDivElement>(null);
  const [activeIdx, setActiveIdx] = useState(0);
  const [shareHint, setShareHint] = useState<string | null>(null);

  const onScrollTrack = useCallback(() => {
    const el = trackRef.current;
    if (!el || images.length <= 1) return;
    const w = el.clientWidth || 1;
    setActiveIdx(Math.min(images.length - 1, Math.round(el.scrollLeft / w)));
  }, [images.length]);

  useEffect(() => {
    const el = trackRef.current;
    if (!el) return;
    el.addEventListener("scroll", onScrollTrack, { passive: true });
    return () => el.removeEventListener("scroll", onScrollTrack);
  }, [onScrollTrack, images.length]);

  const showShareHint = useCallback((msg: string) => {
    setShareHint(msg);
    window.setTimeout(() => setShareHint(null), 2600);
  }, []);

  const handleShare = async () => {
    const r = await shareProductLink(product.name, product.id);
    if (r === "copied") showShareHint("Ссылка скопирована");
    else if (r === "noop") showShareHint("Не удалось открыть отправку");
  };

  return (
    <article className="productDetail">
      <div className="productDetail__galleryWrap">
        {images.length > 0 ? (
          <>
            <div className="productDetail__track" ref={trackRef}>
              {images.map((src, i) => (
                <div key={`${src}-${i}`} className="productDetail__slide">
                  <img
                    src={src}
                    alt={i === 0 ? product.name : ""}
                    className="productDetail__slideImg"
                    loading={i === 0 ? "eager" : "lazy"}
                  />
                </div>
              ))}
            </div>
            {images.length > 1 && (
              <div className="productDetail__dots" role="tablist" aria-label="Фото товара">
                {images.map((_, i) => (
                  <span
                    key={i}
                    role="presentation"
                    className={
                      i === activeIdx ? "productDetail__dot productDetail__dot--active" : "productDetail__dot"
                    }
                  />
                ))}
              </div>
            )}
          </>
        ) : (
          <div className="productDetail__placeholder">
            <ImageOff size={56} strokeWidth={1.25} aria-hidden className="productDetail__placeholderIcon" />
          </div>
        )}
      </div>

      <div className="productDetail__sheet">
        <div className="productDetail__rowTop">
          <span className="productDetail__badge">В каталоге</span>
          <button
            type="button"
            className="btn btn--secondary btn--icon productDetail__shareBtn"
            onClick={handleShare}
            aria-label="Поделиться ссылкой на товар в Telegram"
          >
            <Share2 size={20} strokeWidth={2} aria-hidden />
          </button>
        </div>

        <h1 className="productDetail__title">{product.name}</h1>

        <div className="productDetail__priceRow">
          <span className="productDetail__price">{product.price}</span>
          <span className="productDetail__priceSuffix">₽</span>
        </div>

        {product.description ? (
          <p className="productDetail__desc">{product.description}</p>
        ) : null}

        <div className="productDetail__actions">
          <p className="productDetail__hint">{shareHint ?? "\u00a0"}</p>

          {quantityInCart > 0 ? (
            <div className="productDetail__inCart">
              <p className="productDetail__inCartLabel">
                Уже в корзине: <strong>{quantityInCart}</strong> шт.
              </p>
              <div className="productDetail__inCartRow">
                <div className="qtyControl productDetail__qtyControl" aria-label="Количество в корзине">
                  <button
                    type="button"
                    aria-label="Уменьшить"
                    disabled={cartBusy}
                    onClick={() => onCartDelta(-1)}
                    className="qtyControl__btn"
                  >
                    <Minus size={16} strokeWidth={2.5} aria-hidden />
                  </button>
                  <span className="qtyControl__value">{quantityInCart}</span>
                  <button
                    type="button"
                    aria-label="Увеличить"
                    disabled={cartBusy}
                    onClick={() => onCartDelta(1)}
                    className="qtyControl__btn"
                  >
                    <Plus size={16} strokeWidth={2.5} aria-hidden />
                  </button>
                </div>
                {cartBusy ? (
                  <span className="productDetail__inCartBusy">Обновляем…</span>
                ) : null}
              </div>
            </div>
          ) : (
            <button
              type="button"
              onClick={onAddToCart}
              disabled={cartBusy}
              className="btn btn--primary btn--full productDetail__cta"
            >
              <ShoppingBag size={20} strokeWidth={2} aria-hidden className="productDetail__ctaIcon" />
              {cartBusy ? "Добавляем…" : "В корзину"}
            </button>
          )}
        </div>
      </div>
    </article>
  );
}
