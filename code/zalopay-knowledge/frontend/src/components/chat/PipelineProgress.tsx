import { useEffect, useRef, useState } from "react";
import { DepartmentChip } from "@/components/chat/Badges";
import { ChatAvatar } from "@/components/chat/ChatAvatar";
import { Check, Loader2 } from "@/components/ui/icons";
import { classNames, formatMs } from "@/lib/format";
import {
  gsap,
  REDUCED_MOTION_QUERY,
  runMessageEnter,
  runStaggerEnter,
  runThinkingGlow,
  useGSAP,
} from "@/lib/gsap";
import { t } from "@/lib/i18n";
import {
  formatPipelineElapsed,
  PIPELINE_STEP_ORDER,
  STEP_I18N_KEY,
  stepElapsedMs,
  type PipelineProgressState,
  type PipelineStepState,
  type StepStatus,
} from "@/lib/pipelineSteps";
import { useUserStore } from "@/store/userStore";
import type { Lang } from "@/lib/types";

interface PipelineProgressProps {
  progress: PipelineProgressState;
  onCollapsedDismiss?: () => void;
}

function StepIcon({ status }: { status: StepStatus }) {
  if (status === "done") {
    return (
      <span className="pipeline-step-icon pipeline-step-icon--done" aria-hidden>
        <Check size="sm" className="text-white" strokeWidth={2.5} />
      </span>
    );
  }
  if (status === "active") {
    return (
      <span className="pipeline-step-icon pipeline-step-icon--active" aria-hidden>
        <Loader2 size="sm" className="text-brand" />
      </span>
    );
  }
  return <span className="pipeline-step-icon pipeline-step-icon--pending" aria-hidden />;
}

function StepTimer({ step, now }: { step: PipelineStepState; now: number }) {
  const elapsed = stepElapsedMs(step, now);
  if (elapsed == null || step.status === "pending") return null;

  return (
    <span className="pipeline-step-timer tabular-nums" aria-hidden>
      {formatMs(elapsed)}
    </span>
  );
}

function stepLabel(step: PipelineStepState, locale: Lang): string {
  if (step.label) return step.label;
  return t(STEP_I18N_KEY[step.id] as Parameters<typeof t>[0], locale);
}

function PipelineStepRow({
  step,
  progress,
  locale,
  now,
  isLast,
}: {
  step: PipelineStepState;
  progress: PipelineProgressState;
  locale: Lang;
  now: number;
  isLast: boolean;
}) {
  const showDeptBranches =
    progress.departments.length > 0 &&
    (step.id === "retrieval" ||
      (progress.usesPipelineEvents &&
        (step.id === "grade" || step.id === "verify" || step.id === "synthesis") &&
        step.status !== "pending"));

  return (
    <li
      className={classNames(
        "pipeline-step",
        step.status === "active" && "pipeline-step--active",
        step.status === "done" && "pipeline-step--done",
      )}
      data-step={step.id}
      data-status={step.status}
    >
      <div className="pipeline-step-row">
        <StepIcon status={step.status} />
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <span
              className={classNames(
                "pipeline-step-label",
                step.status === "active" && "text-content-primary",
                step.status === "pending" && "text-content-muted",
              )}
            >
              {stepLabel(step, locale)}
            </span>
            <StepTimer step={step} now={now} />
          </div>

          {showDeptBranches && (
            <div
              className="pipeline-dept-branches"
              role="list"
              aria-label={t("pipelineDeptBranches", locale)}
            >
              {progress.departments.map((dept) => {
                const branch = progress.deptBranches[dept];
                const branchStatus = branch?.status ?? "pending";
                return (
                  <span
                    key={dept}
                    role="listitem"
                    className={classNames(
                      "pipeline-dept-chip",
                      branchStatus === "active" && "pipeline-dept-chip--active",
                      branchStatus === "done" && "pipeline-dept-chip--done",
                    )}
                    data-dept={dept}
                    data-status={branchStatus}
                  >
                    <DepartmentChip deptKey={dept} />
                  </span>
                );
              })}
            </div>
          )}
        </div>
      </div>
      {!isLast && <span className="pipeline-step-connector" aria-hidden />}
    </li>
  );
}

export function PipelineProgress({ progress, onCollapsedDismiss }: PipelineProgressProps) {
  const locale = useUserStore((s) => s.locale);
  const rowRef = useRef<HTMLDivElement>(null);
  const avatarWrapRef = useRef<HTMLDivElement>(null);
  const stepperRef = useRef<HTMLOListElement>(null);
  const [now, setNow] = useState(() => Date.now());
  const collapsed = progress.phase === "collapsed";

  useEffect(() => {
    if (progress.phase !== "running") return;
    const id = window.setInterval(() => setNow(Date.now()), 250);
    return () => window.clearInterval(id);
  }, [progress.phase]);

  useEffect(() => {
    if (!collapsed || !onCollapsedDismiss) return;
    const id = window.setTimeout(onCollapsedDismiss, 2800);
    return () => window.clearTimeout(id);
  }, [collapsed, onCollapsedDismiss]);

  useGSAP(
    () => {
      const row = rowRef.current;
      const avatarWrap = avatarWrapRef.current;
      const stepper = stepperRef.current;
      if (!row) return;

      const cleanups: Array<() => void> = [runMessageEnter(row, "assistant")];

      if (!collapsed && avatarWrap) {
        cleanups.push(runThinkingGlow(avatarWrap));
      }

      const mm = gsap.matchMedia();
      mm.add({ reduceMotion: REDUCED_MOTION_QUERY }, (context) => {
        if (context.conditions?.reduceMotion || collapsed || !stepper) return;
        const stepEls = stepper.querySelectorAll(".pipeline-step");
        if (stepEls.length > 0) {
          cleanups.push(runStaggerEnter(stepEls));
        }
      });

      return () => {
        cleanups.forEach((fn) => fn());
        mm.revert();
      };
    },
    { scope: rowRef, dependencies: [collapsed, progress.steps.map((s) => s.status).join("|")] },
  );

  const totalSeconds =
    progress.totalElapsedMs != null
      ? progress.totalElapsedMs / 1000
      : (now - progress.startedAt) / 1000;

  const deptCount = Math.max(progress.departmentCount, progress.departments.length);

  return (
    <div ref={rowRef} className="flex gap-3" role="status" aria-live="polite">
      <div ref={avatarWrapRef} className="rounded-full">
        <ChatAvatar role="assistant" className="avatar-assistant-glow" />
      </div>

      <div className="min-w-0 flex-1">
        <span className="text-xs font-medium text-content-secondary">
          {collapsed ? t("pipelineComplete", locale) : t("assistantName", locale)}
        </span>

        {collapsed ? (
          <p className="pipeline-collapsed-summary mt-1.5">
            {t("pipelineProcessedSummary", locale, {
              seconds: formatPipelineElapsed(totalSeconds),
              count: deptCount,
            })}
          </p>
        ) : (
          <div className="pipeline-shell mt-1.5">
            <span className="sr-only">{t("sending", locale)}</span>
            <ol ref={stepperRef} className="pipeline-stepper">
              {PIPELINE_STEP_ORDER.map((id, index) => {
                const step = progress.steps.find((s) => s.id === id);
                if (!step) return null;
                return (
                  <PipelineStepRow
                    key={id}
                    step={step}
                    progress={progress}
                    locale={locale}
                    now={now}
                    isLast={index === PIPELINE_STEP_ORDER.length - 1}
                  />
                );
              })}
            </ol>
          </div>
        )}
      </div>
    </div>
  );
}

/** @deprecated Use PipelineProgress — kept for tests importing the old name. */
export function TypingIndicator() {
  return null;
}
