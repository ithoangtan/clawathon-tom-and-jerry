import { ScrollablePage } from "@/components/layout/ScrollablePage";
import { AdminSyncControls } from "@/components/admin/AdminSyncControls";
import { AdminSyncStatusPanel } from "@/components/admin/AdminSyncStatusPanel";
import { Database } from "@/components/ui/icons";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";

export function AdminPage() {
  const locale = useUserStore((s) => s.locale);

  return (
    <ScrollablePage>
    <div className="page-shell space-y-8 sm:space-y-10">
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

      <AdminSyncControls />
      <AdminSyncStatusPanel />
    </div>
    </ScrollablePage>
  );
}
