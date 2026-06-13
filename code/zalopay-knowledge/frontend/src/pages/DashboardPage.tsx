import { Activity, AlertTriangle, RotateCw } from "@/components/ui/icons";
import { HistoryTable, MetricsGrid } from "@/components/dashboard/DashboardPanels";
import { ScrollablePage } from "@/components/layout/ScrollablePage";
import { Card } from "@/components/ui/Card";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { t } from "@/lib/i18n";
import { useDashboard } from "@/hooks/useDashboard";
import { useUserStore } from "@/store/userStore";
import { MOCK_DASHBOARD } from "@/lib/mockDashboard";

export function DashboardPage() {
  const locale = useUserStore((s) => s.locale);
  const { data, error, loading, refresh } = useDashboard();

  const displayData = data ?? (error ? MOCK_DASHBOARD : null);

  return (
    <ScrollablePage>
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

      {error && (
        <div
          role="alert"
          className="flex items-center gap-3 rounded-lg border border-danger/30 bg-danger-muted px-4 py-3 text-sm text-danger"
        >
          <AlertTriangle size="sm" className="flex-shrink-0" />
          <span className="flex-1">{error}</span>
          <button
            type="button"
            onClick={refresh}
            className="inline-flex items-center gap-1.5 rounded-md border border-danger/30 px-3 py-1 text-xs font-medium transition-colors hover:bg-danger/10"
          >
            <RotateCw size="xs" />
            {t("retry", locale) ?? "Thử lại"}
          </button>
        </div>
      )}

      {loading && !displayData ? (
        <div className="surface-card p-12">
          <LoadingSpinner />
        </div>
      ) : displayData ? (
        <MetricsGrid data={displayData} />
      ) : null}

      {displayData && (
        <section aria-labelledby="history-heading">
          <Card>
            <h3 id="history-heading" className="section-title mb-0">
              {t("queryHistory", locale)}
            </h3>
            <div className="mt-4">
              <HistoryTable history={displayData.history} />
            </div>
          </Card>
        </section>
      )}
    </div>
    </ScrollablePage>
  );
}
