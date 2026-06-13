import type { Lang } from "./types";

type Strings = Record<string, { en: string; vi: string }>;

const strings: Strings = {
  appTitle: { en: "ZaloPay Knowledge", vi: "Tri thức ZaloPay" },
  appSubtitle: {
    en: "Citation-grounded answers from internal docs",
    vi: "Câu trả lời có trích dẫn từ tài liệu nội bộ",
  },
  navChat: { en: "Chat", vi: "Hỏi đáp" },
  navDashboard: { en: "Dashboard", vi: "Bảng điều khiển" },
  navSettings: { en: "Settings", vi: "Cài đặt" },
  newSession: { en: "New session", vi: "Phiên mới" },
  indexNotReady: {
    en: "Knowledge base not synced yet — go to Settings to sync.",
    vi: "Cơ sở tri thức chưa được đồng bộ — vào Cài đặt để đồng bộ.",
  },
  askPlaceholder: {
    en: "Ask about ZaloPay policies, runbooks, or procedures…",
    vi: "Hỏi về chính sách, quy trình hoặc runbook của ZaloPay…",
  },
  send: { en: "Send", vi: "Gửi" },
  sending: { en: "Thinking…", vi: "Đang xử lý…" },
  targetDepartments: { en: "Target departments", vi: "Phòng ban mục tiêu" },
  targetAll: { en: "Auto-route (Agent Center)", vi: "Tự động định tuyến" },
  citations: { en: "Sources", vi: "Nguồn tham khảo" },
  confidence: { en: "Confidence", vi: "Độ tin cậy" },
  feedbackThanks: { en: "Thanks for your feedback!", vi: "Cảm ơn phản hồi của bạn!" },
  feedbackPrompt: { en: "Was this helpful?", vi: "Câu trả lời có hữu ích không?" },
  feedbackComment: { en: "Optional comment", vi: "Bình luận (tuỳ chọn)" },
  feedbackCommentPlaceholder: {
    en: "Tell us what worked or what was missing…",
    vi: "Cho chúng tôi biết điều gì hữu ích hoặc còn thiếu…",
  },
  submit: { en: "Submit", vi: "Gửi" },
  saved: { en: "Saved", vi: "Đã lưu" },
  identityHint: {
    en: "Role and home department are sent with every chat request to personalize answers.",
    vi: "Vai trò và phòng ban chính được gửi kèm mỗi yêu cầu chat để cá nhân hoá câu trả lời.",
  },
  conflictTitle: { en: "Conflicting sources detected", vi: "Phát hiện nguồn mâu thuẫn" },
  conflictHint: {
    en: "These departments document different facts. Please verify with doc owners.",
    vi: "Các phòng ban ghi nhận thông tin khác nhau. Vui lòng xác minh với chủ tài liệu.",
  },
  conflictItem: {
    en: "Conflict {index} of {total}",
    vi: "Mâu thuẫn {index}/{total}",
  },
  deprecatedWarning: { en: "Deprecated document", vi: "Tài liệu đã lỗi thời" },
  successorDoc: { en: "See updated version", vi: "Xem phiên bản mới" },
  statusAnswered: { en: "Answered", vi: "Đã trả lời" },
  statusRefused: { en: "Not covered in the docs", vi: "Không có thông tin trong tài liệu" },
  refusalTitle: { en: "Not covered in the docs", vi: "Không có thông tin trong tài liệu" },
  refusalHint: {
    en: "Try rephrasing your question or contact the document owner for that topic.",
    vi: "Hãy thử hỏi cụ thể hơn hoặc liên hệ bộ phận sở hữu tài liệu liên quan.",
  },
  accessDeniedTitle: { en: "Access denied", vi: "Không có quyền truy cập" },
  accessDeniedHint: {
    en: "Your role cannot query this department's knowledge. Contact your administrator if you need access.",
    vi: "Vai trò của bạn không được phép truy vấn tài liệu bộ phận này. Liên hệ quản trị viên nếu bạn cần quyền truy cập.",
  },
  statusAccessDenied: { en: "Access denied", vi: "Không có quyền truy cập" },
  citationSection: { en: "Section", vi: "Mục" },
  citationPage: { en: "Page", vi: "Trang" },
  citationUpdated: { en: "Updated", vi: "Cập nhật" },
  statusPartial: { en: "Partial answer", vi: "Trả lời một phần" },
  emptyChatTitle: {
    en: "How can I help?",
    vi: "Tôi có thể giúp gì?",
  },
  emptyChat: {
    en: "Ask a question to get started. Every answer includes citations from Confluence or Drive.",
    vi: "Đặt câu hỏi để bắt đầu. Mỗi câu trả lời đều có trích dẫn từ Confluence hoặc Drive.",
  },
  you: { en: "You", vi: "Bạn" },
  assistantName: { en: "ZaloPay Knowledge", vi: "Tri thức ZaloPay" },
  inputHint: {
    en: "Enter to send · Shift+Enter for new line",
    vi: "Enter để gửi · Shift+Enter xuống dòng",
  },
  exampleQuestions: { en: "Try asking:", vi: "Thử hỏi:" },
  errorGeneric: { en: "Something went wrong. Please try again.", vi: "Đã xảy ra lỗi. Vui lòng thử lại." },
  errorTimeout: { en: "Request timed out. Try a narrower question.", vi: "Hết thời gian chờ. Thử câu hỏi cụ thể hơn." },
  errorKbNotReady: {
    en: "Knowledge base not ready — please sync first.",
    vi: "Cơ sở tri thức chưa sẵn sàng — vui lòng đồng bộ trước.",
  },
  retry: { en: "Retry", vi: "Thử lại" },
  dashboardTitle: { en: "Usage & Health", vi: "Sử dụng & Sức khoẻ" },
  syncStatus: { en: "Sync Status", vi: "Trạng thái đồng bộ" },
  queryHistory: { en: "Recent Queries", vi: "Truy vấn gần đây" },
  settingsTitle: { en: "Settings", vi: "Cài đặt" },
  identity: { en: "Your identity", vi: "Danh tính của bạn" },
  syncControls: { en: "Knowledge sync", vi: "Đồng bộ tri thức" },
  configPanel: { en: "Runtime config", vi: "Cấu hình runtime" },
  syncConfluence: { en: "Sync from Confluence", vi: "Đồng bộ từ Confluence" },
  syncGdrive: { en: "Sync PDFs from Drive", vi: "Đồng bộ PDF từ Drive" },
  syncing: { en: "Syncing…", vi: "Đang đồng bộ…" },
  fresh: { en: "Fresh", vi: "Mới" },
  stale: { en: "Stale", vi: "Cũ" },
  neverSynced: { en: "Never synced", vi: "Chưa đồng bộ" },
  docs: { en: "docs", vi: "tài liệu" },
  chunks: { en: "chunks", vi: "đoạn" },
  userId: { en: "User ID", vi: "Mã người dùng" },
  role: { en: "Role", vi: "Vai trò" },
  homeDept: { en: "Home department", vi: "Phòng ban chính" },
  locale: { en: "Language", vi: "Ngôn ngữ" },
  save: { en: "Save", vi: "Lưu" },
  totalQueries: { en: "Total queries", vi: "Tổng truy vấn" },
  refusalRate: { en: "Refusal rate", vi: "Tỷ lệ từ chối" },
  latencyP50: { en: "Latency p50", vi: "Độ trễ p50" },
  latencyP95: { en: "Latency p95", vi: "Độ trễ p95" },
  feedbackUp: { en: "Thumbs up", vi: "Hài lòng" },
  feedbackDown: { en: "Thumbs down", vi: "Không hài lòng" },
  expandCitations: { en: "Show all sources", vi: "Xem tất cả nguồn" },
  collapseCitations: { en: "Hide sources", vi: "Ẩn nguồn" },
  clarifyPrompt: { en: "Clarification needed", vi: "Cần làm rõ" },
  skipToContent: { en: "Skip to main content", vi: "Chuyển đến nội dung chính" },
  healthHealthy: { en: "System healthy", vi: "Hệ thống hoạt động" },
  healthIndexPending: { en: "Index not ready", vi: "Chỉ mục chưa sẵn sàng" },
  noHistory: { en: "No queries yet.", vi: "Chưa có truy vấn nào." },
  loading: { en: "Loading…", vi: "Đang tải…" },
  copy: { en: "Copy", vi: "Sao chép" },
  copied: { en: "Copied!", vi: "Đã sao chép!" },
  copyCode: { en: "Copy code", vi: "Sao chép mã" },
  copyMessage: { en: "Copy response", vi: "Sao chép câu trả lời" },
};

export function t(
  key: keyof typeof strings,
  locale: Lang,
  vars?: Record<string, string | number>,
): string {
  const entry = strings[key];
  let text = entry ? (locale === "vi" ? entry.vi : entry.en) : String(key);
  if (vars) {
    for (const [name, value] of Object.entries(vars)) {
      text = text.replaceAll(`{${name}}`, String(value));
    }
  }
  return text;
}

export type I18nKey = keyof typeof strings;
