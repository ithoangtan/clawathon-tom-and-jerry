import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { api, ApiError } from "@/lib/apiClient";

type Phase = "idle" | "sending" | "sent" | "error";

export function AdminTestEmailPanel() {
  const [to, setTo] = useState("");
  const [subject, setSubject] = useState("Test email từ Zalopay Wiki Agent");
  const [body, setBody] = useState("Đây là email test để kiểm tra kết nối Gmail token.");
  const [phase, setPhase] = useState<Phase>("idle");
  const [detail, setDetail] = useState<string | null>(null);

  async function handleSend() {
    if (!to.trim()) return;
    setPhase("sending");
    setDetail(null);
    try {
      const res = await api.testEmail({ to: to.trim(), subject, body });
      if (res.status === "sent") {
        setPhase("sent");
      } else {
        setDetail(res.detail ?? "Gửi thất bại, kiểm tra log server.");
        setPhase("error");
      }
    } catch (e) {
      setDetail(e instanceof ApiError ? (e.detail ?? e.message) : "Lỗi kết nối.");
      setPhase("error");
    }
  }

  const inputCls =
    "w-full rounded-lg border border-border bg-surface-glass px-3 py-2 text-sm text-content-primary placeholder:text-content-muted focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20 disabled:opacity-50";

  return (
    <Card>
      <div className="flex items-start gap-3">
        <div
          className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-sky-50 text-sky-600 dark:bg-sky-950 dark:text-sky-400"
          aria-hidden
        >
          ✉️
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold text-content-primary">Test Email</h3>
          <p className="mt-0.5 text-xs text-content-secondary">
            Gửi email thử để verify Gmail token hiện tại đang hoạt động.
          </p>
        </div>
      </div>

      <div className="mt-4 space-y-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-content-secondary">
            Địa chỉ nhận
          </label>
          <input
            type="email"
            value={to}
            onChange={(e) => setTo(e.target.value)}
            placeholder="email@example.com"
            className={inputCls}
            disabled={phase === "sending"}
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-content-secondary">
            Tiêu đề
          </label>
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Subject"
            className={inputCls}
            disabled={phase === "sending"}
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-content-secondary">
            Nội dung
          </label>
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={4}
            placeholder="Nội dung email..."
            className={`${inputCls} resize-none`}
            disabled={phase === "sending"}
          />
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            onClick={handleSend}
            disabled={!to.trim() || phase === "sending"}
          >
            {phase === "sending" ? "Đang gửi…" : "Gửi test email"}
          </Button>

          {phase === "sent" && (
            <span className="text-sm font-medium text-emerald-600" role="status">
              ✅ Đã gửi thành công!
            </span>
          )}

          {phase === "error" && (
            <span className="text-sm text-red-600" role="alert">
              ❌ {detail}
            </span>
          )}
        </div>

        {phase === "sent" && (
          <p className="text-xs text-content-muted">
            Kiểm tra hộp thư <strong>{to}</strong> — nếu không thấy, xem thêm spam/promotions.
          </p>
        )}
      </div>
    </Card>
  );
}
