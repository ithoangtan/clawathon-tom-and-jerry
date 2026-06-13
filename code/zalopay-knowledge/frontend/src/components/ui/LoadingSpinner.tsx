import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";

interface LoadingSpinnerProps {
  label?: string;
}

export function LoadingSpinner({ label }: LoadingSpinnerProps) {
  const locale = useUserStore((s) => s.locale);
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-8" role="status">
      <div
        className="h-8 w-8 animate-spin rounded-full border-2 border-brand border-t-transparent shadow-glow"
        aria-hidden
      />
      <span className="text-sm text-content-secondary">{label ?? t("loading", locale)}</span>
    </div>
  );
}
