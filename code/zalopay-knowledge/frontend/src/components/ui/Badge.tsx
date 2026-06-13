import { classNames } from "@/lib/format";
import type { HTMLAttributes } from "react";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: "default" | "success" | "warning" | "danger" | "info";
}

const tones: Record<NonNullable<BadgeProps["tone"]>, string> = {
  default: "bg-white/10 text-content-secondary border border-border",
  success: "bg-success-muted text-success border border-success/20",
  warning: "bg-warning-muted text-warning border border-warning/20",
  danger: "bg-danger-muted text-danger border border-danger/20",
  info: "bg-brand-light text-brand border border-brand/20",
};

export function Badge({ tone = "default", className, children, ...props }: BadgeProps) {
  return (
    <span
      className={classNames(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        tones[tone],
        className,
      )}
      data-tone={tone}
      {...props}
    >
      {children}
    </span>
  );
}
