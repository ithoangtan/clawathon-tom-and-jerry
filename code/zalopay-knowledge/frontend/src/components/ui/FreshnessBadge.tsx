import { Badge } from "@/components/ui/Badge";
import { freshnessLevel, formatFreshnessHours } from "@/lib/format";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";

interface FreshnessBadgeProps {
  lastSuccessAt?: string | null;
  freshnessHours?: number | null;
}

export function FreshnessBadge({ lastSuccessAt, freshnessHours }: FreshnessBadgeProps) {
  const locale = useUserStore((s) => s.locale);
  const level = freshnessLevel(lastSuccessAt, freshnessHours);

  const label =
    level === "red"
      ? t("neverSynced", locale)
      : level === "green"
        ? t("fresh", locale)
        : t("stale", locale);

  const tone = level === "green" ? "success" : level === "amber" ? "warning" : "danger";

  return (
    <Badge tone={tone} title={formatFreshnessHours(freshnessHours)}>
      {label}
      {freshnessHours != null && level !== "red" && (
        <span className="ml-1 opacity-75">({formatFreshnessHours(freshnessHours)})</span>
      )}
    </Badge>
  );
}
