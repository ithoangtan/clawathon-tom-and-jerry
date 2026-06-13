import { classNames } from "@/lib/format";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";

type AvatarRole = "user" | "assistant";

interface ChatAvatarProps {
  role: AvatarRole;
  className?: string;
}

export function ChatAvatar({ role, className }: ChatAvatarProps) {
  const locale = useUserStore((s) => s.locale);
  const isAssistant = role === "assistant";

  return (
    <div
      className={classNames(
        "flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full text-xs font-semibold",
        isAssistant
          ? "bg-brand text-white shadow-sm"
          : "bg-slate-200 text-slate-600",
        className,
      )}
      aria-hidden
    >
      {isAssistant ? (
        <span>ZP</span>
      ) : (
        <span aria-label={t("you", locale)}>U</span>
      )}
    </div>
  );
}
