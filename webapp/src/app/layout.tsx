import type { Metadata } from "next";
import { ClientRootLayout } from "@/components/ClientRootLayout";
import "./globals.css";

export const metadata: Metadata = {
  title: "Пчёлка",
  description: "Магазин мёда и продуктов пасеки",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <head>
        {/* @font-face только здесь: статика public/fonts.css, не через бандлер Next */}
        <link rel="stylesheet" href="/fonts.css" />
        <link
          rel="icon"
          href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Ccircle fill='%23c9901a' cx='16' cy='16' r='14'/%3E%3C/svg%3E"
        />
        <script src="https://telegram.org/js/telegram-web-app.js" async />
      </head>
      <ClientRootLayout>{children}</ClientRootLayout>
    </html>
  );
}
