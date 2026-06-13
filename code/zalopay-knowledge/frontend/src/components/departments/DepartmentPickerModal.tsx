import { Button } from "@/components/ui/Button";
import { Check, Search, X } from "@/components/ui/icons";
import { useFocusTrap } from "@/hooks/useFocusTrap";
import {
  departmentDescription,
  departmentHeadManager,
  departmentMetaLabel,
  DEPARTMENTS,
  descriptionSnippet,
  filterDepartments,
  type DepartmentMeta,
} from "@/lib/departments";
import { classNames } from "@/lib/format";
import { runChipPop } from "@/lib/gsap";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { Department } from "@/lib/types";
import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";

interface DepartmentPickerModalProps {
  open: boolean;
  onClose: () => void;
  selected: Department[];
  onChange: (departments: Department[]) => void;
  departments?: DepartmentMeta[];
}

export function DepartmentPickerModal({
  open,
  onClose,
  selected,
  onChange,
  departments = DEPARTMENTS,
}: DepartmentPickerModalProps) {
  const locale = useUserStore((s) => s.locale);
  const dialogRef = useRef<HTMLDivElement>(null);
  const [query, setQuery] = useState("");
  const [expandedKey, setExpandedKey] = useState<Department | null>(null);

  useFocusTrap(open, dialogRef);

  useEffect(() => {
    if (!open) return;

    document.body.classList.add("dept-picker-open");
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.classList.remove("dept-picker-open");
      document.body.style.overflow = prevOverflow;
    };
  }, [open]);

  useEffect(() => {
    if (!open) {
      setQuery("");
      setExpandedKey(null);
      return;
    }

    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }

    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

  const filtered = useMemo(
    () => filterDepartments(departments, query, locale),
    [departments, query, locale],
  );

  function toggleDepartment(dept: Department, el?: HTMLButtonElement) {
    if (selected.includes(dept)) {
      onChange(selected.filter((d) => d !== dept));
      return;
    }
    if (el) runChipPop(el);
    onChange([...selected, dept]);
  }

  function toggleExpanded(dept: Department) {
    setExpandedKey((prev) => (prev === dept ? null : dept));
  }

  if (!open) return null;

  return createPortal(
    <div
      className="dept-picker-overlay fixed inset-0 flex items-end justify-center sm:items-center"
      role="presentation"
    >
      <button
        type="button"
        className="dept-picker-backdrop absolute inset-0"
        onClick={onClose}
        aria-label={t("closeAddDepartments", locale)}
      />

      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="dept-picker-title"
        className="dept-picker-modal relative flex max-h-[min(85dvh,640px)] w-full max-w-lg flex-col rounded-t-2xl sm:rounded-2xl"
      >
        <header className="flex flex-shrink-0 items-start justify-between gap-3 border-b border-border px-4 py-3 sm:px-5">
          <div>
            <h2 id="dept-picker-title" className="text-base font-semibold text-content-primary">
              {t("addDepartmentModalTitle", locale)}
            </h2>
            <p className="mt-0.5 text-xs text-content-secondary">
              {t("addDepartmentModalHint", locale)}
            </p>
          </div>
          <Button
            variant="ghost"
            className="flex-shrink-0 !px-2 !py-2"
            onClick={onClose}
            aria-label={t("closeAddDepartments", locale)}
          >
            <X size="sm" />
          </Button>
        </header>

        <div className="flex-shrink-0 border-b border-border px-4 py-3 sm:px-5">
          <label className="sr-only" htmlFor="dept-picker-search">
            {t("departmentSearchPlaceholder", locale)}
          </label>
          <div className="relative">
            <Search
              size="sm"
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-content-muted"
            />
            <input
              id="dept-picker-search"
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={t("departmentSearchPlaceholder", locale)}
              className="w-full rounded-lg border border-border bg-surface-base py-2 pl-9 pr-3 text-sm text-content-primary placeholder:text-content-muted focus:border-brand focus:ring-1 focus:ring-brand"
              autoComplete="off"
              spellCheck={false}
            />
          </div>
        </div>

        <div
          role="listbox"
          aria-multiselectable
          aria-label={t("addDepartmentModalTitle", locale)}
          className="min-h-0 flex-1 overflow-y-auto overscroll-contain chat-scroll"
        >
          {filtered.length === 0 ? (
            <p className="px-4 py-8 text-center text-sm text-content-secondary" role="status">
              {t("departmentSearchEmpty", locale)}
            </p>
          ) : (
            filtered.map((dept) => {
              const isSelected = selected.includes(dept.key);
              const isExpanded = expandedKey === dept.key;
              const name = departmentMetaLabel(dept, locale);
              const head = departmentHeadManager(dept, locale);
              const snippet = descriptionSnippet(departmentDescription(dept, locale));

              return (
                <div
                  key={dept.key}
                  className={classNames(
                    "dept-picker-row border-b border-border last:border-b-0",
                    isSelected && "bg-brand/5",
                  )}
                >
                  <div className="flex items-start gap-2 px-3 py-2.5 sm:px-4">
                    <button
                      type="button"
                      role="option"
                      aria-selected={isSelected}
                      aria-expanded={isExpanded}
                      onClick={() => toggleExpanded(dept.key)}
                      className="dept-picker-row-main min-w-0 flex-1 rounded-lg px-2 py-1 text-left transition-colors focus-visible:outline-none"
                    >
                      <span className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
                        <span
                          className="text-sm font-medium text-content-primary"
                          style={{ color: isSelected ? dept.accent_color : undefined }}
                        >
                          {name}
                        </span>
                        <span className="text-xs text-content-secondary">{head}</span>
                      </span>
                      {!isExpanded && (
                        <span className="mt-0.5 block text-xs leading-snug text-content-muted line-clamp-1">
                          {snippet}
                        </span>
                      )}
                    </button>

                    <button
                      type="button"
                      onClick={(e) => toggleDepartment(dept.key, e.currentTarget)}
                      className={classNames(
                        "dept-picker-quick-add mt-0.5 inline-flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg border transition-colors",
                        isSelected
                          ? "border-transparent text-white"
                          : "border-border bg-surface-glass text-content-secondary hover:border-brand/40 hover:bg-brand/10 hover:text-brand",
                      )}
                      style={
                        isSelected ? { backgroundColor: dept.accent_color } : undefined
                      }
                      aria-label={
                        isSelected
                          ? t("deselectDepartment", locale, { name })
                          : t("selectDepartment", locale, { name })
                      }
                      title={
                        isSelected
                          ? t("deselectDepartment", locale, { name })
                          : t("selectDepartment", locale, { name })
                      }
                      aria-pressed={isSelected}
                    >
                      <Check size="sm" />
                    </button>
                  </div>

                  {isExpanded && (
                    <div className="dept-picker-row-expanded border-t border-border/60 px-4 pb-3 pt-2 sm:px-5">
                      <p className="text-xs font-medium text-content-secondary">
                        {t("departmentHeadLabel", locale)}
                      </p>
                      <p className="text-sm text-content-primary">{head}</p>
                      <p className="mt-2 text-xs font-medium text-content-secondary">
                        {t("departmentDescriptionLabel", locale)}
                      </p>
                      <p className="text-sm leading-relaxed text-content-secondary">
                        {departmentDescription(dept, locale)}
                      </p>
                      <Button
                        variant="secondary"
                        className="mt-3 !px-3 !py-1.5 text-xs"
                        onClick={(e) => toggleDepartment(dept.key, e.currentTarget)}
                      >
                        {isSelected
                          ? t("deselectDepartmentAction", locale)
                          : t("selectDepartmentAction", locale)}
                      </Button>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        <footer className="flex flex-shrink-0 justify-end border-t border-border px-4 py-3 sm:px-5">
          <Button variant="secondary" onClick={onClose}>
            {t("done", locale)}
          </Button>
        </footer>
      </div>
    </div>,
    document.body,
  );
}
