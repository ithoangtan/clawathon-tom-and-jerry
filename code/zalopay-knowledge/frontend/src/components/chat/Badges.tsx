import { Badge } from "@/components/ui/Badge";
import { departmentLabel, departmentDescription, getDepartment } from "@/lib/departments";
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
  /** When the router asks which department to query, avoid showing a refusal label. */
  clarifying?: boolean;
}

export function ConfidenceBadge({
  confidence,
  status,
  refusalReason,
  clarifying,
}: ConfidenceBadgeProps) {
  const locale = useUserStore((s) => s.locale);

  // Agent action progress messages: show a single distinct badge, no confidence.
  if (status === "agent_action") {
    return (
      <Badge tone="info" style={{ cursor: "default" }}>
        {t("statusAgentAction", locale)}
      </Badge>
    );
  }

  const statusTone = clarifying
    ? "warning"
    : status === "answered"
      ? "success"
      : status === "partial"
        ? "warning"
        : "danger";

  const statusLabel = clarifying
    ? t("statusClarify", locale)
    : status === "answered"
      ? t("statusAnswered", locale)
      : status === "partial"
        ? t("statusPartial", locale)
        : refusalReason === "access_denied"
          ? t("statusAccessDenied", locale)
          : refusalReason === "out_of_scope"
            ? t("statusOutOfScope", locale)
            : t("statusRefused", locale);

  const statusTooltip = clarifying
    ? t("tooltipStatusClarify", locale)
    : status === "answered"
      ? t("tooltipStatusAnswered", locale)
      : status === "partial"
        ? t("tooltipStatusPartial", locale)
        : t("tooltipStatusRefused", locale);

  const hasValidConfidence = confidence != null && !isNaN(confidence);

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge tone={statusTone} title={statusTooltip} style={{ cursor: "help" }}>{statusLabel}</Badge>
      {hasValidConfidence && (() => {
        const tierTone = confidence >= 0.80 ? "success" : confidence >= 0.55 ? "warning" : "danger";
        const tierKey = confidence >= 0.80 ? "confidenceHigh" : confidence >= 0.55 ? "confidenceMedium" : "confidenceLow";
        return (
          <Badge tone={tierTone} title={t("tooltipConfidence", locale)} style={{ cursor: "help" }}>
            {t(tierKey as Parameters<typeof t>[0], locale)} · {formatConfidence(confidence)}
          </Badge>
        );
      })()}
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

  const description = departmentDescription(dept, locale);

  return (
    <span
      ref={chipRef}
      className={
        interactive
          ? "dept-chip-interactive inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium text-white shadow-sm"
          : "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium text-white shadow-sm"
      }
      style={{ backgroundColor: dept.accent_color, cursor: "help" }}
      title={description}
    >
      {departmentLabel(dept.key, locale)}
    </span>
  );
}
