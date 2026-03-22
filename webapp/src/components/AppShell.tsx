"use client";

import { AppHeader } from "./AppHeader";
import { TelegramDeepLinkRedirect } from "./TelegramDeepLinkRedirect";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="appShell">
      <TelegramDeepLinkRedirect />
      <AppHeader />
      <main className="appMain" role="main">
        {children}
      </main>
    </div>
  );
}

