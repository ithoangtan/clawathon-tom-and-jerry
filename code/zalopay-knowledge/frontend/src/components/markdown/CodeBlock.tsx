import { CopyButton } from "@/components/markdown/CopyButton";
import { displayLanguage, highlightCode, normalizeLanguage } from "@/components/markdown/lightHighlight";
import { t } from "@/lib/i18n";
import { useUserStore } from "@/store/userStore";
import { useMemo } from "react";

interface CodeBlockProps {
  code: string;
  language?: string;
}

export function CodeBlock({ code, language = "text" }: CodeBlockProps) {
  const locale = useUserStore((s) => s.locale);
  const lang = normalizeLanguage(language);
  const label = displayLanguage(language);

  const highlighted = useMemo(() => {
    if (lang === "text" || lang === "markdown" || lang === "yaml") {
      return null;
    }
    return highlightCode(code, lang);
  }, [code, lang]);

  return (
    <div className="code-block group my-4 overflow-hidden rounded-xl border border-slate-200/80 bg-[#f6f8fa] shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-200/80 bg-slate-100/80 px-3 py-1.5">
        <span className="text-xs font-medium text-slate-500">{label}</span>
        <CopyButton
          text={code}
          label={t("copyCode", locale)}
          className="opacity-70 group-hover:opacity-100"
        />
      </div>
      <div className="overflow-x-auto">
        {highlighted ? (
          <pre className="hljs !m-0 !rounded-none !border-0 !bg-transparent p-4 text-[13px] leading-relaxed">
            <code
              className={`language-${lang}`}
              dangerouslySetInnerHTML={{ __html: highlighted }}
            />
          </pre>
        ) : (
          <pre className="m-0 bg-transparent p-4 text-[13px] leading-relaxed">
            <code className="font-mono text-slate-800 whitespace-pre">{code}</code>
          </pre>
        )}
      </div>
    </div>
  );
}
