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
import type { Citation, Department } from "@/lib/types";
import { useCallback, useEffect, useState } from "react";
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

  const indexReady = health?.index_ready ?? false;
  const examples = locale === "vi" ? EXAMPLE_QUESTIONS.vi : EXAMPLE_QUESTIONS.en;
  const isEmpty = messages.length === 0 && !loading;

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
      <div className="dept-target-bar relative z-30 flex-shrink-0 overflow-visible border-b border-slate-200/60 chat-glass px-4 py-2.5">
        <div className="mx-auto max-w-3xl">
          <DepartmentTargetBar
            selected={targetDepartments}
            autoRoute={targetAutoRoute}
            onChange={setTargetDepartments}
            onAutoRouteChange={setTargetAutoRoute}
          />
          {!indexReady && (
            <p className="mt-2 text-xs text-amber-700" role="status">
              {indexNotReadyMessage(locale, targetAutoRoute, targetDepartments)}{" "}
              <Link to="/admin" className="font-medium text-brand underline-offset-2 hover:underline">
                {t("indexNotReadyAdminLink", locale)}
              </Link>
            </p>
          )}
        </div>
      </div>

      <div
        ref={scrollRef}
        className="chat-scroll relative z-10 flex-1 overflow-y-auto overscroll-contain"
        role="log"
        aria-live="polite"
        aria-relevant="additions"
        aria-label={t("navChat", locale)}
      >
        <div className="mx-auto max-w-3xl px-4 py-6">
          {isEmpty && (
            <ChatEmptyState examples={examples} onExampleClick={handleExampleClick} />
          )}

          {messages.length > 0 && (
            <div className="space-y-8">
              {messages.map((msg) =>
                msg.role === "user" ? (
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
                    onClarifySelect={handleClarify}
                    onCitationClick={(index) => openCitation(msg.response!.citations, index)}
                  />
                ) : null,
              )}

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
          )}

          <div className="h-4" aria-hidden />
        </div>
      </div>

      <div className="relative z-10 flex-shrink-0 border-t border-slate-200/60 chat-glass px-4 pb-4 pt-3">
        <div className="mx-auto max-w-3xl">
          <ChatInput
            value={input}
            onChange={setInput}
            onSubmit={() => sendMessage(input)}
            loading={loading}
            disabled={!indexReady}
          />
        </div>
      </div>
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
