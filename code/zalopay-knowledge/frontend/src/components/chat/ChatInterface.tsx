import { AssistantMessage } from "@/components/chat/AssistantMessage";
import {
  CitationEvidenceInspector,
  type CitationInspectorState,
} from "@/components/chat/CitationEvidenceInspector";
import { ChatEmptyState } from "@/components/chat/ChatEmptyState";
import { ChatInput } from "@/components/chat/ChatInput";
import { DepartmentTargetBar } from "@/components/chat/DepartmentTargetBar";
import { PipelineProgress } from "@/components/chat/PipelineProgress";
import { UserMessage } from "@/components/chat/UserMessage";
import { ErrorState } from "@/components/ui/StateViews";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import { t, indexNotReadyMessage } from "@/lib/i18n";
import { classNames } from "@/lib/format";
import { useChat } from "@/hooks/useChat";
import { useHealth } from "@/hooks/useHealth";
import { useSmoothScroll } from "@/hooks/useSmoothScroll";
import { useUserStore } from "@/store/userStore";
import { useMockStore } from "@/store/mockStore";
import type { Citation, Department } from "@/lib/types";
import { useTutorialContext } from "@/hooks/useTutorial";
import { useTutorialStore } from "@/store/tutorialStore";
import { useCallback, useEffect, useRef, useState } from "react";

const IS_DEV = import.meta.env.DEV || window.location.hostname === "localhost";
import { Link } from "react-router-dom";

const EXAMPLE_QUESTIONS = {
  en: [
    "What is the escalation process when a fraud alert triggers on a high-value merchant transaction?",
    "Walk me through the settlement reconciliation steps with a partner bank after a failed batch.",
    "What KYC re-verification is required when a merchant's transaction volume doubles?",
  ],
  vi: [
    "Quy trình leo thang khi cảnh báo gian lận kích hoạt trên giao dịch merchant giá trị cao là gì?",
    "Các bước đối soát thanh toán với ngân hàng đối tác khi một batch thất bại diễn ra như thế nào?",
    "Cần xác minh lại KYC như thế nào khi khối lượng giao dịch của merchant tăng gấp đôi?",
  ],
};

export function ChatInterface() {
  const locale = useUserStore((s) => s.locale);
  const { health } = useHealth();
  const {
    messages,
    input,
    setInput,
    targetDepartments,
    setTargetDepartments,
    targetAutoRoute,
    setTargetAutoRoute,
    loading,
    streamingStatus,
    pipelineProgress,
    dismissPipelineSummary,
    error,
    sendMessage,
    retryLast,
  } = useChat();

  const scrollRef = useSmoothScroll([messages, loading, streamingStatus, pipelineProgress]);

  const { startTutorial, isRunning } = useTutorialContext();
  const responseDismissed = useTutorialStore((s) => s.dismissed["response"] ?? false);
  const hasHydrated = useTutorialStore((s) => s.hasHydrated);
  const autoStartedResponseRef = useRef(false);

  useEffect(() => {
    const hasCompletedResponse = messages.some(
      (m) => m.role === "assistant" && m.response && !m.streaming,
    );
    if (
      hasCompletedResponse &&
      hasHydrated &&
      !responseDismissed &&
      !autoStartedResponseRef.current &&
      !isRunning
    ) {
      autoStartedResponseRef.current = true;
      const timer = window.setTimeout(() => startTutorial("response", 0), 1500);
      return () => window.clearTimeout(timer);
    }
  }, [messages, hasHydrated, responseDismissed, isRunning, startTutorial]);

  const isDesktop = useMediaQuery("(min-width: 768px)");
  const [inspector, setInspector] = useState<CitationInspectorState | null>(null);

  const closeInspector = useCallback(() => setInspector(null), []);

  const openCitation = useCallback((citations: Citation[], index: number) => {
    setInspector({ citations, selectedIndex: index });
  }, []);

  useEffect(() => {
    if (!inspector) return;
    const activeInspector = inspector;

    function onKeyDown(e: KeyboardEvent) {
      const target = e.target;
      if (
        target instanceof HTMLElement &&
        (target.tagName === "INPUT" ||
          target.tagName === "TEXTAREA" ||
          target.isContentEditable)
      ) {
        return;
      }

      if (e.key === "Escape") {
        e.preventDefault();
        closeInspector();
        return;
      }

      if (/^[1-9]$/.test(e.key)) {
        const idx = parseInt(e.key, 10);
        if (idx <= activeInspector.citations.length) {
          e.preventDefault();
          setInspector((prev) => (prev ? { ...prev, selectedIndex: idx } : null));
        }
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [inspector, closeInspector]);

  useEffect(() => {
    if (!inspector || isDesktop) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [inspector, isDesktop]);

  const chatScenario = useMockStore((s) => s.chatScenario);
  const indexReady = (IS_DEV && chatScenario !== null) || (health?.index_ready ?? false);
  const examples = locale === "vi" ? EXAMPLE_QUESTIONS.vi : EXAMPLE_QUESTIONS.en;
  const isEmpty = messages.length === 0 && !loading;

  const departmentBar = (
    <DepartmentTargetBar
      selected={targetDepartments}
      autoRoute={targetAutoRoute}
      onChange={setTargetDepartments}
      onAutoRouteChange={setTargetAutoRoute}
      compact
    />
  );

  const indexWarning = !indexReady ? (
    <p className="text-xs text-amber-700" role="status">
      {indexNotReadyMessage(locale, targetAutoRoute, targetDepartments)}{" "}
      <Link to="/admin" className="font-medium text-brand underline-offset-2 hover:underline">
        {t("indexNotReadyAdminLink", locale)}
      </Link>
    </p>
  ) : null;

  function renderComposer(variant: "default" | "hero" = "default") {
    return (
      <div className="chat-composer mx-auto w-full max-w-3xl space-y-2">
        <ChatInput
          variant={variant}
          value={input}
          onChange={setInput}
          onSubmit={() => sendMessage(input)}
          loading={loading}
          disabled={!indexReady}
        />
        {departmentBar}
        {indexWarning}
      </div>
    );
  }

  function handleClarify(dept: Department) {
    setTargetAutoRoute(false);
    setTargetDepartments([dept]);
    const lastUser = [...messages].reverse().find((m) => m.role === "user");
    if (lastUser) {
      sendMessage(lastUser.content, [dept]);
    }
  }

  function handleExampleClick(question: string) {
    setInput(question);
    sendMessage(question);
  }

  function handleSuggestedSelect(question: string) {
    setInput(question);
    sendMessage(question);
  }

  function mapError(err: string): string {
    if (err.includes("timeout") || err.includes("408")) return t("errorTimeout", locale);
    if (err.includes("not ready") || err.includes("503")) return t("errorKbNotReady", locale);
    return err;
  }

  return (
    <div className="chat-shell flex h-full min-h-0">
      <div
        className={classNames(
          "flex min-h-0 flex-col",
          inspector && isDesktop ? "w-[60%] flex-shrink-0" : "w-full flex-1",
        )}
      >
      {isEmpty ? (
        <div className="chat-top-clearance relative z-10 flex flex-1 flex-col px-4 pb-8">
          <div className="flex flex-1 flex-col items-center justify-center">
            <ChatEmptyState
              examples={examples}
              onExampleClick={handleExampleClick}
              belowInput={
                <>
                  {departmentBar}
                  {indexWarning}
                </>
              }
            >
              <ChatInput
                variant="hero"
                value={input}
                onChange={setInput}
                onSubmit={() => sendMessage(input)}
                loading={loading}
                disabled={!indexReady}
              />
            </ChatEmptyState>
          </div>
        </div>
      ) : (
        <>
          <div
            ref={scrollRef}
            className="chat-scroll chat-top-clearance relative z-10 flex-1 overflow-y-auto overscroll-contain"
            role="log"
            aria-live="polite"
            aria-relevant="additions"
            aria-label={t("navChat", locale)}
          >
            <div className="mx-auto max-w-3xl px-4 py-6">
              <div className="space-y-8">
                {messages.map((msg, idx) => {
                  const isLastAssistant =
                    msg.role === "assistant" &&
                    !messages.slice(idx + 1).some((m) => m.role === "assistant");
                  return msg.role === "user" ? (
                    <UserMessage
                      key={msg.id}
                      content={msg.content}
                      timestamp={msg.timestamp}
                    />
                  ) : msg.response ? (
                    <AssistantMessage
                      key={msg.id}
                      response={msg.response}
                      timestamp={msg.timestamp}
                      streaming={msg.streaming}
                      isLast={isLastAssistant}
                      onClarifySelect={handleClarify}
                      onCitationClick={(index) => openCitation(msg.response!.citations, index)}
                      onSuggestedSelect={handleSuggestedSelect}
                    />
                  ) : null;
                })}

                {(loading || pipelineProgress?.phase === "collapsed") && pipelineProgress && (
                  <PipelineProgress
                    progress={pipelineProgress}
                    onCollapsedDismiss={dismissPipelineSummary}
                  />
                )}

                {error && (
                  <ErrorState message={mapError(error)} onRetry={retryLast} />
                )}
              </div>

              <div className="h-4" aria-hidden />
            </div>
          </div>

          <div className="chat-input-dock relative z-10 flex-shrink-0 px-4 pb-4 pt-2">
            {renderComposer()}
          </div>
        </>
      )}
      </div>

      {inspector && (
        <CitationEvidenceInspector
          state={inspector}
          open
          variant={isDesktop ? "panel" : "sheet"}
          onClose={closeInspector}
          onSelectIndex={(index) =>
            setInspector((prev) => (prev ? { ...prev, selectedIndex: index } : null))
          }
        />
      )}
    </div>
  );
}
