import { CopyButton } from "@/components/markdown/CopyButton";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";

interface MessageCopyButtonProps {
  text: string;
}

/** Copy the full assistant response to clipboard. */
export function MessageCopyButton({ text }: MessageCopyButtonProps) {
  const locale = useUserStore((s) => s.locale);

  return (
    <CopyButton
      text={text}
      label={t("copyMessage", locale)}
      size="md"
      className="text-slate-400 hover:text-slate-600"
    />
  );
}
