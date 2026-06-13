import { useRef } from "react";
import { Card } from "@/components/ui/Card";
import { DepartmentChip } from "@/components/chat/Badges";
import { ConfidenceBadge } from "@/components/chat/Badges";
import {
  Activity,
  Gauge,
  Hash,
  ShieldX,
  ThumbsDown,
  ThumbsUp,
  Timer,
} from "@/components/ui/icons";
import type { IconProps } from "@/components/ui/icons";
import { formatDate, formatMs, formatPercent } from "@/lib/format";
import { attachPerspectiveTilt, runStaggerEnter, useGSAP } from "@/lib/gsap";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { DashboardData } from "@/lib/types";
import type { ComponentType } from "react";

interface MetricsGridProps {
  data: DashboardData;
}

type MetricDef = {
  label: string;
  value: string;
  icon: ComponentType<IconProps>;
};

export function MetricsGrid({ data }: MetricsGridProps) {
  const locale = useUserStore((s) => s.locale);
  const gridRef = useRef<HTMLDivElement>(null);

  const metrics: MetricDef[] = [
    { label: t("totalQueries", locale), value: data.query_count.toLocaleString(), icon: Hash },
    { label: t("refusalRate", locale), value: formatPercent(data.refusal_rate), icon: ShieldX },
    { label: t("latencyP50", locale), value: formatMs(data.latency_p50_ms), icon: Gauge },
    { label: t("latencyP95", locale), value: formatMs(data.latency_p95_ms), icon: Timer },
    { label: t("feedbackUp", locale), value: data.feedback_up.toLocaleString(), icon: ThumbsUp },
    { label: t("feedbackDown", locale), value: data.feedback_down.toLocaleString(), icon: ThumbsDown },
  ];

  useGSAP(
    () => {
      const cards = gridRef.current?.querySelectorAll("[data-metric-card]");
      if (!cards?.length) return;

      const cleanupStagger = runStaggerEnter(cards);
      const tiltCleanups = [...cards].map((card) =>
        attachPerspectiveTilt(card as HTMLElement, { maxTilt: 5 }),
      );

      return () => {
        cleanupStagger();
        tiltCleanups.forEach((fn) => fn());
      };
    },
    { scope: gridRef },
  );

  return (
    <div ref={gridRef} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {metrics.map((m) => {
        const MetricIcon = m.icon;
        return (
          <Card
            key={m.label}
            data-metric-card
            padding="sm"
            className="metric-card-3d group transition-shadow hover:shadow-glow"
          >
            <div className="flex items-start justify-between gap-3">
              <p className="text-xs font-medium uppercase tracking-wide text-content-secondary">
                {m.label}
              </p>
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-muted text-brand transition-transform group-hover:scale-110">
                <MetricIcon size="sm" />
              </span>
            </div>
            <p className="mt-2 text-2xl font-bold text-content-primary">{m.value}</p>
          </Card>
        );
      })}
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
      <div className="flex flex-col items-center py-8 text-center" role="status">
        <Activity size="lg" className="mb-3 text-content-muted opacity-60" />
        <p className="text-sm text-content-secondary">{t("noHistory", locale)}</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm text-left">
        <thead>
          <tr className="border-b border-border text-content-secondary">
            <th className="py-2 pr-4 font-medium" scope="col">
              {t("historyTime", locale)}
            </th>
            <th className="py-2 pr-4 font-medium" scope="col">
              {t("historyQuestion", locale)}
            </th>
            <th className="py-2 pr-4 font-medium" scope="col">
              {t("historyDepartments", locale)}
            </th>
            <th className="py-2 pr-4 font-medium" scope="col">
              {t("historyStatus", locale)}
            </th>
            <th className="py-2 font-medium" scope="col">
              {t("historyLatency", locale)}
            </th>
          </tr>
        </thead>
        <tbody>
          {history.map((item, i) => (
            <tr key={`${item.ts}-${i}`} className="border-b border-border/60">
              <td className="py-3 pr-4 whitespace-nowrap text-content-secondary">
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
              <td className="py-3 text-content-secondary">{formatMs(item.latency_ms)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
