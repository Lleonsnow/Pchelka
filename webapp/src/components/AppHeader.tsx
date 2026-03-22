"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { LucideIcon } from "lucide-react";
import { Hexagon, Home, LayoutGrid, ShoppingCart, User } from "lucide-react";

type HeaderLink = {
  href: string;
  label: string;
  Icon: LucideIcon;
  exact?: boolean;
};

const BASE_LINKS: HeaderLink[] = [
  { href: "/", label: "Главная", Icon: Home, exact: true },
  { href: "/catalog", label: "Каталог", Icon: LayoutGrid },
  { href: "/cart", label: "Корзина", Icon: ShoppingCart },
  { href: "/profile", label: "Профиль", Icon: User },
];

function isActiveLink(pathname: string, link: HeaderLink): boolean {
  if (link.exact) return pathname === link.href;
  return pathname === link.href || pathname.startsWith(`${link.href}/`);
}

export function AppHeader() {
  const pathname = usePathname() ?? "/";

  return (
    <header className="appHeader">
      <div className="appHeader__top">
        <Link href="/" className="appHeader__brand" aria-label="Пчёлка — на главную">
          <span className="appHeader__brandMark" aria-hidden>
            <Hexagon className="appHeader__brandMarkSvg" strokeWidth={2.4} aria-hidden />
          </span>
          <span className="appHeader__brandText">Пчёлка</span>
        </Link>
      </div>
      <div className="appHeader__inner">
        <nav className="appHeader__nav" aria-label="Навигация">
          {BASE_LINKS.map((l) => {
            const active = isActiveLink(pathname, l);
            const { Icon } = l;
            return (
              <Link
                key={l.href}
                href={l.href}
                className={active ? "appHeader__pill appHeader__pill--active" : "appHeader__pill"}
                aria-current={active ? "page" : undefined}
              >
                <span className="appHeader__pillIcon" aria-hidden>
                  <Icon size={18} strokeWidth={2.25} />
                </span>
                <span className="appHeader__pillLabel">{l.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
