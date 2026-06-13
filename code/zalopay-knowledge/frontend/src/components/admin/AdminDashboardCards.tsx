import { Card } from "@/components/ui/Card";
import { FileText, Database, Activity, History } from "@/components/ui/icons";
import { formatFreshnessHours } from "@/lib/format";
import { t } from "@/lib/i18n";
import type { AdminSyncStatus } from "@/lib/types";
import { useUserStore } from "@/store/userStore";

interface StatCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub?: string;
  accent?: string;
}

function StatCard({ icon, label, value, sub, accent = "bg-brand-muted text-brand" }: StatCardProps) {
  return (
    <Card className="flex items-center gap-4 py-4">
      <div className={`flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl ${accent}`}>
        {icon}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium uppercase tracking-wide text-content-secondary">{label}</p>
        <p className="mt-0.5 text-2xl font-bold text-content-primary tabular-nums">{value}</p>
        {sub && <p className="mt-0.5 text-xs text-content-muted">{sub}</p>}
      </div>
    </Card>
  );
}

interface Props {
  status: AdminSyncStatus | null;
}

export function AdminDashboardCards({ status }: Props) {
  const locale = useUserStore((s) => s.locale);

  const depts = status?.departments ?? [];
  const gdrive = status?.sources.find((s) => s.source === "gdrive");

  const totalDocs =
    depts.reduce((a, d) => a + (d.doc_count ?? 0), 0) + (gdrive?.doc_count ?? 0);

  const totalChunks =
    depts.reduce((a, d) => a + (d.chunk_count ?? 0), 0) + (gdrive?.chunk_count ?? 0);

  const syncedCount =
    depts.filter((d) => d.last_success_at).length + (gdrive?.last_success_at ? 1 : 0);
  const totalSources = depts.length + (gdrive ? 1 : 0);

  const allLastSync = [
    ...depts.map((d) => d.last_success_at),
    gdrive?.last_success_at,
  ]
    .filter(Boolean)
    .sort()
    .reverse() as string[];

  const lastSync = allLastSync[0] ?? null;
  const minFreshness = [...depts, ...(gdrive ? [gdrive] : [])].reduce(
    (min, s) => {
      const h = "freshness_hours" in s ? s.freshness_hours : null;
      if (h == null) return min;
      return min == null ? h : Math.min(min, h);
    },
    null as number | null,
  );

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <StatCard
        icon={<FileText size="md" />}
        label={t("adminTotalDocs", locale)}
        value={totalDocs.toLocaleString()}
        sub={`${totalChunks.toLocaleString()} ${t("chunks", locale)}`}
        accent="bg-brand-muted text-brand"
      />
      <StatCard
        icon={<Database size="md" />}
        label={t("adminTotalChunks", locale)}
        value={totalChunks.toLocaleString()}
        accent="bg-accent/10 text-accent"
      />
      <StatCard
        icon={<Activity size="md" />}
        label={t("adminSourcesSynced", locale)}
        value={`${syncedCount} / ${totalSources}`}
        sub={
          status?.running
            ? t("syncing", locale)
            : undefined
        }
        accent="bg-emerald-500/10 text-emerald-500"
      />
      <StatCard
        icon={<History size="md" />}
        label={t("adminLastUpdate", locale)}
        value={minFreshness != null ? formatFreshnessHours(minFreshness, locale) : "—"}
        sub={lastSync ? undefined : t("adminNeverSynced", locale)}
        accent="bg-surface-glass text-content-secondary"
      />
    </div>
  );
}
