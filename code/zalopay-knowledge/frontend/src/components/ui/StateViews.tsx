import { Button } from "@/components/ui/Button";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: string;
}

export function EmptyState({ title, description, icon = "💬" }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center" role="status">
      <span className="mb-4 text-4xl" aria-hidden>
        {icon}
      </span>
      <h3 className="text-lg font-semibold text-content-primary">{title}</h3>
      {description && (
        <p className="mt-2 max-w-md text-sm text-content-secondary">{description}</p>
      )}
    </div>
  );
}

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  const locale = useUserStore((s) => s.locale);
  return (
    <div
      className="rounded-xl border border-danger/30 bg-danger-muted p-4 text-sm text-danger"
      role="alert"
    >
      <p>{message}</p>
      {onRetry && (
        <Button variant="secondary" className="mt-3" onClick={onRetry}>
          {t("retry", locale)}
        </Button>
      )}
    </div>
  );
}
