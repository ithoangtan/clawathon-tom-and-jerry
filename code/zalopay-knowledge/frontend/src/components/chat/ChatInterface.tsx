import { AssistantMessage } from "@/components/chat/AssistantMessage";
import {
  CitationEvidenceInspector,
  type CitationInspectorState,
} from "@/components/chat/CitationEvidenceInspector";
import { ChatAvatar } from "@/components/chat/ChatAvatar";
import { ChatEmptyState } from "@/components/chat/ChatEmptyState";
import { ChatInput } from "@/components/chat/ChatInput";
import { DepartmentTargetBar } from "@/components/chat/DepartmentTargetBar";
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
import { api } from "@/lib/apiClient";
import { useCallback, useEffect, useRef, useState } from "react";

const IS_DEV = import.meta.env.DEV || window.location.hostname === "localhost";
import { Link } from "react-router-dom";

const EXAMPLE_QUESTIONS = {
  en: [
    "What fraud detection models does Zalopay use in its e-wallet ecosystem?",
    "How does the Lucky Wheel campaign work and what are its v2 configuration steps?",
    "What are the commercial terms and revenue sharing models for bank partnerships?",
  ],
  vi: [
    "Mô hình phát hiện gian lận trong hệ sinh thái ví điện tử của Zalopay hoạt động như thế nào?",
    "Các bước cấu hình và vận hành chiến dịch Lucky Wheel v2 là gì?",
    "Điều khoản thương mại và mô hình chia sẻ doanh thu trong quan hệ đối tác ngân hàng gồm những gì?",
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
    error,
    sendMessage,
    retryLast,
  } = useChat();

  const sessionId = useUserStore((s) => s.sessionId);
  const scrollRef = useSmoothScroll([messages, loading]);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom on session switch and when webhook messages arrive.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [sessionId]);

  useEffect(() => {
    if (messages.length > 0) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.length]);

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
  const fallbackExamples = locale === "vi" ? EXAMPLE_QUESTIONS.vi : EXAMPLE_QUESTIONS.en;
  const [examples, setExamples] = useState<string[]>(fallbackExamples);

  useEffect(() => {
    api.suggestedQuestions(locale).then((data) => {
      if (data.questions.length > 0) {
        setExamples(data.questions);
      }
    }).catch(() => { /* keep fallback */ });
  }, [locale]);

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

                {loading && (
                  <div className="flex gap-3" role="status" aria-live="polite">
                    <ChatAvatar role="assistant" className="avatar-assistant-glow" />
                    <div className="min-w-0 flex-1">
                      <span className="text-xs font-medium text-content-secondary">
                        {t("assistantName", locale)}
                      </span>
                      <p className="mt-1.5 text-sm text-content-muted">{t("sending", locale)}</p>
                    </div>
                  </div>
                )}

                {error && (
                  <ErrorState message={mapError(error)} onRetry={retryLast} />
                )}
              </div>

              <div ref={bottomRef} className="h-4" aria-hidden />
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
