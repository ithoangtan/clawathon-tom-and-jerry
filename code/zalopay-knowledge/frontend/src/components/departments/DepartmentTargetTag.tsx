import { X } from "@/components/ui/icons";
import {
  departmentDescription,
  departmentHeadManager,
  departmentLabel,
  descriptionSnippet,
  getDepartment,
} from "@/lib/departments";
import { classNames } from "@/lib/format";
import { runChipPop } from "@/lib/gsap";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { Department } from "@/lib/types";
import { useCallback, useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";

const TOOLTIP_GAP_PX = 8;
const TOOLTIP_EST_HEIGHT_PX = 140;

type TooltipPlacement = "top" | "bottom";

interface TooltipPosition {
  top: number;
  left: number;
  placement: TooltipPlacement;
}

interface DepartmentTargetTagProps {
  deptKey: Department;
  onRemove: (dept: Department) => void;
}

export function DepartmentTargetTag({ deptKey, onRemove }: DepartmentTargetTagProps) {
  const locale = useUserStore((s) => s.locale);
  const dept = getDepartment(deptKey);
  const label = departmentLabel(deptKey, locale);
  const tooltipId = useId();
  const removeLabel = t("removeDepartment", locale, { name: label });

  const triggerRef = useRef<HTMLSpanElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState<TooltipPosition>({
    top: 0,
    left: 0,
    placement: "top",
  });

  const updateTooltipPosition = useCallback(() => {
    const trigger = triggerRef.current;
    if (!trigger) return;

    const rect = trigger.getBoundingClientRect();
    const tooltipHeight = tooltipRef.current?.offsetHeight ?? TOOLTIP_EST_HEIGHT_PX;
    const spaceAbove = rect.top;
    const spaceBelow = window.innerHeight - rect.bottom;
    const placement: TooltipPlacement =
      spaceAbove >= tooltipHeight + TOOLTIP_GAP_PX || spaceBelow < spaceAbove ? "top" : "bottom";

    setTooltipPosition({
      top: placement === "top" ? rect.top - TOOLTIP_GAP_PX : rect.bottom + TOOLTIP_GAP_PX,
      left: rect.left + rect.width / 2,
      placement,
    });
  }, []);

  const showTooltip = useCallback(() => {
    setTooltipVisible(true);
  }, []);

  const hideTooltip = useCallback(() => {
    setTooltipVisible(false);
  }, []);

  useEffect(() => {
    if (!tooltipVisible) return;

    updateTooltipPosition();

    const onScrollOrResize = () => updateTooltipPosition();
    window.addEventListener("scroll", onScrollOrResize, true);
    window.addEventListener("resize", onScrollOrResize);

    return () => {
      window.removeEventListener("scroll", onScrollOrResize, true);
      window.removeEventListener("resize", onScrollOrResize);
    };
  }, [tooltipVisible, updateTooltipPosition]);

  useEffect(() => {
    if (!tooltipVisible) return;
    updateTooltipPosition();
  }, [tooltipVisible, updateTooltipPosition]);

  const handleRemove = useCallback(
    (el: HTMLButtonElement) => {
      runChipPop(el);
      onRemove(deptKey);
    },
    [deptKey, onRemove],
  );

  const handleBlur = useCallback(
    (e: React.FocusEvent<HTMLSpanElement>) => {
      if (!e.currentTarget.contains(e.relatedTarget as Node | null)) {
        hideTooltip();
      }
    },
    [hideTooltip],
  );

  return (
    <span
      ref={triggerRef}
      className="dept-target-tag group relative inline-flex"
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={handleBlur}
    >
      <span
        className="dept-chip-interactive dept-target-tag-chip inline-flex items-center rounded-full py-1 pl-3 pr-1 text-xs font-medium text-white shadow-sm"
        style={{ backgroundColor: dept.accent_color }}
        aria-describedby={tooltipVisible ? tooltipId : undefined}
        tabIndex={0}
      >
        <span className="min-w-0 truncate">{label}</span>
        <button
          type="button"
          className="dept-target-tag-remove ml-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-black/20 text-white/90 transition-all duration-fast hover:bg-black/35 hover:text-white focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
          onClick={(e) => {
            e.stopPropagation();
            handleRemove(e.currentTarget);
          }}
          aria-label={removeLabel}
        >
          <X size="xs" />
        </button>
      </span>

      {tooltipVisible &&
        createPortal(
          <div
            ref={tooltipRef}
            id={tooltipId}
            role="tooltip"
            className={classNames(
              "dept-tag-tooltip dept-tag-tooltip--portal pointer-events-none w-64",
              tooltipPosition.placement === "top"
                ? "dept-tag-tooltip--top"
                : "dept-tag-tooltip--bottom",
            )}
            style={{
              top: tooltipPosition.top,
              left: tooltipPosition.left,
            }}
          >
            <div className="relative rounded-xl border border-border-strong bg-surface-glass p-3 text-left shadow-glass">
              <p className="text-sm font-semibold text-content-primary">{label}</p>
              <p className="mt-1 text-xs text-content-secondary">
                {t("departmentHeadLabel", locale)}: {departmentHeadManager(dept, locale)}
              </p>
              <p className="mt-1.5 text-xs leading-relaxed text-content-secondary">
                {descriptionSnippet(departmentDescription(dept, locale), 120)}
              </p>
            </div>
          </div>,
          document.body,
        )}
    </span>
  );
}
