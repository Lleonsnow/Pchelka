"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { hideBackButton, setupBackButton } from "@/lib/telegram";
import { getCategories, getProducts, type Category, type Product } from "@/lib/api";

function CatalogSkeleton({ kind }: { kind: "categories" | "products" }) {
  const count = kind === "categories" ? 6 : 6;
  return (
    <div className="catalogSkeletonGrid mt-2">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="skeletonCard">
          <div className="skeleton skeletonMedia" />
          <div className="skeleton skeletonLine skeletonLine--long" />
          <div className="skeleton skeletonLine skeletonLine--short" />
        </div>
      ))}
    </div>
  );
}

function CatalogPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const categoryId = searchParams.get("category");
  const productId = searchParams.get("product");
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const parentId = categoryId ? parseInt(categoryId, 10) : undefined;
  const isCategoryList = !categoryId && !productId;

  useEffect(() => {
    if (productId) {
      router.push(`/catalog/product/${productId}`);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    if (categoryId) {
      getProducts(parentId, search || undefined)
        .then((data) => {
          if (!cancelled) setProducts(data);
        })
        .catch((e) => {
          if (!cancelled) setError(e.message);
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    } else {
      getCategories()
        .then((data) => {
          if (!cancelled) setCategories(data);
        })
        .catch((e) => {
          if (!cancelled) setError(e.message);
        })
        .finally(() => {
          if (!cancelled) setLoading(false);
        });
    }
    return () => {
      cancelled = true;
    };
  }, [categoryId, parentId, productId, router, search]);

  useEffect(() => {
    if (categoryId) {
      setupBackButton(() => router.push("/catalog"));
      return () => hideBackButton();
    }
    hideBackButton();
  }, [categoryId, router]);

  if (error) {
    return (
      <div className="page">
        <p className="error-msg">{error}</p>
        <Link href="/catalog" className="btn btn--secondary mt-2">← Каталог</Link>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="page">
        <header className="page__header">
          <div>
            <h1 className="page__title">{categoryId ? "Товары" : "Каталог"}</h1>
            <p className="page__subtitle">
              {categoryId ? "Подбираем позиции…" : "Подгружаем категории…"}
            </p>
          </div>
        </header>
        {categoryId ? (
          <>
            <div className="catalogSearch">
              <input
                type="search"
                className="input input--flat"
                placeholder="Поиск по названию…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <CatalogSkeleton kind="products" />
          </>
        ) : (
          <CatalogSkeleton kind="categories" />
        )}
      </div>
    );
  }

  return (
    <div className="page">
      <header className="page__header">
        <div>
          <h1 className="page__title">{categoryId ? "Товары" : "Каталог"}</h1>
          <p className="page__subtitle">
            {categoryId ? "Выберите товар" : "Мёд и продукты пасеки"}
          </p>
        </div>
      </header>

      {categoryId && (
        <div className="catalogSearch">
          <input
            type="search"
            className="input input--flat"
            placeholder="Поиск по названию…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      )}

      {isCategoryList ? (
        <div className={`grid grid--categories mt-2`}>
          {categories.map((c) => (
            <Link
              key={c.id}
              href={`/catalog?category=${c.id}`}
              className="card card--clickable catalogCategoryCard"
            >
              <span className="catalogCategoryCard__iconWrap">
                <span className="catalogCategoryCard__icon" aria-hidden>🍯</span>
              </span>
              <div className="catalogCategoryCard__content">
                <strong className="catalogCategoryCard__name">{c.name}</strong>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <>
          {products.length === 0 ? (
            <div className="empty-state card mt-2">
              <div className="empty-state__icon">🔎</div>
              <p className="mb-0">Ничего не нашли</p>
              <p className="hint mt-1 mb-0">Попробуйте изменить запрос поиска.</p>
            </div>
          ) : (
            <ul className="grid grid--products mt-2 list-divider">
              {products.map((p) => (
                <li key={p.id}>
                  <Link href={`/catalog/product/${p.id}`} className="card card--clickable productCard">
                    <div className="productCard__media">
                      {p.image_url ? (
                        <img src={p.image_url} alt="" className="productCard__img" />
                      ) : (
                        <span className="productCard__placeholder" aria-hidden>🍯</span>
                      )}
                    </div>
                    <div className="productCard__body">
                      <strong className="productCard__name">{p.name}</strong>
                      <span className="productCard__price">{p.price} ₽</span>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  );
}

export default function CatalogPage() {
  return (
    <Suspense
      fallback={
        <div className="page">
          <header className="page__header">
            <div>
              <h1 className="page__title">Каталог</h1>
              <p className="page__subtitle">Подгружаем…</p>
            </div>
          </header>
          <CatalogSkeleton kind="categories" />
        </div>
      }
    >
      <CatalogPageContent />
    </Suspense>
  );
}
