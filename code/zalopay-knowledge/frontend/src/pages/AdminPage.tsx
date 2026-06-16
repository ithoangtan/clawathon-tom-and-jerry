import { ScrollablePage } from "@/components/layout/ScrollablePage";
import { AdminDashboardCards } from "@/components/admin/AdminDashboardCards";
import { AdminSyncTable } from "@/components/admin/AdminSyncTable";
import { AdminSyncTimeline } from "@/components/admin/AdminSyncTimeline";
import { RecentJobsSection } from "@/components/admin/AdminSyncStatusPanel";
import { KnowledgeGapPanel } from "@/components/admin/KnowledgeGapPanel";
import { AdminTestEmailPanel } from "@/components/admin/AdminTestEmailPanel";
// import { AdminReindexCard } from "@/components/admin/AdminReindexCard";
import { Database } from "@/components/ui/icons";
import { t } from "@/lib/i18n";
import { usePageTutorial } from "@/hooks/useTutorial";
import { useUserStore } from "@/store/userStore";
import { useAdminSyncStatus } from "@/hooks/useAdminSyncStatus";

export function AdminPage() {
  const locale = useUserStore((s) => s.locale);
  const { status } = useAdminSyncStatus();
  usePageTutorial("admin");

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
        <div data-tour="admin-cards">
          <AdminDashboardCards status={status} />
        </div>

        {/* Unified sources table */}
        <div data-tour="admin-sources">
          <AdminSyncTable />
        </div>

        {/* Timeline chart */}
        <AdminSyncTimeline />

        {/* Recent jobs */}
        <div data-tour="admin-jobs">
          <RecentJobsSection />
        </div>

        {/* Force re-index (after embedding model change) */}
        {/* <AdminReindexCard /> */}

        {/* Knowledge gap tracker */}
        <section aria-labelledby="knowledge-gaps-heading">
          <h3 id="knowledge-gaps-heading" className="sr-only">{t("knowledgeGapsTitle", locale)}</h3>
          <KnowledgeGapPanel />
        </section>

        {/* Test email */}
        <section aria-labelledby="test-email-heading">
          <h3 id="test-email-heading" className="mb-3 text-sm font-semibold text-content-secondary uppercase tracking-wide">
            Kiểm tra kết nối Email
          </h3>
          <AdminTestEmailPanel />
        </section>
      </div>
    </ScrollablePage>
  );
}
