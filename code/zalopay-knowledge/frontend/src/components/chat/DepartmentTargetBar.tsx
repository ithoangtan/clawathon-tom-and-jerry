import { DepartmentPickerModal } from "@/components/departments/DepartmentPickerModal";
import { DepartmentTargetTag } from "@/components/departments/DepartmentTargetTag";
import { Plus, Wand2, X } from "@/components/ui/icons";
import { useTutorialPauseOptional } from "@/hooks/useTutorial";
import { runChipPop } from "@/lib/gsap";
import { t } from "@/lib/i18n";
import { classNames } from "@/lib/format";
import { useUserStore } from "@/store/userStore";
import type { Department } from "@/lib/types";
import { useState } from "react";

interface DepartmentTargetBarProps {
  selected: Department[];
  autoRoute: boolean;
  onChange: (departments: Department[]) => void;
  onAutoRouteChange: (autoRoute: boolean) => void;
  className?: string;
  compact?: boolean;
}

export function DepartmentTargetBar({
  selected,
  autoRoute,
  onChange,
  onAutoRouteChange,
  className,
  compact = false,
}: DepartmentTargetBarProps) {
  const locale = useUserStore((s) => s.locale);
  const { pauseTutorial, isRunning: tutorialRunning } = useTutorialPauseOptional();
  const [pickerOpen, setPickerOpen] = useState(false);

  function enableAutoRoute(el: HTMLButtonElement) {
    runChipPop(el);
    onAutoRouteChange(true);
  }

  function disableAutoRoute(el: HTMLButtonElement) {
    runChipPop(el);
    onAutoRouteChange(false);
  }

  function removeDepartment(dept: Department) {
    onChange(selected.filter((d) => d !== dept));
  }

  function openPicker(el: HTMLButtonElement) {
    runChipPop(el);
    if (tutorialRunning) pauseTutorial();
    if (autoRoute) {
      onAutoRouteChange(false);
    }
    setPickerOpen(true);
  }

  return (
    <>
      <div
        className={classNames(
          "dept-target-bar__tags flex flex-wrap items-center gap-2",
          compact && "justify-start gap-1.5",
          className,
        )}
        role="group"
        aria-label={t("targetDepartments", locale)}
        data-tour="department-bar"
      >
        <span
          className={classNames(
            "text-xs font-medium text-content-secondary",
            compact ? "sr-only" : "mr-1",
          )}
        >
          {t("targetDepartments", locale)}:
        </span>

        {autoRoute ? (
          <span className="dept-auto-route dept-target-tag group relative inline-flex">
            <span
              className={classNames(
                "dept-chip-interactive dept-auto-route-chip inline-flex items-center rounded-full py-1 pl-3 pr-1 text-xs font-medium",
                "bg-gradient-to-r from-brand to-brand-dark text-white shadow-sm shadow-brand/20",
              )}
              aria-pressed="true"
              tabIndex={0}
            >
              <Wand2 size="xs" className="mr-1 inline shrink-0 opacity-90" />
              <span className="min-w-0 truncate">{t("targetAll", locale)}</span>
              <button
                type="button"
                className="dept-target-tag-remove dept-auto-route-remove ml-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-black/20 text-white/90 transition-all duration-fast hover:bg-black/35 hover:text-white focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
                onClick={(e) => {
                  e.stopPropagation();
                  disableAutoRoute(e.currentTarget);
                }}
                aria-label={t("turnOffAutoRoute", locale)}
              >
                <X size="xs" />
              </button>
            </span>
          </span>
        ) : (
          <button
            type="button"
            onClick={(e) => enableAutoRoute(e.currentTarget)}
            className={classNames(
              "dept-chip-interactive rounded-full px-3 py-1 text-xs font-medium transition-colors",
              "border border-border bg-surface-glass text-content-secondary hover:border-border-strong hover:bg-surface",
            )}
            aria-pressed={false}
            aria-label={t("enableAutoRoute", locale)}
          >
            <Wand2 size="xs" className="mr-1 inline opacity-90" />
            {t("targetAll", locale)}
          </button>
        )}

        {!autoRoute &&
          selected.map((deptKey) => (
            <DepartmentTargetTag key={deptKey} deptKey={deptKey} onRemove={removeDepartment} />
          ))}

        <button
          type="button"
          onClick={(e) => openPicker(e.currentTarget)}
          className="dept-chip-interactive inline-flex h-7 w-7 items-center justify-center rounded-full border border-dashed border-border-strong bg-surface-glass text-content-secondary transition-colors hover:border-brand/50 hover:bg-brand/10 hover:text-brand"
          aria-label={t("addDepartment", locale)}
          aria-haspopup="dialog"
          aria-expanded={pickerOpen}
        >
          <Plus size="sm" />
        </button>
      </div>

      <DepartmentPickerModal
        open={pickerOpen}
        onClose={() => setPickerOpen(false)}
        selected={selected}
        onChange={onChange}
      />
    </>
  );
}
