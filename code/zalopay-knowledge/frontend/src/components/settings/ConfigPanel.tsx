import { Card } from "@/components/ui/Card";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { HealthInfo } from "@/lib/types";

interface ConfigPanelProps {
  health: HealthInfo | null;
}

export function ConfigPanel({ health }: ConfigPanelProps) {
  const locale = useUserStore((s) => s.locale);
  const config = health?.config;

  if (!config || Object.keys(config).length === 0) {
    return (
      <Card>
        <h3 className="font-semibold text-slate-800 mb-2">{t("configPanel", locale)}</h3>
        <p className="text-sm text-slate-500">No config snapshot available.</p>
      </Card>
    );
  }

  return (
    <Card>
      <h3 className="font-semibold text-slate-800 mb-4">{t("configPanel", locale)}</h3>
      <dl className="grid gap-3 sm:grid-cols-2 text-sm">
        {Object.entries(config).map(([key, value]) => (
          <div key={key} className="border-b border-slate-100 pb-2">
            <dt className="text-slate-500 font-mono text-xs">{key}</dt>
            <dd className="font-medium text-slate-800 mt-0.5">
              {typeof value === "object" ? JSON.stringify(value) : String(value)}
            </dd>
          </div>
        ))}
      </dl>
      {health?.version && (
        <p className="mt-4 text-xs text-slate-500">Version {health.version}</p>
      )}
    </Card>
  );
}
