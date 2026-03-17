"use client";

import { usePathname } from "next/navigation";
import { AppHeader } from "./AppHeader";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? "/";

  return (
    <div className="appShell">
      <AppHeader />
      <main key={pathname} className="appMain pageTransition" role="main">
        {children}
      </main>
    </div>
  );
}

