"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Package, Search } from "lucide-react";
import { hideBackButton, setupBackButton } from "@/lib/telegram";
import { useAsyncData } from "@/lib/useAsyncData";
import { getCategories, getProducts, type Category, type Product } from "@/lib/api";

type CatalogData =
  | { mode: "categories"; list: Category[] }
  | { mode: "products"; list: Product[] };

async function fetchCatalog(categoryId: string | null, search: string): Promise<CatalogData> {
  if (categoryId) {
    const parentId = parseInt(categoryId, 10);
    if (Number.isNaN(parentId)) {
      throw new Error("Неверная категория");
    }
    const list = await getProducts(parentId, search || undefined);
    return { mode: "products", list };
  }
  const list = await getCategories();
  return { mode: "categories", list };
}

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
  const [search, setSearch] = useState("");
  const isCategoryList = !categoryId && !productId;

  const { data, loading, error } = useAsyncData(
    () => fetchCatalog(categoryId, search),
    [categoryId, search],
    { enabled: !productId },
  );

  useEffect(() => {
    if (productId) {
      router.push(`/catalog/product/${productId}`);
    }
  }, [productId, router]);

  useEffect(() => {
    if (categoryId) {
      setupBackButton(() => router.push("/catalog"));
      return () => hideBackButton();
    }
    hideBackButton();
  }, [categoryId, router]);

  if (productId) {
    return (
      <div className="page">
        <header className="page__header">
          <div>
            <h1 className="page__title">Каталог</h1>
            <p className="page__subtitle">Переход к товару…</p>
          </div>
        </header>
        <div className="loading">Загрузка…</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <p className="error-msg">{error}</p>
        <Link href="/catalog" className="btn btn--secondary mt-2">← Каталог</Link>
      </div>
    );
  }

  if (loading || !data) {
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

  const categories = data.mode === "categories" ? data.list : [];
  const products = data.mode === "products" ? data.list : [];

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
                <span className="catalogCategoryCard__icon" aria-hidden>
                  <Package strokeWidth={2} />
                </span>
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
              <div className="empty-state__icon" aria-hidden>
                <Search strokeWidth={1.75} />
              </div>
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
                        <span className="productCard__placeholder" aria-hidden>
                          <Package strokeWidth={1.75} />
                        </span>
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
