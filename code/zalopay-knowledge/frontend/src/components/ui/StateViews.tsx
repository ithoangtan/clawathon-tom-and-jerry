import { Button } from "@/components/ui/Button";
import { AlertCircle, MessageSquare, RotateCw } from "@/components/ui/icons";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description?: string;
  icon?: ReactNode;
}

export function EmptyState({ title, description, icon }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center" role="status">
      <span className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-muted text-brand">
        {icon ?? <MessageSquare size="xl" />}
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
      <div className="flex gap-3">
        <AlertCircle size="lg" className="mt-0.5 shrink-0" />
        <div className="min-w-0 flex-1">
          <p>{message}</p>
          {onRetry && (
            <Button variant="secondary" className="mt-3" onClick={onRetry}>
              <RotateCw size="sm" />
              {t("retry", locale)}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
