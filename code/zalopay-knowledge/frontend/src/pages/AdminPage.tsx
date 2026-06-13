import { ScrollablePage } from "@/components/layout/ScrollablePage";
import { AdminDashboardCards } from "@/components/admin/AdminDashboardCards";
import { AdminSyncTable } from "@/components/admin/AdminSyncTable";
import { AdminSyncTimeline } from "@/components/admin/AdminSyncTimeline";
import { RecentJobsSection } from "@/components/admin/AdminSyncStatusPanel";
import { Database } from "@/components/ui/icons";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import { useAdminSyncStatus } from "@/hooks/useAdminSyncStatus";

export function AdminPage() {
  const locale = useUserStore((s) => s.locale);
  const { status } = useAdminSyncStatus();

  return (
    <ScrollablePage>
      <div className="page-shell space-y-6 sm:space-y-8">
        <header className="page-header">
          <div className="flex items-start gap-4">
            <div
              className="hidden h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl bg-brand-muted text-brand sm:flex"
              aria-hidden
            >
              <Database size="lg" />
            </div>
            <div
              className="hidden h-12 w-1 flex-shrink-0 rounded-full bg-gradient-to-b from-brand to-accent sm:block"
              aria-hidden
            />
            <div>
              <h2 className="page-title">{t("adminTitle", locale)}</h2>
              <p className="page-subtitle">{t("adminSubtitle", locale)}</p>
            </div>
          </div>
        </header>

        {/* Dashboard summary cards */}
        <AdminDashboardCards status={status} />

        {/* Unified sources table */}
        <AdminSyncTable />

        {/* Timeline chart */}
        <AdminSyncTimeline />

        {/* Recent jobs */}
        <RecentJobsSection />
      </div>
    </ScrollablePage>
  );
}
