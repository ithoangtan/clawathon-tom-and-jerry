import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Check } from "@/components/ui/icons";
import { DepartmentSearchList } from "@/components/departments/DepartmentSearchList";
import { DEPARTMENTS, ROLES, roleLabel } from "@/lib/departments";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import type { Department, Lang, Role } from "@/lib/types";
import { useEffect, useState } from "react";

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

        <div className="sm:col-span-2">
          <span className="block text-sm font-medium text-slate-700 mb-1">
            {t("homeDept", locale)}
          </span>
          <DepartmentSearchList
            selected={[draftDept]}
            onChange={(depts) => {
              if (depts[0]) setDraftDept(depts[0]);
            }}
            multiple={false}
            departments={DEPARTMENTS}
            maxListHeightClass="max-h-44"
          />
        </div>

        <div>
          <label htmlFor="locale" className="block text-sm font-medium text-slate-700 mb-1">
            {t("locale", locale)}
          </label>
          <select
            id="locale"
            className={fieldClass}
            value={draftLocale}
            onChange={(e) => setDraftLocale(e.target.value as Lang)}
          >
            <option value="en">{t("langEn", draftLocale)}</option>
            <option value="vi">{t("langVi", draftLocale)}</option>
          </select>
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
    </Card>
  );
}
