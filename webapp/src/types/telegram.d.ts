export declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        version?: string;
        initData: string;
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
      };
    };
  }
}
