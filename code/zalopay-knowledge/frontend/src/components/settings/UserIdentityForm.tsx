import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Check } from "@/components/ui/icons";
import { DepartmentPickerModal } from "@/components/departments/DepartmentPickerModal";
import { DEPARTMENTS, ROLES, departmentMetaLabel, getDepartment, roleLabel } from "@/lib/departments";
import { classNames } from "@/lib/format";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { Department, Lang, Role } from "@/lib/types";
import { useEffect, useState } from "react";

const LANG_OPTIONS: { value: Lang; short: string; label: string }[] = [
  { value: "en", short: "EN", label: "English" },
  { value: "vi", short: "VI", label: "Tiếng Việt" },
];

export function UserIdentityForm() {
  const locale = useUserStore((s) => s.locale);
  const userId = useUserStore((s) => s.userId);
  const role = useUserStore((s) => s.role);
  const homeDept = useUserStore((s) => s.homeDept);
  const userLocale = useUserStore((s) => s.locale);
  const update = useUserStore((s) => s.update);

  const [draftUserId, setDraftUserId] = useState(userId);
  const [draftRole, setDraftRole] = useState<Role>(role);
  const [draftDept, setDraftDept] = useState<Department>(homeDept);
  const [draftLocale, setDraftLocale] = useState<Lang>(userLocale);
  const [deptPickerOpen, setDeptPickerOpen] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setDraftUserId(userId);
    setDraftRole(role);
    setDraftDept(homeDept);
    setDraftLocale(userLocale);
  }, [userId, role, homeDept, userLocale]);

  function handleSave() {
    update({
      userId: draftUserId.trim() || userId,
      role: draftRole,
      homeDept: draftDept,
      locale: draftLocale,
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  const fieldClass =
    "w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-brand focus:ring-1 focus:ring-brand";

  const dirty =
    draftUserId.trim() !== userId ||
    draftRole !== role ||
    draftDept !== homeDept ||
    draftLocale !== userLocale;

  const deptMeta = DEPARTMENTS.find((d) => d.key === draftDept) ?? getDepartment(draftDept);
  const deptName = deptMeta ? departmentMetaLabel(deptMeta, locale) : draftDept;

  return (
    <Card>
      <h3 className="font-semibold text-slate-800 mb-1">{t("identity", locale)}</h3>
      <p className="text-sm text-slate-500 mb-4">{t("identityHint", locale)}</p>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label htmlFor="user-id" className="block text-sm font-medium text-slate-700 mb-1">
            {t("userId", locale)}
          </label>
          <input
            id="user-id"
            type="text"
            className={fieldClass}
            value={draftUserId}
            onChange={(e) => setDraftUserId(e.target.value)}
            autoComplete="username"
          />
        </div>

        <div>
          <label htmlFor="role" className="block text-sm font-medium text-slate-700 mb-1">
            {t("role", locale)}
          </label>
          <select
            id="role"
            className={fieldClass}
            value={draftRole}
            onChange={(e) => setDraftRole(e.target.value as Role)}
          >
            {ROLES.map((r) => (
              <option key={r} value={r}>
                {roleLabel(r, draftLocale)}
              </option>
            ))}
          </select>
        </div>

        <div>
          <span className="block text-sm font-medium text-slate-700 mb-2">
            {t("locale", locale)}
          </span>
          <div
            role="group"
            aria-label={t("locale", locale)}
            className="inline-flex items-center rounded-lg border border-border bg-surface-glass p-0.5"
          >
            {LANG_OPTIONS.map((opt) => {
              const active = draftLocale === opt.value;
              return (
                <button
                  key={opt.value}
                  type="button"
                  aria-pressed={active}
                  aria-label={opt.label}
                  onClick={() => setDraftLocale(opt.value)}
                  className={classNames(
                    "min-w-[2.5rem] rounded-md px-3 py-1.5 text-xs font-semibold tracking-wide transition-all duration-fast",
                    active
                      ? "bg-brand text-white shadow-sm"
                      : "text-content-secondary hover:bg-brand-light hover:text-content-primary",
                  )}
                >
                  {opt.short}
                </button>
              );
            })}
          </div>
        </div>

        <div className="sm:col-span-2">
          <span className="block text-sm font-medium text-slate-700 mb-2">
            {t("homeDept", locale)}
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setDeptPickerOpen(true)}
              className="inline-flex items-center gap-2 rounded-full border border-border bg-surface-glass px-3 py-1.5 text-sm font-medium text-content-primary transition-colors hover:border-border-strong hover:bg-surface"
              style={{ borderLeftColor: deptMeta?.accent_color, borderLeftWidth: 3 }}
            >
              <span
                className="h-2 w-2 flex-shrink-0 rounded-full"
                style={{ backgroundColor: deptMeta?.accent_color }}
                aria-hidden
              />
              {deptName}
            </button>
            <button
              type="button"
              onClick={() => setDeptPickerOpen(true)}
              className="text-xs text-brand hover:underline"
            >
              {t("change", locale)}
            </button>
          </div>
        </div>
      </div>

      <div className="mt-4 flex items-center gap-3">
        <Button onClick={handleSave} disabled={!dirty}>
          {t("save", locale)}
        </Button>
        {saved && (
          <span className="inline-flex items-center gap-1 text-sm text-emerald-600" role="status" aria-live="polite">
            <Check size="sm" />
            {t("saved", locale)}
          </span>
        )}
      </div>

      <DepartmentPickerModal
        open={deptPickerOpen}
        onClose={() => setDeptPickerOpen(false)}
        selected={[draftDept]}
        onChange={(depts) => {
          const newDept = depts.find((d) => d !== draftDept) ?? depts[0];
          if (newDept) {
            setDraftDept(newDept);
            setDeptPickerOpen(false);
          }
        }}
      />
    </Card>
  );
}
