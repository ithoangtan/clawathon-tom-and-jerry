import { t as translate, type I18nKey } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";

/** React hook for locale-aware UI strings (not AI responses). */
export function useI18n() {
  const locale = useUserStore((s) => s.locale);
  const setLocale = useUserStore((s) => s.setLocale);

  function t(key: I18nKey, vars?: Record<string, string | number>): string {
    return translate(key, locale, vars);
  }

  return { locale, setLocale, t };
}
