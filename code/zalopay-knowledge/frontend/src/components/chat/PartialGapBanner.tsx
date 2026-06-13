import { AlertCircle } from "@/components/ui/icons";
import { departmentLabel } from "@/lib/departments";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { Department } from "@/lib/types";

interface PartialGapBannerProps {
  /** Departments that were queried but returned no usable answer. */
  refusals?: Department[] | null;
}

/** Surfaces the partial-answer ladder tier when some department branches refused. */
export function PartialGapBanner({ refusals }: PartialGapBannerProps) {
  const locale = useUserStore((s) => s.locale);
  const depts = refusals?.filter(Boolean) ?? [];

  return (
    <div
      role="note"
      className="mt-4 rounded-lg border border-amber-200/90 bg-amber-50/80 px-4 py-3 text-sm text-amber-950"
    >
      <div className="flex gap-2.5">
        <AlertCircle size="sm" className="mt-0.5 flex-shrink-0 text-amber-700" aria-hidden />
        <div>
          <p>{t("partialGapHint", locale)}</p>
          {depts.length > 0 && (
            <p className="mt-1 text-amber-900/90">
              {t("partialGapDepartments", locale, {
                departments: depts.map((d) => departmentLabel(d, locale)).join(", "),
              })}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
