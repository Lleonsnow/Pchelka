"use client";

import { useEffect } from "react";
import { notifyReady, getThemeParams } from "@/lib/telegram";
import { AppShell } from "@/components/AppShell";

export function ClientRootLayout({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    notifyReady();
  }, []);

  const theme = getThemeParams();
  const bg = theme.bg_color ?? "#fff";
  const text = theme.text_color ?? "#000";
  const hint = theme.hint_color ?? "#999";
  const linkColor = theme.link_color ?? "#2481cc";

  return (
    <body
      suppressHydrationWarning
      className="theme-pchelka"
      style={{
        backgroundColor: bg,
        color: text,
        ["--link-color" as string]: linkColor,
        ["--hint-color" as string]: hint,
      }}
    >
      <AppShell>{children}</AppShell>
    </body>
  );
}
