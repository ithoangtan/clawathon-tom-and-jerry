import { AssistantMessage } from "@/components/chat/AssistantMessage";
import { ChatEmptyState } from "@/components/chat/ChatEmptyState";
import { ChatInput } from "@/components/chat/ChatInput";
import { DepartmentTargetBar } from "@/components/chat/DepartmentTargetBar";
import { TypingIndicator } from "@/components/chat/TypingIndicator";
import { UserMessage } from "@/components/chat/UserMessage";
import { ErrorState } from "@/components/ui/StateViews";
import { t } from "@/lib/i18n";
import { useChat } from "@/hooks/useChat";
import { useHealth } from "@/hooks/useHealth";
import { useSmoothScroll } from "@/hooks/useSmoothScroll";
import { useUserStore } from "@/store/userStore";
import type { Department } from "@/lib/types";

const EXAMPLE_QUESTIONS = {
  en: [
    "How does settlement reconciliation work with partner banks?",
    "What is the escalation process for risk alerts?",
    "What are the KYC re-verification thresholds?",
  ],
  vi: [
    "Quy trình đối soát thanh toán với ngân hàng đối tác như thế nào?",
    "Quy trình leo thang cảnh báo rủi ro là gì?",
    "Ngưỡng xác minh lại KYC là bao nhiêu?",
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
    loading,
    streamingStatus,
    error,
    sendMessage,
    retryLast,
  } = useChat();

  const scrollRef = useSmoothScroll([messages, loading, streamingStatus]);

  const indexReady = health?.index_ready ?? false;
  const examples = locale === "vi" ? EXAMPLE_QUESTIONS.vi : EXAMPLE_QUESTIONS.en;
  const isEmpty = messages.length === 0 && !loading;

  function handleClarify(dept: Department) {
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
    <div className="chat-shell flex h-full min-h-0 flex-col">
      <div className="relative z-10 flex-shrink-0 border-b border-slate-200/60 chat-glass px-4 py-2.5">
        <div className="mx-auto max-w-3xl">
          <DepartmentTargetBar
            selected={targetDepartments}
            onChange={setTargetDepartments}
          />
          {!indexReady && (
            <p className="mt-2 text-xs text-amber-700" role="status">
              {t("indexNotReady", locale)}
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
                  />
                ) : null,
              )}

              {loading && <TypingIndicator statusText={streamingStatus} />}

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
  );
}
