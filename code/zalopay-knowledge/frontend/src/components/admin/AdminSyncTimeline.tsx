import { useMemo } from "react";
import { Card } from "@/components/ui/Card";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { t } from "@/lib/i18n";
import { useAdminSyncStatus } from "@/hooks/useAdminSyncStatus";
import { useUserStore } from "@/store/userStore";
import type { AdminSyncJob } from "@/lib/types";

const DAYS = 14;
const BAR_COLORS = {
  success: "#10b981",
  failure: "#ef4444",
  running: "#3b82f6",
};

function getDayKey(iso: string): string {
  return iso.slice(0, 10); // YYYY-MM-DD
}

function buildDayBuckets(jobs: AdminSyncJob[]): {
  date: string;
  label: string;
  success: number;
  failure: number;
  running: number;
  total: number;
}[] {
  const today = new Date();
  const buckets: Record<string, { success: number; failure: number; running: number }> = {};

  // pre-fill 14 days
  for (let i = DAYS - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    buckets[key] = { success: 0, failure: 0, running: 0 };
  }

  for (const job of jobs) {
    const key = getDayKey(job.started_at);
    if (!buckets[key]) continue;
    if (job.state === "success") buckets[key].success++;
    else if (job.state === "failure") buckets[key].failure++;
    else buckets[key].running++;
  }

  return Object.entries(buckets).map(([date, counts]) => {
    const d = new Date(date + "T00:00:00");
    const label = `${d.getDate()}/${d.getMonth() + 1}`;
    return { date, label, ...counts, total: counts.success + counts.failure + counts.running };
  });
}

const CHART_H = 140;
const PADDING_L = 32;
const PADDING_R = 12;
const PADDING_T = 12;
const PADDING_B = 28;

export function AdminSyncTimeline() {
  const locale = useUserStore((s) => s.locale);
  const { status, loading } = useAdminSyncStatus();

  const jobs = status?.recent_jobs ?? [];
  const buckets = useMemo(() => buildDayBuckets(jobs), [jobs]);

  const maxTotal = Math.max(...buckets.map((b) => b.total), 1);

  // Responsive: we use a viewBox with fixed width so SVG scales automatically
  const SVG_W = 560;
  const chartW = SVG_W - PADDING_L - PADDING_R;
  const chartH = CHART_H - PADDING_T - PADDING_B;

  const barW = Math.max((chartW / DAYS) * 0.55, 6);
  const gap = chartW / DAYS;

  const yLabels = [maxTotal, Math.ceil(maxTotal / 2), 0];

  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-semibold text-slate-800">{t("adminSyncHistory", locale)}</h3>
        <div className="flex items-center gap-4 text-xs text-slate-500">
          {(["success", "failure", "running"] as const).map((k) => (
            <span key={k} className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm" style={{ background: BAR_COLORS[k] }} />
              {k === "success"
                ? t("adminJobSuccess", locale)
                : k === "failure"
                  ? t("adminJobFailure", locale)
                  : t("adminJobRunning", locale)}
            </span>
          ))}
        </div>
      </div>

      {loading && !status ? (
        <LoadingSpinner />
      ) : jobs.length === 0 ? (
        <p className="py-8 text-center text-sm text-slate-400">{t("adminNoJobs", locale)}</p>
      ) : (
        <svg
          viewBox={`0 0 ${SVG_W} ${CHART_H}`}
          className="w-full"
          aria-label={t("adminSyncHistory", locale)}
          role="img"
        >
          {/* Y grid lines */}
          {yLabels.map((val, i) => {
            const y = PADDING_T + chartH - (val / maxTotal) * chartH;
            return (
              <g key={i}>
                <line
                  x1={PADDING_L}
                  x2={PADDING_L + chartW}
                  y1={y}
                  y2={y}
                  stroke="#e2e8f0"
                  strokeWidth={1}
                />
                <text
                  x={PADDING_L - 4}
                  y={y + 4}
                  textAnchor="end"
                  fontSize={9}
                  fill="#94a3b8"
                >
                  {val}
                </text>
              </g>
            );
          })}

          {/* Bars */}
          {buckets.map((bucket, i) => {
            const x = PADDING_L + i * gap + gap / 2 - barW / 2;
            const segments = [
              { key: "success" as const, count: bucket.success },
              { key: "failure" as const, count: bucket.failure },
              { key: "running" as const, count: bucket.running },
            ];

            let currentY = PADDING_T + chartH;
            const rects = segments
              .filter((s) => s.count > 0)
              .map((seg) => {
                const h = (seg.count / maxTotal) * chartH;
                currentY -= h;
                return (
                  <rect
                    key={seg.key}
                    x={x}
                    y={currentY}
                    width={barW}
                    height={h}
                    fill={BAR_COLORS[seg.key]}
                    rx={bucket.total === seg.count ? 3 : 0}
                    opacity={0.85}
                  />
                );
              });

            // round top of the whole bar
            const totalH = (bucket.total / maxTotal) * chartH;
            const barTopY = PADDING_T + chartH - totalH;

            return (
              <g key={bucket.date}>
                {bucket.total > 0 && (
                  <rect
                    x={x}
                    y={barTopY}
                    width={barW}
                    height={3}
                    rx={1.5}
                    fill="transparent"
                  />
                )}
                {rects}
                {/* Hover tooltip area */}
                <rect
                  x={x - 4}
                  y={PADDING_T}
                  width={barW + 8}
                  height={chartH}
                  fill="transparent"
                  className="cursor-default"
                >
                  <title>{`${bucket.date}: ${bucket.total} ${t("adminJobsDay", locale)} (✓${bucket.success} ✗${bucket.failure})`}</title>
                </rect>
                {/* X label */}
                {(i === 0 || i === DAYS - 1 || i % 3 === 0) && (
                  <text
                    x={x + barW / 2}
                    y={CHART_H - 6}
                    textAnchor="middle"
                    fontSize={9}
                    fill="#94a3b8"
                  >
                    {bucket.label}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      )}
    </Card>
  );
}
