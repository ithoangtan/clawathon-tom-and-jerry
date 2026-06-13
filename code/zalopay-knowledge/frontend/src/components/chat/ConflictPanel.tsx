import { Card } from "@/components/ui/Card";
import { CitationList } from "@/components/chat/CitationList";
import { DepartmentChip } from "@/components/chat/Badges";
import { AlertTriangle } from "@/components/ui/icons";
import { getDepartment } from "@/lib/departments";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { Conflict } from "@/lib/types";

interface ConflictPanelProps {
  conflicts: Conflict[];
}

function ConflictIcon() {
  return <AlertTriangle size="lg" className="shrink-0 text-amber-700" />;
}

export function ConflictPanel({ conflicts }: ConflictPanelProps) {
  const locale = useUserStore((s) => s.locale);

  if (!conflicts.length) return null;

  return (
    <div
      className="mt-4 space-y-3"
      role="region"
      aria-label={t("conflictTitle", locale)}
    >
      <div className="flex gap-3 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3">
        <ConflictIcon />
        <div>
          <h4 className="font-semibold text-amber-900">{t("conflictTitle", locale)}</h4>
          <p className="mt-1 text-sm text-amber-800">{t("conflictHint", locale)}</p>
        </div>
      </div>

      {conflicts.map((conflict, i) => (
        <Card key={i} padding="sm" className="border-amber-200 bg-amber-50/30">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wide text-amber-800">
              {t("conflictItem", locale, { index: i + 1, total: conflicts.length })}
            </span>
            {conflict.topic && (
              <h5 className="font-medium text-slate-800">{conflict.topic}</h5>
            )}
          </div>
          <div className="space-y-4">
            {conflict.sides.map((side, j) => {
              const accent = getDepartment(side.department).accent_color;
              return (
                <div
                  key={j}
                  className="rounded-r-md border-l-4 bg-white/80 pl-3 pr-2 py-2"
                  style={{ borderColor: accent }}
                >
                  <DepartmentChip deptKey={side.department} />
                  <p className="mt-2 text-sm leading-relaxed text-slate-700">{side.statement}</p>
                  <CitationList citations={[side.citation]} collapsible={false} />
                </div>
              );
            })}
          </div>
        </Card>
      ))}
    </div>
  );
}
