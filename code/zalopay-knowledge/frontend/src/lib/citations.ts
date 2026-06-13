import { sourceLabel, t } from "@/lib/i18n";
import type { Citation, Lang } from "@/lib/types";

const EXCERPT_MAX_CHARS = 400;

export function isCitationDeprecated(citation: Citation): boolean {
  return Boolean(citation.deprecated) || citation.lifecycle_state === "deprecated";
}

export function formatExcerpt(excerpt: string | null | undefined): string | null {
  if (!excerpt?.trim()) return null;
  const trimmed = excerpt.trim();
  if (trimmed.length <= EXCERPT_MAX_CHARS) return trimmed;
  return `${trimmed.slice(0, EXCERPT_MAX_CHARS).trimEnd()}…`;
}

export function openSourceLabel(sourceType: string | null | undefined, locale: Lang): string {
  if (sourceType === "confluence") return t("openInConfluence", locale);
  if (sourceType === "gdrive") return t("openInDrive", locale);
  return t("openInSource", locale);
}

export function lifecycleLabel(citation: Citation, locale: Lang): string {
  return isCitationDeprecated(citation)
    ? t("evidenceLifecycleDeprecated", locale)
    : t("evidenceLifecycleActive", locale);
}

export function lifecycleTone(citation: Citation): "success" | "warning" {
  return isCitationDeprecated(citation) ? "warning" : "success";
}

export function docTypeLabel(sourceType: string | null | undefined, locale: Lang): string {
  if (!sourceType) return t("evidenceDocTypeUnknown", locale);
  return sourceLabel(sourceType, locale);
}
