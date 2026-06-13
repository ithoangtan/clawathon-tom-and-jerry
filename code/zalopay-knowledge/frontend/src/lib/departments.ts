import type { Department, Lang } from "./types";

/** Mirror of app/common/departments.py — single source for UI labels & colors. */
export interface DepartmentMeta {
  key: Department;
  name_en: string;
  name_vi: string;
  accent_color: string;
  channel_hint: string;
  head_manager_en: string;
  head_manager_vi: string;
  description_en: string;
  description_vi: string;
}

export const DEPARTMENTS: DepartmentMeta[] = [
  {
    key: "risk",
    name_en: "Risk",
    name_vi: "Quản lý Rủi ro",
    accent_color: "#E63946",
    channel_hint: "teams-risk-knowledge",
    head_manager_en: "Lan Nguyen",
    head_manager_vi: "Nguyễn Thị Lan",
    description_en:
      "Risk controls, fraud monitoring, compliance policies, and incident escalation.",
    description_vi:
      "Kiểm soát rủi ro, giám sát gian lận, chính sách tuân thủ và leo thang sự cố.",
  },
  {
    key: "grow_enablement",
    name_en: "Grow Enablement",
    name_vi: "Phát triển Kinh doanh",
    accent_color: "#2A9D8F",
    channel_hint: "teams-grow-enablement-knowledge",
    head_manager_en: "Minh Tran",
    head_manager_vi: "Trần Văn Minh",
    description_en:
      "Merchant growth programs, onboarding playbooks, and enablement runbooks.",
    description_vi:
      "Chương trình phát triển merchant, playbook onboarding và runbook enablement.",
  },
  {
    key: "bank_partnerships",
    name_en: "Bank Partnerships",
    name_vi: "Đối tác Ngân hàng",
    accent_color: "#457B9D",
    channel_hint: "teams-bank-partnerships-knowledge",
    head_manager_en: "Hoang Le",
    head_manager_vi: "Lê Hoàng",
    description_en:
      "Bank integrations, settlement reconciliation, and partner SLA documentation.",
    description_vi:
      "Tích hợp ngân hàng, đối soát thanh toán và tài liệu SLA đối tác.",
  },
];

export const ROLES = ["engineer", "pm", "ops", "risk", "business"] as const;

export function getDepartment(key: Department): DepartmentMeta {
  const dept = DEPARTMENTS.find((d) => d.key === key);
  if (!dept) throw new Error(`Unknown department: ${key}`);
  return dept;
}

export function departmentLabel(key: Department, locale: Lang): string {
  const dept = getDepartment(key);
  return departmentMetaLabel(dept, locale);
}

export function departmentMetaLabel(dept: DepartmentMeta, locale: Lang): string {
  return locale === "vi" ? dept.name_vi : dept.name_en;
}

export function departmentHeadManager(dept: DepartmentMeta, locale: Lang): string {
  return locale === "vi" ? dept.head_manager_vi : dept.head_manager_en;
}

export function departmentDescription(dept: DepartmentMeta, locale: Lang): string {
  return locale === "vi" ? dept.description_vi : dept.description_en;
}

/** Truncate long descriptions for compact list rows. */
export function descriptionSnippet(text: string, maxLen = 96): string {
  const trimmed = text.trim();
  if (trimmed.length <= maxLen) return trimmed;
  return `${trimmed.slice(0, maxLen - 1).trimEnd()}…`;
}

/** Case-insensitive filter across name, head manager, and description. */
export function filterDepartments(
  departments: DepartmentMeta[],
  query: string,
  locale: Lang,
): DepartmentMeta[] {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return departments;

  return departments.filter((dept) => {
    const haystack = [
      departmentMetaLabel(dept, locale),
      departmentHeadManager(dept, locale),
      departmentDescription(dept, locale),
      dept.key.replace(/_/g, " "),
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(normalized);
  });
}

export function roleLabel(role: string, locale: Lang): string {
  const labels: Record<string, { en: string; vi: string }> = {
    engineer: { en: "Engineer", vi: "Kỹ sư" },
    pm: { en: "Product Manager", vi: "Quản lý Sản phẩm" },
    ops: { en: "Operations", vi: "Vận hành" },
    risk: { en: "Risk / Compliance", vi: "Rủi ro / Tuân thủ" },
    business: { en: "Business", vi: "Kinh doanh" },
  };
  const entry = labels[role] ?? { en: role, vi: role };
  return locale === "vi" ? entry.vi : entry.en;
}
