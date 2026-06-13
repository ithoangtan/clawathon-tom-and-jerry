import { useUserStore } from "@/store/userStore";
import { useEffect } from "react";

/** Keeps data-theme attribute on <html> in sync with the persisted theme. */
export function ThemeEffect() {
  const theme = useUserStore((s) => s.theme);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  return null;
}
