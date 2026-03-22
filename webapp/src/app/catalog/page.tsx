"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Package, Search } from "lucide-react";
import { hideBackButton, setupBackButton } from "@/lib/telegram";
import { useAsyncData } from "@/lib/useAsyncData";
import { getCategories, getProducts, type Category, type Product } from "@/lib/api";

const PRODUCTS_PAGE_SIZE = 24;

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

  const { data: categories, loading: catLoading, error: catError } = useAsyncData(
    () => getCategories(),
    [],
    { enabled: isCategoryList },
  );

  const parentId = categoryId ? parseInt(categoryId, 10) : NaN;
  const [products, setProducts] = useState<Product[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [prodLoading, setProdLoading] = useState(false);
  const [prodLoadingMore, setProdLoadingMore] = useState(false);
  const [prodError, setProdError] = useState<string | null>(null);
  const fetchGenRef = useRef(0);
  const loadingMoreGuard = useRef(false);
  const nextOffsetRef = useRef(0);

  useEffect(() => {
    nextOffsetRef.current = products.length;
  }, [products.length]);

  useEffect(() => {
    if (!categoryId || productId || Number.isNaN(parentId)) {
      return;
    }
    const gen = ++fetchGenRef.current;
    let cancelled = false;
    setProdLoading(true);
    setProdError(null);
    setProducts([]);
    setTotalCount(0);
    nextOffsetRef.current = 0;
    getProducts(parentId, search || undefined, { limit: PRODUCTS_PAGE_SIZE, offset: 0 })
      .then((r) => {
        if (cancelled || gen !== fetchGenRef.current) return;
        setProducts(r.results);
        setTotalCount(r.count);
      })
      .catch((e) => {
        if (cancelled || gen !== fetchGenRef.current) return;
        setProdError(e instanceof Error ? e.message : String(e));
      })
      .finally(() => {
        if (cancelled || gen !== fetchGenRef.current) return;
        setProdLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [categoryId, search, productId, parentId]);

  const loadMore = useCallback(async () => {
    if (!categoryId || productId || Number.isNaN(parentId)) return;
    if (prodLoading || loadingMoreGuard.current) return;
    const offset = nextOffsetRef.current;
    if (offset >= totalCount) return;
    const genAtStart = fetchGenRef.current;
    loadingMoreGuard.current = true;
    setProdLoadingMore(true);
    try {
      const { results, count } = await getProducts(parentId, search || undefined, {
        limit: PRODUCTS_PAGE_SIZE,
        offset,
      });
      if (genAtStart !== fetchGenRef.current) return;
      setProducts((prev) => [...prev, ...results]);
      setTotalCount(count);
    } catch (e) {
      if (genAtStart !== fetchGenRef.current) return;
      setProdError(e instanceof Error ? e.message : String(e));
    } finally {
      loadingMoreGuard.current = false;
      setProdLoadingMore(false);
    }
  }, [categoryId, productId, parentId, search, totalCount, prodLoading]);

  const hasMore = products.length < totalCount;
  const sentinelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!categoryId || productId || !hasMore) return;
    const node = sentinelRef.current;
    if (!node) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) void loadMore();
      },
      { root: null, rootMargin: "320px", threshold: 0 },
    );
    obs.observe(node);
    return () => obs.disconnect();
  }, [categoryId, productId, hasMore, loadMore]);

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

  const error = isCategoryList ? catError : prodError;
  if (error) {
    return (
      <div className="page">
        <p className="error-msg">{error}</p>
        <Link href="/catalog" className="btn btn--secondary mt-2">
          ← Каталог
        </Link>
      </div>
    );
  }

  const loading = isCategoryList ? catLoading : prodLoading && products.length === 0;

  if (loading || (isCategoryList && !categories)) {
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

  const categoryRows = categories ?? [];

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
          {categoryRows.map((c) => (
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
            <>
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
              {hasMore && <div ref={sentinelRef} className="catalogLoadSentinel" aria-hidden />}
              {prodLoadingMore && (
                <p className="hint mt-2 mb-0 text-center">Загружаем ещё…</p>
              )}
            </>
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
