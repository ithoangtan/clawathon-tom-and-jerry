import { Badge } from "@/components/ui/Badge";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { Citation } from "@/lib/types";

interface StalenessBadgeProps {
  citation: Citation;
}

export function StalenessBadge({ citation }: StalenessBadgeProps) {
  const locale = useUserStore((s) => s.locale);

  if (!citation.deprecated && citation.lifecycle_state !== "deprecated") {
    return null;
  }

  return (
    <div className="mt-2 flex flex-wrap items-center gap-2" role="note">
      <Badge tone="warning">{t("deprecatedWarning", locale)}</Badge>
      {citation.successor_url && (
        <a
          href={citation.successor_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs font-medium text-brand hover:underline"
        >
          {t("successorDoc", locale)} →
        </a>
      )}
    </div>
  );
}
