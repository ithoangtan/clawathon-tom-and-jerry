import { ScrollablePage } from "@/components/layout/ScrollablePage";
import { ConfigPanel } from "@/components/settings/ConfigPanel";
import { UserIdentityForm } from "@/components/settings/UserIdentityForm";
import { t } from "@/lib/i18n";
import { useHealth } from "@/hooks/useHealth";
import { usePageTutorial } from "@/hooks/useTutorial";
import { useUserStore } from "@/store/userStore";

export function SettingsPage() {
  const locale = useUserStore((s) => s.locale);
  const { health } = useHealth();
  usePageTutorial("settings");

  return (
    <ScrollablePage>
    <div className="page-shell mx-auto max-w-3xl space-y-8">
      <header className="page-header">
        <h2 className="page-title">{t("settingsTitle", locale)}</h2>
        <p className="page-subtitle">{t("settingsSubtitle", locale)}</p>
      </header>

      <div className="space-y-6">
        <div data-tour="settings-identity">
          <UserIdentityForm />
        </div>
        <div data-tour="settings-sync">
          <ConfigPanel health={health} />
        </div>
      </div>
    </div>
    </ScrollablePage>
  );
}
