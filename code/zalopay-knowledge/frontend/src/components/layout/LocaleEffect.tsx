import { useUserStore } from "@/store/userStore";
import { useEffect } from "react";

/** Keeps document language in sync with the persisted UI locale. */
export function LocaleEffect() {
  const locale = useUserStore((s) => s.locale);

  useEffect(() => {
    document.documentElement.lang = locale === "vi" ? "vi" : "en";
  }, [locale]);

  return null;
}
