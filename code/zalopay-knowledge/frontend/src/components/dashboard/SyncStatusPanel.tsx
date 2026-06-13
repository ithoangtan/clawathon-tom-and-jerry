import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { FreshnessBadge } from "@/components/ui/FreshnessBadge";
import { ErrorState } from "@/components/ui/StateViews";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { formatDate, formatFreshnessHours } from "@/lib/format";
import { t } from "@/lib/i18n";
import { useSyncStatus } from "@/hooks/useSyncStatus";
import { useUserStore } from "@/store/userStore";
import type { SourceStatus } from "@/lib/types";

export function SyncStatusPanel() {
  const locale = useUserStore((s) => s.locale);
  const { status, error, loading, refresh } = useSyncStatus();

  if (loading && !status) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={refresh} />;
  }

  if (!status?.sources.length) {
    return (
      <p className="text-sm text-slate-500" role="status">
        {t("neverSynced", locale)}
      </p>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2" role="list">
      {status.sources.map((source) => (
        <SourceCard key={source.source} source={source} />
      ))}
    </div>
  );
}

function SourceCard({ source }: { source: SourceStatus }) {
  const locale = useUserStore((s) => s.locale);

  const stateTone =
    source.state === "running"
      ? "info"
      : source.state === "error"
        ? "danger"
        : "default";

  const label =
    source.source === "confluence"
      ? "Confluence"
      : source.source === "gdrive"
        ? "Google Drive"
        : source.source;

  return (
    <Card role="listitem">
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-semibold text-slate-800">{label}</h3>
        <div className="flex gap-2">
          <Badge tone={stateTone}>{source.state}</Badge>
          <FreshnessBadge
            lastSuccessAt={source.last_success_at}
            freshnessHours={source.freshness_hours}
          />
        </div>
      </div>

      <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
        <div>
          <dt className="text-slate-500">{t("docs", locale)}</dt>
          <dd className="font-medium">{source.doc_count.toLocaleString()}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t("chunks", locale)}</dt>
          <dd className="font-medium">{source.chunk_count.toLocaleString()}</dd>
        </div>
      </dl>

      {source.last_success_at && (
        <p className="mt-2 text-xs text-slate-500">
          Last sync: {formatDate(source.last_success_at, locale)}
          {source.freshness_hours != null && (
            <span> · {formatFreshnessHours(source.freshness_hours)}</span>
          )}
        </p>
      )}

      {source.progress && (
        <p className="mt-2 text-xs text-brand">
          {Object.entries(source.progress)
            .map(([k, v]) => `${k.replace(/_/g, " ")}: ${String(v)}`)
            .join(" · ")}
        </p>
      )}

      {source.errors.length > 0 && (
        <ul className="mt-2 text-xs text-red-600" role="alert">
          {source.errors.map((err, i) => (
            <li key={i}>{err}</li>
          ))}
        </ul>
      )}
    </Card>
  );
}
