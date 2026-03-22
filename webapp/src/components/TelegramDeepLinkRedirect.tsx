"use client";

import { useEffect, useRef } from "react";
import { usePathname, useRouter } from "next/navigation";
import { getWebAppStartParam } from "@/lib/telegram";

/**
 * t.me/bot/&lt;app&gt;?startapp=product_&lt;id&gt; и часть сценариев «Открыть в браузере» передают start_param —
 * перенаправляем на страницу товара (меню бота обычно указывает только корень сайта).
 */
export function TelegramDeepLinkRedirect() {
  const router = useRouter();
  const pathname = usePathname() ?? "/";
  const doneRef = useRef(false);

  useEffect(() => {
    if (doneRef.current) return;
    const sp = getWebAppStartParam();
    if (!sp) return;
    const m = /^product_(\d+)$/.exec(sp.trim());
    if (!m) return;
    const id = m[1];
    const target = `/catalog/product/${id}`;
    if (pathname === target || pathname.startsWith(`${target}/`)) {
      doneRef.current = true;
      return;
    }
    doneRef.current = true;
    router.replace(target);
  }, [pathname, router]);

  return null;
}
