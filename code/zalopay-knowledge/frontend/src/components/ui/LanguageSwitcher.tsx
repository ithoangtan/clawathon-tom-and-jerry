import { classNames } from "@/lib/format";
import { useI18n } from "@/hooks/useI18n";
import type { Lang } from "@/lib/types";

const OPTIONS: { value: Lang; short: string; labelKey: "switchToEnglish" | "switchToVietnamese" }[] = [
  { value: "en", short: "EN", labelKey: "switchToEnglish" },
  { value: "vi", short: "VI", labelKey: "switchToVietnamese" },
];

export function LanguageSwitcher({ className }: { className?: string }) {
  const { locale, setLocale, t } = useI18n();

  return (
    <div
      role="group"
      aria-label={t("locale")}
      className={classNames(
        "inline-flex items-center rounded-lg border border-border bg-surface-glass p-0.5",
        className,
      )}
    >
      {OPTIONS.map((option) => {
        const active = locale === option.value;
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={active}
            aria-label={t(option.labelKey)}
            onClick={() => setLocale(option.value)}
            className={classNames(
              "min-w-[2.25rem] rounded-md px-2 py-1 text-xs font-semibold tracking-wide transition-all duration-fast ease-expo",
              active
                ? "bg-brand text-white shadow-sm"
                : "text-content-secondary hover:bg-brand-light hover:text-content-primary",
            )}
          >
            {option.short}
          </button>
        );
      })}
    </div>
  );
}
