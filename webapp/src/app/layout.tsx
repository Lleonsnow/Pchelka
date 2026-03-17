"use client";

import { useEffect } from "react";
import { notifyReady, getThemeParams } from "@/lib/telegram";
import { AppShell } from "@/components/AppShell";
import "./globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  useEffect(() => {
    notifyReady();
  }, []);

  const theme = getThemeParams();
  const bg = theme.bg_color ?? "#fff";
  const text = theme.text_color ?? "#000";
  const hint = theme.hint_color ?? "#999";
  const linkColor = theme.link_color ?? "#2481cc";

  return (
    <html lang="ru" suppressHydrationWarning>
      <head>
        <link
          rel="icon"
          href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle fill='%23c9901a' cx='16' cy='16' r='14'/%3E%3C/svg%3E"
        />
        <script src="https://telegram.org/js/telegram-web-app.js" async />
      </head>
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
    </html>
  );
}
