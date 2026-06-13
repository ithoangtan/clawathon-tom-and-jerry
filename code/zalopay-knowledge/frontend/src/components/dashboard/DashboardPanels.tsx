import { Card } from "@/components/ui/Card";
import { DepartmentChip } from "@/components/chat/Badges";
import { ConfidenceBadge } from "@/components/chat/Badges";
import { formatDate, formatMs, formatPercent } from "@/lib/format";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { DashboardData } from "@/lib/types";

interface MetricsGridProps {
  data: DashboardData;
}

export function MetricsGrid({ data }: MetricsGridProps) {
  const locale = useUserStore((s) => s.locale);

  const metrics = [
    { label: t("totalQueries", locale), value: data.query_count.toLocaleString() },
    { label: t("refusalRate", locale), value: formatPercent(data.refusal_rate) },
    { label: t("latencyP50", locale), value: formatMs(data.latency_p50_ms) },
    { label: t("latencyP95", locale), value: formatMs(data.latency_p95_ms) },
    { label: t("feedbackUp", locale), value: data.feedback_up.toLocaleString() },
    { label: t("feedbackDown", locale), value: data.feedback_down.toLocaleString() },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {metrics.map((m) => (
        <Card key={m.label} padding="sm">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            {m.label}
          </p>
          <p className="mt-1 text-2xl font-bold text-slate-900">{m.value}</p>
        </Card>
      ))}
    </div>
  );
}

interface HistoryTableProps {
  history: DashboardData["history"];
}

export function HistoryTable({ history }: HistoryTableProps) {
  const locale = useUserStore((s) => s.locale);

  if (history.length === 0) {
    return (
      <p className="text-sm text-slate-500 py-8 text-center" role="status">
        {t("noHistory", locale)}
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm text-left">
        <thead>
          <tr className="border-b border-slate-200 text-slate-500">
            <th className="py-2 pr-4 font-medium" scope="col">
              Time
            </th>
            <th className="py-2 pr-4 font-medium" scope="col">
              Question
            </th>
            <th className="py-2 pr-4 font-medium" scope="col">
              Departments
            </th>
            <th className="py-2 pr-4 font-medium" scope="col">
              Status
            </th>
            <th className="py-2 font-medium" scope="col">
              Latency
            </th>
          </tr>
        </thead>
        <tbody>
          {history.map((item, i) => (
            <tr key={`${item.ts}-${i}`} className="border-b border-slate-100">
              <td className="py-3 pr-4 whitespace-nowrap text-slate-500">
                {formatDate(item.ts, locale)}
              </td>
              <td className="py-3 pr-4 max-w-xs truncate" title={item.question}>
                {item.question}
              </td>
              <td className="py-3 pr-4">
                <div className="flex flex-wrap gap-1">
                  {item.departments.map((d) => (
                    <DepartmentChip key={d} deptKey={d} />
                  ))}
                </div>
              </td>
              <td className="py-3 pr-4">
                <ConfidenceBadge confidence={item.confidence} status={item.status} />
              </td>
              <td className="py-3 text-slate-500">{formatMs(item.latency_ms)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
