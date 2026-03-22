"use client";

import { useCallback, useEffect, useState, type Dispatch, type SetStateAction } from "react";

export type UseAsyncDataOptions = {
  /** Если false — запрос не выполняется, loading будет false. */
  enabled?: boolean;
};

export type UseAsyncDataResult<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
  setData: Dispatch<SetStateAction<T | null>>;
  setError: Dispatch<SetStateAction<string | null>>;
};

/**
 * Асинхронная загрузка при монтировании и при изменении deps; отмена при размонтировании / смене deps.
 * fetcher должен замыкать актуальные значения из deps (или стабилизироваться через useCallback).
 */
export function useAsyncData<T>(
  fetcher: () => Promise<T>,
  deps: unknown[],
  options?: UseAsyncDataOptions,
): UseAsyncDataResult<T> {
  const enabled = options?.enabled ?? true;
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(() => Boolean(enabled));
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => {
    setReloadToken((n) => n + 1);
  }, []);

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      setError(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetcher()
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // fetcher намеренно не в deps — вызывающий синхронизирует замыкание через deps
    // eslint-disable-next-line react-hooks/exhaustive-deps -- см. аргумент deps
  }, [enabled, reloadToken, ...deps]);

  return { data, setData, loading, error, reload, setError };
}
