import { useEffect, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { api, ApiError } from "@/lib/apiClient";

type GmailStatus = "checking" | "ok" | "need_auth" | "not_configured" | "failed";
type SendPhase = "idle" | "sending" | "sent" | "error";

export function AdminTestEmailPanel() {
  // ── Gmail auth status ────────────────────────────────────────────────────
  const [gmailStatus, setGmailStatus] = useState<GmailStatus>("checking");
  const [authUrl, setAuthUrl] = useState<string | null>(null);
  const [statusDetail, setStatusDetail] = useState<string | null>(null);
  const [statusMethod, setStatusMethod] = useState<string | null>(null);

  async function checkStatus() {
    setGmailStatus("checking");
    setAuthUrl(null);
    setStatusDetail(null);
    try {
      const res = await api.gmailStatus();
      setGmailStatus(res.status as GmailStatus);
      setAuthUrl(res.auth_url ?? null);
      setStatusDetail(res.detail ?? null);
      setStatusMethod(res.method ?? null);
    } catch {
      setGmailStatus("failed");
      setStatusDetail("Không thể kiểm tra — server lỗi.");
    }
  }

  useEffect(() => { checkStatus(); }, []);

  // ── Send test email ──────────────────────────────────────────────────────
  const [to, setTo] = useState("");
  const [subject, setSubject] = useState("Test email từ Zalopay Wiki Agent");
  const [body, setBody] = useState("Đây là email test để kiểm tra kết nối Gmail token.");
  const [sendPhase, setSendPhase] = useState<SendPhase>("idle");
  const [sendDetail, setSendDetail] = useState<string | null>(null);

  async function handleSend() {
    if (!to.trim()) return;
    setSendPhase("sending");
    setSendDetail(null);
    try {
      const res = await api.testEmail({ to: to.trim(), subject, body });
      if (res.status === "sent") {
        setSendPhase("sent");
        checkStatus(); // re-verify after successful send
      } else {
        setSendDetail(res.detail ?? "Gửi thất bại, kiểm tra log server.");
        setSendPhase("error");
      }
    } catch (e) {
      setSendDetail(e instanceof ApiError ? (e.detail ?? e.message) : "Lỗi kết nối.");
      setSendPhase("error");
    }
  }

  const inputCls =
    "w-full rounded-lg border border-border bg-surface-glass px-3 py-2 text-sm text-content-primary placeholder:text-content-muted focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20 disabled:opacity-50";

  // ── Status badge ─────────────────────────────────────────────────────────
  function StatusBadge() {
    if (gmailStatus === "checking") {
      return <span className="text-xs text-content-muted animate-pulse">Đang kiểm tra…</span>;
    }
    if (gmailStatus === "ok") {
      const method = statusMethod === "refresh_token" ? "refresh_token" : "AgentBase 3LO";
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          Authorized · {method}
        </span>
      );
    }
    if (gmailStatus === "need_auth") {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-950 dark:text-amber-300">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
          Chưa authorize
        </span>
      );
    }
    if (gmailStatus === "not_configured") {
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-500 dark:bg-slate-800 dark:text-slate-400">
          <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
          Chưa cấu hình
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-2.5 py-0.5 text-xs font-medium text-red-600 dark:bg-red-950 dark:text-red-400">
        <span className="h-1.5 w-1.5 rounded-full bg-red-500" />
        Lỗi
      </span>
    );
  }

  return (
    <Card>
      {/* Header */}
      <div className="flex items-start gap-3">
        <div
          className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-sky-50 text-sky-600 dark:bg-sky-950 dark:text-sky-400 text-lg"
          aria-hidden
        >
          ✉️
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-semibold text-content-primary">Test Email (Gmail)</h3>
            <StatusBadge />
          </div>
          <p className="mt-0.5 text-xs text-content-secondary">
            Gửi email thử để verify Gmail token · kiểm tra AgentBase Identity OAuth.
          </p>
        </div>
        <button
          type="button"
          onClick={checkStatus}
          className="flex-shrink-0 text-xs text-brand underline-offset-2 hover:underline"
          title="Kiểm tra lại"
        >
          Refresh
        </button>
      </div>

      {/* need_auth: show authorization link */}
      {gmailStatus === "need_auth" && authUrl && (
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-950/40">
          <p className="text-sm font-medium text-amber-800 dark:text-amber-300">
            ⚠️ Gmail chưa được authorize
          </p>
          <p className="mt-1 text-xs text-amber-700 dark:text-amber-400">
            Click link bên dưới để đăng nhập Google và cấp quyền <strong>gmail.send</strong>.
            Chỉ cần làm 1 lần — AgentBase sẽ lưu token tự động.
          </p>
          <a
            href={authUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-amber-500"
          >
            🔑 Authorize Gmail với Google
          </a>
          <p className="mt-2 text-[11px] text-amber-600 dark:text-amber-500">
            Sau khi authorize xong, nhấn <strong>Refresh</strong> để kiểm tra lại.
          </p>
        </div>
      )}

      {/* not_configured: show env var guide */}
      {gmailStatus === "not_configured" && (
        <div className="mt-4 rounded-lg border border-border bg-surface-elevated p-4">
          <p className="text-sm font-medium text-content-primary">Cấu hình cần thiết</p>
          <p className="mt-1 text-xs text-content-secondary mb-2">
            Chọn 1 trong 2 cách:
          </p>
          <div className="space-y-3">
            <div>
              <p className="text-xs font-semibold text-brand mb-1">Cách A — AgentBase Identity (runtime)</p>
              <pre className="rounded bg-surface-glass p-2 text-[11px] text-content-secondary overflow-x-auto">{`APP_ENV=agentbase
GREENNODE_AGENT_IDENTITY=<tên identity của agent>
GDRIVE_OAUTH_PROVIDER=identity-google-space
GDRIVE_OAUTH_AGENT_USER_ID=<email Gmail muốn gửi>`}</pre>
            </div>
            <div>
              <p className="text-xs font-semibold text-content-secondary mb-1">Cách B — Local refresh token</p>
              <pre className="rounded bg-surface-glass p-2 text-[11px] text-content-secondary overflow-x-auto">{`GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
GMAIL_REFRESH_TOKEN=...   # chạy scripts/get_gmail_token.py
GMAIL_SENDER=you@gmail.com`}</pre>
            </div>
          </div>
        </div>
      )}

      {/* failed / error detail */}
      {(gmailStatus === "failed") && statusDetail && (
        <div className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 dark:border-red-900 dark:bg-red-950/40">
          <p className="text-xs text-red-600 dark:text-red-400">{statusDetail}</p>
        </div>
      )}

      {/* Send form — only show when authorized */}
      {gmailStatus === "ok" && (
        <div className="mt-5 space-y-3 border-t border-border pt-4">
          <div>
            <label className="mb-1 block text-xs font-medium text-content-secondary">Địa chỉ nhận</label>
            <input
              type="email"
              value={to}
              onChange={(e) => setTo(e.target.value)}
              placeholder="email@example.com"
              className={inputCls}
              disabled={sendPhase === "sending"}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-content-secondary">Tiêu đề</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className={inputCls}
              disabled={sendPhase === "sending"}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-content-secondary">Nội dung</label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={3}
              className={`${inputCls} resize-none`}
              disabled={sendPhase === "sending"}
            />
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button
              variant="primary"
              onClick={handleSend}
              disabled={!to.trim() || sendPhase === "sending"}
            >
              {sendPhase === "sending" ? "Đang gửi…" : "Gửi test email"}
            </Button>
            {sendPhase === "sent" && (
              <span className="text-sm font-medium text-emerald-600" role="status">
                ✅ Đã gửi — kiểm tra hộp thư <strong>{to}</strong>
              </span>
            )}
            {sendPhase === "error" && (
              <span className="text-sm text-red-600" role="alert">❌ {sendDetail}</span>
            )}
          </div>
        </div>
      )}
    </Card>
  );
}
