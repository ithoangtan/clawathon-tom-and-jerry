import { Activity } from "@/components/ui/icons";
import { HistoryTable, MetricsGrid } from "@/components/dashboard/DashboardPanels";
import { SyncStatusPanel } from "@/components/dashboard/SyncStatusPanel";
import { Card } from "@/components/ui/Card";
import { ErrorState } from "@/components/ui/StateViews";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { t } from "@/lib/i18n";
import { useDashboard } from "@/hooks/useDashboard";
import { useUserStore } from "@/store/userStore";

export function DashboardPage() {
  const locale = useUserStore((s) => s.locale);
  const { data, error, loading, refresh } = useDashboard();

  return (
    <div className="page-shell space-y-8 sm:space-y-10" data-tour="dashboard-overview">
      <header className="page-header">
        <div className="flex items-start gap-4">
          <div
            className="hidden h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-brand-muted text-brand sm:flex"
            aria-hidden
          >
            <Activity size="lg" />
          </div>
          <div
            className="hidden h-12 w-1 flex-shrink-0 rounded-full bg-gradient-to-b from-brand to-accent sm:block"
            aria-hidden
          />
          <div>
            <h2 className="page-title">{t("dashboardTitle", locale)}</h2>
            <p className="page-subtitle">{t("dashboardSubtitle", locale)}</p>
          </div>
        </div>
      </header>

      {loading && !data ? (
        <div className="surface-card p-12">
          <LoadingSpinner />
        </div>
      ) : error ? (
        <ErrorState message={error} onRetry={refresh} />
      ) : data ? (
        <MetricsGrid data={data} />
      ) : null}

      <section aria-labelledby="sync-heading" className="space-y-4">
        <h3 id="sync-heading" className="section-title">
          {t("syncStatus", locale)}
        </h3>
        <SyncStatusPanel />
      </section>

      {data && (
        <section aria-labelledby="history-heading">
          <Card>
            <h3 id="history-heading" className="section-title mb-0">
              {t("queryHistory", locale)}
            </h3>
            <div className="mt-4">
              <HistoryTable history={data.history} />
            </div>
          </Card>
        </section>
      )}
    </div>
  );
}
