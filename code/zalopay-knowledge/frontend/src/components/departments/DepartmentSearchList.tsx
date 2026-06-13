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
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { Department } from "@/lib/types";
import { useMemo, useState } from "react";

interface DepartmentSearchListProps {
  selected: Department[];
  onChange: (departments: Department[]) => void;
  /** When false, selecting one department replaces the current selection. */
  multiple?: boolean;
  departments?: DepartmentMeta[];
  searchPlaceholder?: string;
  emptyMessage?: string;
  listClassName?: string;
  maxListHeightClass?: string;
}

export function DepartmentSearchList({
  selected,
  onChange,
  multiple = true,
  departments = DEPARTMENTS,
  searchPlaceholder,
  emptyMessage,
  listClassName,
  maxListHeightClass = "max-h-52",
}: DepartmentSearchListProps) {
  const locale = useUserStore((s) => s.locale);
  const resolvedPlaceholder =
    searchPlaceholder ?? t("departmentSearchPlaceholder", locale);
  const resolvedEmptyMessage = emptyMessage ?? t("departmentSearchEmpty", locale);
  const [query, setQuery] = useState("");

  const filtered = useMemo(
    () => filterDepartments(departments, query, locale),
    [departments, query, locale],
  );

  function toggleDepartment(dept: Department) {
    if (multiple) {
      if (selected.includes(dept)) {
        onChange(selected.filter((d) => d !== dept));
      } else {
        onChange([...selected, dept]);
      }
      return;
    }

    onChange(selected.includes(dept) ? [] : [dept]);
  }

  return (
    <div className="space-y-2">
      <label className="sr-only" htmlFor="department-search">
        {resolvedPlaceholder}
      </label>
      <input
        id="department-search"
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={resolvedPlaceholder}
        className="w-full rounded-lg border border-border bg-surface-base px-3 py-2 text-sm text-content-primary placeholder:text-content-muted focus:border-brand focus:ring-1 focus:ring-brand"
        autoComplete="off"
        spellCheck={false}
      />

      <div
        role="listbox"
        aria-multiselectable={multiple}
        className={classNames(
          "overflow-y-auto rounded-lg border border-border bg-surface-glass chat-scroll",
          maxListHeightClass,
          listClassName,
        )}
      >
        {filtered.length === 0 ? (
          <p className="px-3 py-4 text-sm text-content-secondary" role="status">
            {resolvedEmptyMessage}
          </p>
        ) : (
          filtered.map((dept) => {
            const isSelected = selected.includes(dept.key);
            const name = departmentMetaLabel(dept, locale);
            const head = departmentHeadManager(dept, locale);
            const snippet = descriptionSnippet(departmentDescription(dept, locale));

            return (
              <button
                key={dept.key}
                type="button"
                role="option"
                aria-selected={isSelected}
                onClick={() => toggleDepartment(dept.key)}
                className={classNames(
                  "dept-search-row flex w-full items-start gap-3 border-b border-border px-3 py-2.5 text-left transition-colors last:border-b-0",
                  isSelected ? "bg-brand/10" : "hover:bg-surface-glass",
                )}
              >
                <span
                  aria-hidden
                  className={classNames(
                    "mt-0.5 inline-flex h-4 w-4 flex-shrink-0 items-center justify-center rounded border text-[10px] font-bold",
                    isSelected
                      ? "border-transparent text-white"
                      : "border-border-strong bg-surface-base text-transparent",
                  )}
                  style={isSelected ? { backgroundColor: dept.accent_color } : undefined}
                >
                  ✓
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
                    <span className="text-sm font-medium text-content-primary">{name}</span>
                    <span className="text-xs text-content-secondary">{head}</span>
                  </span>
                  <span className="mt-0.5 block text-xs leading-snug text-content-secondary/90 line-clamp-2">
                    {snippet}
                  </span>
                </span>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
