export declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        version?: string;
        initData: string;
        /** Параметр startapp при открытии по прямой ссылке t.me/bot/app?startapp=... */
        initDataUnsafe?: {
          start_param?: string;
          user?: Record<string, unknown>;
        };
        themeParams: {
          bg_color?: string;
          text_color?: string;
          hint_color?: string;
          link_color?: string;
          button_color?: string;
          button_text_color?: string;
          secondary_bg_color?: string;
        };
        BackButton: { show: () => void; hide: () => void; onClick: (cb: () => void) => void };
        MainButton: {
          show: () => void;
          hide: () => void;
          setText: (text: string) => void;
          onClick: (cb: () => void) => void;
        };
        ready: () => void;
        /** Открывает ссылку вида https://t.me/... внутри Telegram (шаринг, боты и т.д.). */
        openTelegramLink?: (url: string) => void;
        /** Внешняя ссылка в браузере / in-app browser. */
        openLink?: (url: string, options?: { try_instant_view?: boolean }) => void;
      };
    };
  }
}
