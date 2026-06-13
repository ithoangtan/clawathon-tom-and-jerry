import { departmentLabel, DEPARTMENTS } from "@/lib/departments";
import { classNames } from "@/lib/format";
import { runChipPop } from "@/lib/gsap";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { Department } from "@/lib/types";

interface DepartmentTargetBarProps {
  selected: Department[];
  onChange: (departments: Department[]) => void;
}

export function DepartmentTargetBar({ selected, onChange }: DepartmentTargetBarProps) {
  const locale = useUserStore((s) => s.locale);
  const autoRoute = selected.length === 0;

  function toggle(dept: Department, el: HTMLButtonElement) {
    runChipPop(el);
    if (selected.includes(dept)) {
      onChange(selected.filter((d) => d !== dept));
    } else {
      onChange([...selected, dept]);
    }
  }

  function selectAuto(el: HTMLButtonElement) {
    runChipPop(el);
    onChange([]);
  }

  return (
    <div
      className="flex flex-wrap items-center gap-2"
      role="group"
      aria-label={t("targetDepartments", locale)}
    >
      <span className="text-xs font-medium text-content-secondary mr-1">
        {t("targetDepartments", locale)}:
      </span>

      <button
        type="button"
        onClick={(e) => selectAuto(e.currentTarget)}
        className={classNames(
          "dept-chip-interactive rounded-full px-3 py-1 text-xs font-medium transition-colors",
          autoRoute
            ? "bg-gradient-to-r from-brand to-brand-dark text-white shadow-sm shadow-brand/20"
            : "bg-slate-100 text-content-secondary hover:bg-slate-200",
        )}
        aria-pressed={autoRoute}
      >
        {t("targetAll", locale)}
      </button>

      {DEPARTMENTS.map((dept) => {
        const isSelected = selected.includes(dept.key);
        return (
          <button
            key={dept.key}
            type="button"
            onClick={(e) => toggle(dept.key, e.currentTarget)}
            className={classNames(
              "dept-chip-interactive rounded-full px-3 py-1 text-xs font-medium transition-colors border-2",
              isSelected
                ? "text-white border-transparent shadow-sm"
                : "bg-white/80 text-content-secondary border-slate-200/80 hover:border-brand/30",
            )}
            style={isSelected ? { backgroundColor: dept.accent_color } : undefined}
            aria-pressed={isSelected}
          >
            {departmentLabel(dept.key, locale)}
          </button>
        );
      })}
    </div>
  );
}
