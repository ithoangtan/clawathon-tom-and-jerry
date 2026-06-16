import { useEffect, useMemo, useRef, useState } from "react";
import { DepartmentChip } from "@/components/chat/Badges";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { ArrowRight, ChevronLeft, History, Menu, Plus, Search, Trash2, X } from "@/components/ui/icons";
import { useFocusTrap } from "@/hooks/useFocusTrap";
import { classNames, formatDate, generateSessionId } from "@/lib/format";
import { t } from "@/lib/i18n";
import {
  matchesSearch,
  sortThreads,
  threadDepartments,
  threadStatus,
  threadTitle,
  type ThreadStatus,
} from "@/lib/sessionThread";
import { useSessionStore } from "@/store/sessionStore";
import { useSidebarStore } from "@/store/sidebarStore";
import { useUserStore } from "@/store/userStore";
import { useNavigate } from "react-router-dom";

function statusLabel(status: ThreadStatus, locale: "en" | "vi"): string {
  switch (status) {
    case "answered":
      return t("statusAnswered", locale);
    case "refused":
      return t("statusRefused", locale);
    case "conflict":
      return t("statusConflict", locale);
    default:
      return t("statusPending", locale);
  }
}

function statusTone(status: ThreadStatus): "success" | "danger" | "warning" | "default" {
  switch (status) {
    case "answered":
      return "success";
    case "refused":
      return "danger";
    case "conflict":
      return "warning";
    default:
      return "default";
  }
}

interface SessionSidebarPanelProps {
  onCloseMobile?: () => void;
  onCloseDesktop?: () => void;
}

export function SessionSidebarPanel({ onCloseMobile, onCloseDesktop }: SessionSidebarPanelProps) {
  const locale = useUserStore((s) => s.locale);
  const activeSessionId = useUserStore((s) => s.sessionId);
  const threadsRecord = useSessionStore((s) => s.threads);
  const threadsLoaded = useSessionStore((s) => s.loaded);
  const deleteThread = useSessionStore((s) => s.deleteThread);
  const setSessionId = useUserStore((s) => s.setSessionId);
  const startPolling = useSessionStore((s) => s.startPolling);
  const stopPolling = useSessionStore((s) => s.stopPolling);
  const navigate = useNavigate();

  // Start polling whenever a processing session is present; stop when all done.
  useEffect(() => {
    const hasProcessing = Object.values(threadsRecord).some(
      (t) => t.processingStatus === "processing",
    );
    if (hasProcessing) {
      startPolling();
    } else {
      stopPolling();
    }
  }, [threadsRecord, startPolling, stopPolling]);

  const [query, setQuery] = useState("");
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);

  const filtered = useMemo(() => {
    const threads = sortThreads(Object.values(threadsRecord));
    return threads.filter((thread) => matchesSearch(thread, query));
  }, [threadsRecord, query]);

  function handleSelect(sessionId: string) {
    if (sessionId === activeSessionId) {
      onCloseMobile?.();
      return;
    }
    navigate(`/chat/${sessionId}`, { preventScrollReset: true });
    onCloseMobile?.();
  }

  function handleDelete(sessionId: string) {
    deleteThread(sessionId);
    setPendingDeleteId(null);
    if (sessionId === activeSessionId) {
      // Bypass Effect 3 (skip save — we just deleted this session).
      const newId = generateSessionId();
      setSessionId(newId);
      navigate(`/chat/${newId}`);
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-start justify-between gap-2 border-b border-border px-3 py-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <History size="sm" className="text-brand" />
            <h2 className="text-sm font-semibold text-content-primary">
              {t("sessionHistory", locale)}
            </h2>
          </div>
          <p className="mt-1 text-xs text-content-secondary">
            {t("sessionHistoryHint", locale)}
          </p>
        </div>
        {(onCloseMobile || onCloseDesktop) && (
          <Button
            variant="ghost"
            className="!px-2 !py-2"
            onClick={onCloseMobile ?? onCloseDesktop}
            aria-label={t("closeSessionHistory", locale)}
          >
            {onCloseMobile ? <X size="sm" /> : <ChevronLeft size="sm" />}
          </Button>
        )}
      </div>

      <div className="flex-shrink-0 space-y-2 border-b border-border px-3 py-3">
        <Button
          variant="secondary"
          className="w-full justify-start"
          onClick={() => {
            navigate(`/chat/${generateSessionId()}`);
            onCloseMobile?.();
          }}
        >
          <Plus size="sm" />
          {t("newSession", locale)}
        </Button>

        <label className="relative block">
          <span className="sr-only">{t("searchSessions", locale)}</span>
          <Search
            size="sm"
            className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-content-muted"
          />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={t("searchSessions", locale)}
            className="w-full rounded-lg border border-border bg-surface-glass py-2 pl-8 pr-3 text-sm text-content-primary placeholder:text-content-muted focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20"
          />
        </label>
      </div>

      <div
        className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-2 py-2"
        role="list"
        aria-label={t("sessionHistory", locale)}
      >
        {!threadsLoaded ? (
          <p className="px-2 py-6 text-center text-xs text-content-secondary" role="status">
            {locale === "vi" ? "Đang tải…" : "Loading…"}
          </p>
        ) : filtered.length === 0 ? (
          <p className="px-2 py-6 text-center text-xs text-content-secondary" role="status">
            {t("noSessions", locale)}
          </p>
        ) : (
          <ul className="space-y-1">
            {filtered.map((thread) => {
              const title = threadTitle(thread);
              const status = threadStatus(thread);
              const departments = threadDepartments(thread);
              const isActive = thread.sessionId === activeSessionId;
              const isConfirmingDelete = pendingDeleteId === thread.sessionId;
              const isProcessing = thread.processingStatus === "processing";
              const isError = thread.processingStatus === "error";

              return (
                <li key={thread.sessionId} role="listitem">
                  {isConfirmingDelete ? (
                    <div className="rounded-lg border border-danger/30 bg-danger/5 p-3">
                      <p className="text-xs text-content-primary">
                        {t("deleteSessionConfirm", locale)}
                      </p>
                      <div className="mt-2 flex gap-2">
                        <Button
                          variant="danger"
                          className="!px-2 !py-1 text-xs"
                          onClick={() => handleDelete(thread.sessionId)}
                        >
                          {t("confirm", locale)}
                        </Button>
                        <Button
                          variant="ghost"
                          className="!px-2 !py-1 text-xs"
                          onClick={() => setPendingDeleteId(null)}
                        >
                          {t("cancel", locale)}
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div
                      className={classNames(
                        "group relative rounded-lg border transition-colors",
                        isActive
                          ? "border-brand/40 bg-brand-light shadow-sm"
                          : isProcessing
                            ? "border-warning/40 bg-warning/5 animate-pulse"
                            : "border-transparent hover:border-border hover:bg-surface-glass",
                      )}
                    >
                      <button
                        type="button"
                        onClick={() => handleSelect(thread.sessionId)}
                        className="w-full px-3 py-2.5 text-left"
                        aria-current={isActive ? "true" : undefined}
                      >
                        <p className="line-clamp-2 text-sm font-medium text-content-primary">
                          {title ?? t("noHistory", locale)}
                        </p>
                        {thread.workflowId && (
                          <p className="mt-0.5 text-[10px] text-content-muted font-mono truncate">
                            {thread.jiraKey ?? thread.workflowId}
                          </p>
                        )}
                        <p className="mt-1 text-[11px] text-content-muted">
                          {formatDate(thread.updatedAt, locale)}
                        </p>
                        <div className="mt-2 flex flex-wrap items-center gap-1.5">
                          {isProcessing ? (
                            <Badge tone="warning" className="!text-[10px]">
                              {locale === "vi" ? "Đang xử lý…" : "Processing…"}
                            </Badge>
                          ) : isError ? (
                            <Badge tone="danger" className="!text-[10px]">
                              {locale === "vi" ? "Lỗi" : "Error"}
                            </Badge>
                          ) : (
                            <Badge tone={statusTone(status)} className="!text-[10px]">
                              {statusLabel(status, locale)}
                            </Badge>
                          )}
                          {departments.slice(0, 3).map((dept) => (
                            <DepartmentChip key={dept} deptKey={dept} />
                          ))}
                        </div>
                      </button>
                      <button
                        type="button"
                        className="absolute right-1.5 top-1.5 rounded-md p-1 text-content-muted opacity-0 transition-opacity hover:bg-surface hover:text-danger focus:opacity-100 group-hover:opacity-100"
                        onClick={() => setPendingDeleteId(thread.sessionId)}
                        aria-label={t("deleteSession", locale)}
                      >
                        <Trash2 size="xs" />
                      </button>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}

export function SessionSidebar() {
  const locale = useUserStore((s) => s.locale);
  const sidebarOpen = useSidebarStore((s) => s.open);
  const setSidebarOpen = useSidebarStore((s) => s.setOpen);
  const [mobileOpen, setMobileOpen] = useState(false);
  const drawerRef = useRef<HTMLDivElement>(null);

  useFocusTrap(mobileOpen, drawerRef);

  return (
    <>
      <Button
        variant="ghost"
        className="absolute left-3 top-3 z-30 !px-2 !py-2 md:hidden"
        onClick={() => setMobileOpen(true)}
        aria-label={t("openSessionHistory", locale)}
        aria-expanded={mobileOpen}
        aria-controls="session-history-drawer"
      >
        <Menu size="sm" />
      </Button>

      {!sidebarOpen && (
        <Button
          variant="ghost"
          className="absolute left-3 top-3 z-30 hidden items-center gap-1.5 !px-2.5 !py-2 md:inline-flex"
          onClick={() => setSidebarOpen(true)}
          aria-label={t("openSessionHistory", locale)}
          aria-expanded={false}
          aria-controls="session-sidebar-panel"
        >
          <History size="sm" className="text-brand" />
          <span className="text-xs font-medium text-content-primary">{t("sessionHistory", locale)}</span>
          <ArrowRight size="xs" className="text-content-muted" />
        </Button>
      )}

      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden" role="presentation">
          <button
            type="button"
            className="absolute inset-0 bg-black/40 backdrop-blur-[1px]"
            onClick={() => setMobileOpen(false)}
            aria-label={t("closeSessionHistory", locale)}
          />
          <div
            id="session-history-drawer"
            ref={drawerRef}
            className="session-sidebar absolute inset-y-0 left-0 flex w-[min(310px,88vw)] flex-col border-r border-border chat-glass shadow-xl"
            role="dialog"
            aria-modal="true"
            aria-label={t("sessionHistory", locale)}
          >
            <SessionSidebarPanel onCloseMobile={() => setMobileOpen(false)} />
          </div>
        </div>
      )}
    </>
  );
}
