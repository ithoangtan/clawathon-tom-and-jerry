import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card } from "@/components/ui/Card";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { t } from "@/lib/i18n";
import { useAdminSyncStatus } from "@/hooks/useAdminSyncStatus";
import { useUserStore } from "@/store/userStore";
import type { AdminSyncJob } from "@/lib/types";

const DAYS = 14;

const COLORS = {
  success: "#10b981",
  failure: "#ef4444",
  running: "#3b82f6",
};

function buildDayBuckets(jobs: AdminSyncJob[]) {
  const today = new Date();
  const buckets: Record<string, { date: string; label: string; success: number; failure: number; running: number }> = {};

  for (let i = DAYS - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    const label = `${d.getDate()}/${d.getMonth() + 1}`;
    buckets[key] = { date: key, label, success: 0, failure: 0, running: 0 };
  }

  for (const job of jobs) {
    const key = job.started_at.slice(0, 10);
    if (!buckets[key]) continue;
    if (job.state === "success") buckets[key].success++;
    else if (job.state === "failure") buckets[key].failure++;
    else buckets[key].running++;
  }

  return Object.values(buckets);
}

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: { name: string; value: number; fill: string }[]; label?: string }) {
  if (!active || !payload?.length) return null;
  const total = payload.reduce((s, p) => s + (p.value ?? 0), 0);
  if (total === 0) return null;
  return (
    <div className="rounded-lg border border-border bg-surface-elevated px-3 py-2 text-xs shadow-glass">
      <p className="mb-1 font-semibold text-content-primary">{label}</p>
      {payload.map((p) =>
        p.value > 0 ? (
          <p key={p.name} style={{ color: p.fill }}>
            {p.name}: {p.value}
          </p>
        ) : null,
      )}
    </div>
  );
}

export function AdminSyncTimeline() {
  const locale = useUserStore((s) => s.locale);
  const { status, loading } = useAdminSyncStatus();

  const jobs = status?.recent_jobs ?? [];
  const data = useMemo(() => buildDayBuckets(jobs), [jobs]);

  const legendItems = (["success", "failure", "running"] as const).map((k) => ({
    key: k,
    color: COLORS[k],
    label:
      k === "success"
        ? t("adminJobSuccess", locale)
        : k === "failure"
          ? t("adminJobFailure", locale)
          : t("adminJobRunning", locale),
  }));

  return (
    <Card>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-semibold text-content-primary">{t("adminSyncHistory", locale)}</h3>
        <div className="flex items-center gap-4 text-xs text-content-secondary">
          {legendItems.map((item) => (
            <span key={item.key} className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm" style={{ background: item.color }} />
              {item.label}
            </span>
          ))}
        </div>
      </div>

      {loading && !status ? (
        <LoadingSpinner />
      ) : jobs.length === 0 ? (
        <p className="py-8 text-center text-sm text-content-muted">{t("adminNoJobs", locale)}</p>
      ) : (
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={data} margin={{ top: 4, right: 4, bottom: 4, left: 0 }} barSize={14}>
            <CartesianGrid vertical={false} stroke="var(--color-border)" strokeDasharray="3 3" />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 10, fill: "var(--color-text-muted)" }}
              tickLine={false}
              axisLine={false}
              interval={2}
            />
            <YAxis
              allowDecimals={false}
              tick={{ fontSize: 10, fill: "var(--color-text-muted)" }}
              tickLine={false}
              axisLine={false}
              width={24}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: "var(--color-bg-glass)", radius: 4 }} />
            <Bar dataKey="success" stackId="a" fill={COLORS.success} radius={[0, 0, 0, 0]}>
              {data.map((entry, i) => (
                <Cell key={i} fill={COLORS.success} opacity={entry.success > 0 ? 0.9 : 0} />
              ))}
            </Bar>
            <Bar dataKey="failure" stackId="a" fill={COLORS.failure} radius={[0, 0, 0, 0]}>
              {data.map((entry, i) => (
                <Cell key={i} fill={COLORS.failure} opacity={entry.failure > 0 ? 0.9 : 0} />
              ))}
            </Bar>
            <Bar dataKey="running" stackId="a" fill={COLORS.running} radius={[3, 3, 0, 0]}>
              {data.map((entry, i) => (
                <Cell key={i} fill={COLORS.running} opacity={entry.running > 0 ? 0.9 : 0} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
