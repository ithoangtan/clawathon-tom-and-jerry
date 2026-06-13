import { Badge } from "@/components/ui/Badge";
import { departmentLabel, getDepartment } from "@/lib/departments";
import { formatConfidence } from "@/lib/format";
import { attachHoverLift, useGSAP } from "@/lib/gsap";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { AnswerStatus, RefusalReason } from "@/lib/types";
import { useRef } from "react";

interface ConfidenceBadgeProps {
  confidence: number;
  status: AnswerStatus;
  refusalReason?: RefusalReason | null;
}

export function ConfidenceBadge({ confidence, status, refusalReason }: ConfidenceBadgeProps) {
  const locale = useUserStore((s) => s.locale);

  const statusTone =
    status === "answered" ? "success" : status === "partial" ? "warning" : "danger";

  const statusLabel =
    status === "answered"
      ? t("statusAnswered", locale)
      : status === "partial"
        ? t("statusPartial", locale)
        : refusalReason === "access_denied"
          ? t("statusAccessDenied", locale)
          : t("statusRefused", locale);

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge tone={statusTone}>{statusLabel}</Badge>
      <span className="text-xs text-content-secondary">
        {t("confidence", locale)}: {formatConfidence(confidence)}
      </span>
    </div>
  );
}

interface DepartmentChipProps {
  deptKey: string;
  interactive?: boolean;
}

export function DepartmentChip({ deptKey, interactive }: DepartmentChipProps) {
  const locale = useUserStore((s) => s.locale);
  const dept = getDepartment(deptKey as Parameters<typeof getDepartment>[0]);
  const chipRef = useRef<HTMLSpanElement>(null);

  useGSAP(
    () => {
      if (!interactive) return;
      const el = chipRef.current;
      if (!el) return;
      return attachHoverLift(el, { y: -2, scale: 1.04 });
    },
    { scope: chipRef, dependencies: [interactive] },
  );

  return (
    <span
      ref={chipRef}
      className={
        interactive
          ? "dept-chip-interactive inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium text-white shadow-sm"
          : "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium text-white shadow-sm"
      }
      style={{ backgroundColor: dept.accent_color }}
    >
      {departmentLabel(dept.key, locale)}
    </span>
  );
}
