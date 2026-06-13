import type { Lang } from "./types";

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatMs(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(1)} s`;
}

export function formatConfidence(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function formatMessageTime(iso: string, locale: Lang): string {
  try {
    return new Intl.DateTimeFormat(locale === "vi" ? "vi-VN" : "en-US", {
      hour: "numeric",
      minute: "2-digit",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function formatDate(iso: string | null | undefined, locale: Lang): string {
  if (!iso) return "—";
  try {
    return new Intl.DateTimeFormat(locale === "vi" ? "vi-VN" : "en-US", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function formatFreshnessHours(hours: number | null | undefined): string {
  if (hours == null) return "—";
  if (hours < 1) return "< 1h ago";
  if (hours < 24) return `${Math.round(hours)}h ago`;
  const days = Math.round(hours / 24);
  return `${days}d ago`;
}

export function freshnessLevel(
  lastSuccess: string | null | undefined,
  freshnessHours: number | null | undefined,
): "green" | "amber" | "red" {
  if (!lastSuccess) return "red";
  if (freshnessHours != null && freshnessHours <= 24) return "green";
  return "amber";
}

export function generateSessionId(): string {
  return `sess-${crypto.randomUUID()}`;
}

export function generateUserId(): string {
  return `user-${crypto.randomUUID().slice(0, 8)}`;
}

export function classNames(...parts: (string | false | null | undefined)[]): string {
  return parts.filter(Boolean).join(" ");
}
