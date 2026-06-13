import { Button } from "@/components/ui/Button";
import { useI18n } from "@/hooks/useI18n";
import { useTutorialContext } from "@/hooks/useTutorial";
import { classNames } from "@/lib/format";

function HelpIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      className="h-4 w-4"
      aria-hidden
    >
      <circle cx="12" cy="12" r="9" />
      <path d="M9.5 9.5a2.5 2.5 0 1 1 4.2 1.8c-.8.6-1.2 1.2-1.2 2.2" strokeLinecap="round" />
      <circle cx="12" cy="17" r="0.75" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function TutorialHelpButton() {
  const { t } = useI18n();
  const { startTutorial, isRunning } = useTutorialContext();

  return (
    <Button
      variant="ghost"
      data-tour="tutorial-help"
      aria-label={t("tutorialHelpAria")}
      title={t("tutorialHelpTitle")}
      className={classNames("gap-1.5", isRunning && "ring-2 ring-brand/40")}
      onClick={() => startTutorial(0)}
    >
      <HelpIcon />
      <span className="hidden sm:inline">{t("tutorialHelp")}</span>
    </Button>
  );
}
