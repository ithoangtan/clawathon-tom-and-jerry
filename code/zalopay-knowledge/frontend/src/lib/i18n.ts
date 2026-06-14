import type { Department, Lang } from "./types";
import { departmentLabel } from "./departments";

type Strings = Record<string, { en: string; vi: string }>;

const strings: Strings = {
  appTitle: { en: "Zalopay Knowledge", vi: "Tri thức Zalopay" },
  appSubtitle: {
    en: "Citation-grounded answers from internal docs",
    vi: "Câu trả lời có trích dẫn từ tài liệu nội bộ",
  },
  navChat: { en: "Chat", vi: "Hỏi đáp" },
  navDashboard: { en: "Dashboard", vi: "Bảng điều khiển" },
  navSettings: { en: "Settings", vi: "Cài đặt" },
  navAdmin: { en: "Admin", vi: "Quản trị" },
  newSession: { en: "New session", vi: "Phiên mới" },
  sessionHistory: { en: "Session history", vi: "Lịch sử phiên hỏi đáp" },
  sessionHistoryHint: {
    en: "Recent conversations saved on this device.",
    vi: "Các cuộc hội thoại gần đây được lưu trên thiết bị này.",
  },
  searchSessions: { en: "Search sessions", vi: "Tìm phiên hỏi đáp" },
  noSessions: { en: "No saved sessions yet.", vi: "Chưa có phiên nào được lưu." },
  deleteSession: { en: "Delete session", vi: "Xóa phiên" },
  deleteSessionConfirm: {
    en: "Delete this session? This cannot be undone.",
    vi: "Xóa phiên này? Hành động không thể hoàn tác.",
  },
  openSessionHistory: { en: "Open session history", vi: "Mở lịch sử phiên" },
  closeSessionHistory: { en: "Close session history", vi: "Đóng lịch sử phiên" },
  statusConflict: { en: "Conflict", vi: "Mâu thuẫn" },
  statusPending: { en: "In progress", vi: "Đang xử lý" },
  cancel: { en: "Cancel", vi: "Hủy" },
  confirm: { en: "Confirm", vi: "Xác nhận" },
  indexNotReadyDept: {
    en: "The {department} department has no indexed data yet.",
    vi: "Phòng ban {department} chưa có dữ liệu.",
  },
  indexNotReadyDepts: {
    en: "The selected departments ({departments}) have no indexed data yet.",
    vi: "Các phòng ban đã chọn ({departments}) chưa có dữ liệu.",
  },
  indexNotReadyAuto: {
    en: "Target departments have no indexed data yet.",
    vi: "Các phòng ban mục tiêu chưa có dữ liệu.",
  },
  indexNotReadyAdminLink: {
    en: "Go to Admin to sync from Confluence.",
    vi: "Vào Quản trị để đồng bộ từ Confluence.",
  },
  askPlaceholder: {
    en: "Ask about Zalopay policies, runbooks, or procedures…",
    vi: "Hỏi về chính sách, quy trình hoặc runbook của Zalopay…",
  },
  send: { en: "Send", vi: "Gửi" },
  sending: { en: "Thinking…", vi: "Đang xử lý…" },
  targetDepartments: { en: "Target departments", vi: "Phòng ban mục tiêu" },
  targetAll: { en: "Auto-route (Agent Center)", vi: "Tự động định tuyến" },
  turnOffAutoRoute: {
    en: "Turn off auto-route",
    vi: "Tắt tự động định tuyến",
  },
  enableAutoRoute: {
    en: "Enable auto-route (Agent Center)",
    vi: "Bật tự động định tuyến",
  },
  departmentSearchPlaceholder: {
    en: "Search departments by name, head, or description…",
    vi: "Tìm phòng ban theo tên, trưởng bộ phận hoặc mô tả…",
  },
  departmentSearchEmpty: {
    en: "No departments match your search.",
    vi: "Không có phòng ban nào khớp với tìm kiếm của bạn.",
  },
  removeDepartment: {
    en: "Remove {name}",
    vi: "Xóa {name}",
  },
  addDepartment: { en: "Add department", vi: "Thêm phòng ban" },
  addDepartmentModalTitle: {
    en: "Add target departments",
    vi: "Thêm phòng ban mục tiêu",
  },
  addDepartmentModalHint: {
    en: "Search and pin departments. Click the check again to deselect. The picker stays open for multi-select.",
    vi: "Tìm và ghim phòng ban. Nhấn dấu tick lần nữa để bỏ chọn. Cửa sổ vẫn mở để chọn nhiều mục.",
  },
  closeAddDepartments: { en: "Close department picker", vi: "Đóng bộ chọn phòng ban" },
  selectDepartment: { en: "Select {name}", vi: "Chọn {name}" },
  deselectDepartment: { en: "Deselect {name}", vi: "Bỏ chọn {name}" },
  selectDepartmentAction: { en: "Select", vi: "Chọn" },
  deselectDepartmentAction: { en: "Deselect", vi: "Bỏ chọn" },
  departmentNoIndexWarning: {
    en: "No indexed data yet",
    vi: "Chưa có dữ liệu được lập chỉ mục",
  },
  departmentAlreadySelected: { en: "Already selected", vi: "Đã chọn" },
  departmentHeadLabel: { en: "Head manager", vi: "Trưởng bộ phận" },
  departmentDescriptionLabel: { en: "Description", vi: "Mô tả" },
  done: { en: "Done", vi: "Xong" },
  change: { en: "Change", vi: "Thay đổi" },
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
  outOfScopeTitle: {
    en: "Outside indexed documentation",
    vi: "Ngoài phạm vi tài liệu đã lập chỉ mục",
  },
  outOfScopeHint: {
    en: "I only answer from internal docs — not live data, web search, or system actions. Try a documentation question or contact the teams below.",
    vi: "Tôi chỉ trả lời từ tài liệu nội bộ — không có dữ liệu thời gian thực, tìm kiếm web hay thao tác hệ thống. Hãy hỏi về tài liệu hoặc liên hệ các bộ phận bên dưới.",
  },
  statusOutOfScope: { en: "Outside scope", vi: "Ngoài phạm vi" },
  statusAccessDenied: { en: "Access denied", vi: "Không có quyền truy cập" },
  citationSection: { en: "Section", vi: "Mục" },
  citationPage: { en: "Page", vi: "Trang" },
  citationUpdated: { en: "Updated", vi: "Cập nhật" },
  statusPartial: { en: "Partial answer", vi: "Trả lời một phần" },
  statusClarify: { en: "Clarification needed", vi: "Cần làm rõ" },
  partialGapHint: {
    en: "Some targeted departments had no relevant documentation. The answer below reflects only the sources that were found.",
    vi: "Một số phòng ban mục tiêu không có tài liệu liên quan. Câu trả lời bên dưới chỉ dựa trên các nguồn đã tìm thấy.",
  },
  partialGapDepartments: {
    en: "No docs found for: {departments}",
    vi: "Không có tài liệu cho: {departments}",
  },
  emptyChatTitle: {
    en: "How can I help?",
    vi: "Tôi có thể giúp gì?",
  },
  emptyChat: {
    en: "Ask a question to get started. Every answer includes citations from Confluence or Drive.",
    vi: "Đặt câu hỏi để bắt đầu. Mỗi câu trả lời đều có trích dẫn từ Confluence hoặc Drive.",
  },
  you: { en: "You", vi: "Bạn" },
  assistantName: { en: "Zalopay Knowledge", vi: "Tri thức Zalopay" },
  inputHint: {
    en: "Enter to send · Shift+Enter for new line",
    vi: "Enter để gửi · Shift+Enter xuống dòng",
  },
  inputHintSend: { en: "Send", vi: "Gửi" },
  inputHintNewline: { en: "New line", vi: "Xuống dòng" },
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
  adminGdriveHint: {
    en: "Index PDF documents from Google Drive",
    vi: "Lập chỉ mục tài liệu PDF từ Google Drive",
  },
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
  deflectionRate: {
    en: "Deflection rate",
    vi: "Tỷ lệ giải quyết",
  },
  answeredWrongRate: {
    en: "Answered-wrong rate",
    vi: "Tỷ lệ trả lời sai",
  },
  refusalRate: { en: "Refusal rate", vi: "Tỷ lệ từ chối" },
  partialRate: { en: "Partial answer rate", vi: "Tỷ lệ trả lời một phần" },
  conflictRate: { en: "Conflict rate", vi: "Tỷ lệ mâu thuẫn" },
  latencyP50: { en: "Latency p50", vi: "Độ trễ p50" },
  latencyP95: { en: "Latency p95", vi: "Độ trễ p95" },
  feedbackUp: { en: "Thumbs up", vi: "Hài lòng" },
  feedbackDown: { en: "Thumbs down", vi: "Không hài lòng" },
  evalFaithfulness: { en: "Eval faithfulness", vi: "Độ trung thực (eval)" },
  evalRefusalPrecision: { en: "Refusal precision", vi: "Độ chính xác từ chối" },
  evalRefusalRecall: { en: "Refusal recall", vi: "Độ bao phủ từ chối" },
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
  knowledgeAgent: { en: "Knowledge Agent", vi: "Trợ lý Tri thức" },
  settingsSubtitle: {
    en: "Configure your identity, sync preferences, and runtime environment for grounded answers.",
    vi: "Cấu hình danh tính, tùy chọn đồng bộ và môi trường runtime để nhận câu trả lời có căn cứ.",
  },
  adminTitle: { en: "Knowledge sync", vi: "Đồng bộ tri thức" },
  adminSubtitle: {
    en: "Trigger Confluence sync per department or globally, and monitor live job status with page counts and errors.",
    vi: "Kích hoạt đồng bộ Confluence theo phòng ban hoặc toàn bộ, theo dõi trạng thái job, số trang và lỗi.",
  },
  adminSyncActions: { en: "Sync actions", vi: "Thao tác đồng bộ" },
  adminSyncAll: { en: "Sync all departments", vi: "Đồng bộ tất cả phòng ban" },
  adminSyncDepartment: { en: "Sync {department}", vi: "Đồng bộ {department}" },
  adminDepartmentStatus: { en: "Per-department index", vi: "Chỉ mục theo phòng ban" },
  adminRecentJobs: { en: "Recent sync jobs", vi: "Job đồng bộ gần đây" },
  adminNoJobs: { en: "No sync jobs yet.", vi: "Chưa có job đồng bộ nào." },
  adminSpace: { en: "Confluence space", vi: "Không gian Confluence" },
  adminPages: { en: "Pages", vi: "Trang" },
  adminJobSource: { en: "Source", vi: "Nguồn" },
  adminJobDepartment: { en: "Department", vi: "Phòng ban" },
  adminJobStatus: { en: "Status", vi: "Trạng thái" },
  adminJobStarted: { en: "Started", vi: "Bắt đầu" },
  adminJobFinished: { en: "Finished", vi: "Kết thúc" },
  adminJobAllDepartments: { en: "All departments", vi: "Tất cả phòng ban" },
  adminJobSuccess: { en: "success", vi: "thành công" },
  adminJobFailure: { en: "failure", vi: "thất bại" },
  adminJobRunning: { en: "running", vi: "đang chạy" },
  adminSyncStarted: { en: "Sync started.", vi: "Đã bắt đầu đồng bộ." },
  adminSyncInProgress: { en: "A sync job is already running.", vi: "Đã có job đồng bộ đang chạy." },
  adminSyncFailed: { en: "Failed to start sync.", vi: "Không thể bắt đầu đồng bộ." },
  adminTotalDocs: { en: "Total documents", vi: "Tổng tài liệu" },
  adminTotalChunks: { en: "Total chunks", vi: "Tổng đoạn" },
  adminSourcesSynced: { en: "Sources synced", vi: "Nguồn đã đồng bộ" },
  adminLastUpdate: { en: "Last updated", vi: "Cập nhật cuối" },
  adminKnowledgeSources: { en: "Knowledge sources", vi: "Nguồn tri thức" },
  adminViewDetail: { en: "Details", vi: "Chi tiết" },
  adminSyncHistory: { en: "Sync history (14 days)", vi: "Lịch sử đồng bộ (14 ngày)" },
  adminClose: { en: "Close", vi: "Đóng" },
  adminNoData: { en: "No data", vi: "Chưa có dữ liệu" },
  adminTypeConfluence: { en: "Confluence", vi: "Confluence" },
  adminTypeDrive: { en: "Drive", vi: "Drive" },
  adminPagesLabel: { en: "Pages", vi: "Trang" },
  adminFilesLabel: { en: "Files", vi: "Tệp" },
  adminSyncThis: { en: "Sync", vi: "Đồng bộ" },
  adminNeverSynced: { en: "Never", vi: "Chưa sync" },
  adminJobsDay: { en: "jobs", vi: "jobs" },
  adminFilterAll: { en: "All sources", vi: "Tất cả nguồn" },
  adminFilterConfluence: { en: "Confluence only", vi: "Chỉ Confluence" },
  adminFilterDrive: { en: "Drive only", vi: "Chỉ Drive" },
  dashboardSubtitle: {
    en: "Real-time usage metrics, sync health, and query history for your knowledge agent.",
    vi: "Số liệu sử dụng theo thời gian thực, tình trạng đồng bộ và lịch sử truy vấn của trợ lý tri thức.",
  },
  configEmpty: {
    en: "No config snapshot available.",
    vi: "Chưa có ảnh chụp cấu hình.",
  },
  configVersion: { en: "Version {version}", vi: "Phiên bản {version}" },
  lastSync: { en: "Last sync: {date}", vi: "Đồng bộ lần cuối: {date}" },
  langEn: { en: "English", vi: "English" },
  langVi: { en: "Tiếng Việt", vi: "Tiếng Việt" },
  navAriaLabel: { en: "Main navigation", vi: "Điều hướng chính" },
  historyTime: { en: "Time", vi: "Thời gian" },
  historyQuestion: { en: "Question", vi: "Câu hỏi" },
  historyDepartments: { en: "Departments", vi: "Phòng ban" },
  historyStatus: { en: "Status", vi: "Trạng thái" },
  historyLatency: { en: "Latency", vi: "Độ trễ" },
  historyModel: { en: "Model", vi: "Model" },
  modelUsedLabel: { en: "Model", vi: "Model" },
  sourceConfluence: { en: "Confluence", vi: "Confluence" },
  sourceGdrive: { en: "Google Drive", vi: "Google Drive" },
  syncStateRunning: { en: "running", vi: "đang chạy" },
  syncStateIdle: { en: "idle", vi: "chờ" },
  syncStateError: { en: "error", vi: "lỗi" },
  freshnessLessThan1h: { en: "< 1h ago", vi: "< 1 giờ trước" },
  freshnessHoursAgo: { en: "{hours}h ago", vi: "{hours} giờ trước" },
  freshnessDaysAgo: { en: "{days}d ago", vi: "{days} ngày trước" },
  switchToEnglish: { en: "Switch to English", vi: "Chuyển sang tiếng Anh" },
  switchToVietnamese: { en: "Switch to Vietnamese", vi: "Chuyển sang tiếng Việt" },
  evidenceInspectorTitle: { en: "Source evidence", vi: "Minh chứng nguồn" },
  evidenceInspectorAriaLabel: {
    en: "Citation evidence for source {index}",
    vi: "Minh chứng trích dẫn nguồn {index}",
  },
  evidenceExcerpt: { en: "Excerpt", vi: "Đoạn trích" },
  evidenceExcerptMissing: {
    en: "Excerpt not available for this source yet.",
    vi: "Chưa có đoạn trích cho nguồn này.",
  },
  evidenceLifecycleActive: { en: "Active", vi: "Đang dùng" },
  evidenceLifecycleDeprecated: { en: "Deprecated", vi: "Đã lỗi thời" },
  evidenceDocTypeUnknown: { en: "Document", vi: "Tài liệu" },
  evidenceChunkId: { en: "Chunk ID", vi: "Mã đoạn" },
  openInConfluence: { en: "Open in Confluence", vi: "Mở trong Confluence" },
  openInDrive: { en: "Open in Drive", vi: "Mở trong Drive" },
  openInSource: { en: "Open source document", vi: "Mở tài liệu nguồn" },
  closeInspector: { en: "Close evidence panel", vi: "Đóng bảng minh chứng" },
  citationKeyboardHint: {
    en: "Press 1–9 to switch sources · Esc to close",
    vi: "Nhấn 1–9 để chuyển nguồn · Esc để đóng",
  },
  evidenceSelectSource: { en: "View source {index}", vi: "Xem nguồn {index}" },
  pipelineStepRouting: {
    en: "Agent Center routing",
    vi: "Định tuyến Agent Center",
  },
  pipelineStepRetrieval: {
    en: "Per-department retrieval",
    vi: "Truy xuất theo phòng ban",
  },
  pipelineStepGrade: {
    en: "Grade / relevance check",
    vi: "Chấm điểm / kiểm tra liên quan",
  },
  pipelineStepVerify: {
    en: "Claim verification",
    vi: "Xác minh khẳng định",
  },
  pipelineStepSynthesis: {
    en: "Answer synthesis",
    vi: "Tổng hợp câu trả lời",
  },
  pipelineDeptBranches: {
    en: "Department retrieval branches",
    vi: "Nhánh truy xuất theo phòng ban",
  },
  pipelineComplete: { en: "Processing complete", vi: "Đã xử lý xong" },
  pipelineProcessedSummary: {
    en: "Processed in {seconds}s · {count} departments",
    vi: "Xử lý trong {seconds}s · {count} phòng ban",
  },
  "tutorial.welcome.title": {
    en: "Welcome to Zalopay Knowledge",
    vi: "Chào mừng đến Tri thức Zalopay",
  },
  "tutorial.welcome.description": {
    en: "This agent answers questions from internal Confluence and Drive docs only — every answer includes traceable sources. This quick tour shows the main workflows.",
    vi: "Trợ lý chỉ trả lời từ tài liệu Confluence và Drive nội bộ — mỗi câu trả lời đều có nguồn truy vết. Tour ngắn này giới thiệu các luồng chính.",
  },
  "tutorial.departments.title": {
    en: "Choose where to search",
    vi: "Chọn phạm vi tìm kiếm",
  },
  "tutorial.departments.description": {
    en: "Keep Auto-route to let the agent pick Risk, Growth Enablement, or Bank Partnerships — or pin one or more departments to narrow retrieval.",
    vi: "Giữ Tự động định tuyến để trợ lý chọn Risk, Growth Enablement hoặc Bank Partnerships — hoặc ghim một hoặc nhiều phòng ban để thu hẹp kết quả.",
  },
  "tutorial.examples.title": {
    en: "Try a starter question",
    vi: "Thử một câu hỏi mẫu",
  },
  "tutorial.examples.description": {
    en: "Click any example to send it instantly. Good questions mention a process, policy, or runbook (e.g. settlement reconciliation or KYC thresholds).",
    vi: "Nhấn vào câu mẫu để gửi ngay. Câu hỏi tốt nên nêu quy trình, chính sách hoặc runbook (ví dụ đối soát thanh toán hoặc ngưỡng KYC).",
  },
  "tutorial.chatInput.title": {
    en: "Ask in natural language",
    vi: "Hỏi bằng ngôn ngữ tự nhiên",
  },
  "tutorial.chatInput.description": {
    en: "Type your question here and press Enter or Send. Shift+Enter adds a new line. Answers stream in with citations you can open in Confluence or Drive.",
    vi: "Nhập câu hỏi và nhấn Enter hoặc Gửi. Shift+Enter để xuống dòng. Câu trả lời hiển thị kèm trích dẫn mở được trên Confluence hoặc Drive.",
  },
  "tutorial.citations.title": {
    en: "Verify with Sources",
    vi: "Xác minh qua Nguồn tham khảo",
  },
  "tutorial.citations.description": {
    en: "After each answer, a Sources section lists numbered citations with links, sections, and freshness badges. Always check sources before acting on policy or operational guidance.",
    vi: "Sau mỗi câu trả lời, mục Nguồn tham khảo liệt kê trích dẫn có số thứ tự, liên kết, mục và nhãn độ mới. Luôn kiểm tra nguồn trước khi áp dụng chính sách hoặc hướng dẫn vận hành.",
  },
  "tutorial.navDashboard.title": {
    en: "Monitor usage & health",
    vi: "Theo dõi sử dụng & sức khỏe",
  },
  "tutorial.navDashboard.description": {
    en: "Open Dashboard to see query volume, refusal rate, latency, sync status, and recent query history for your team.",
    vi: "Mở Bảng điều khiển để xem lượng truy vấn, tỷ lệ từ chối, độ trễ, trạng thái đồng bộ và lịch sử truy vấn gần đây.",
  },
  "tutorial.dashboardOverview.title": {
    en: "Usage & sync at a glance",
    vi: "Sử dụng & đồng bộ trong một màn hình",
  },
  "tutorial.dashboardOverview.description": {
    en: "Track how the agent is used and whether knowledge sources are up to date. Admins can trigger manual sync from Settings when the index is pending.",
    vi: "Theo dõi cách trợ lý được dùng và tài liệu có cập nhật không. Quản trị viên có thể đồng bộ thủ công từ Cài đặt khi chỉ mục chưa sẵn sàng.",
  },
  "tutorial.finish.title": {
    en: "You're ready to go",
    vi: "Bạn đã sẵn sàng",
  },
  "tutorial.finish.description": {
    en: "Reopen this tour anytime from Help. Set your role and home department in Settings so answers match your context.",
    vi: "Mở lại tour bất cứ lúc nào từ Trợ giúp. Đặt vai trò và phòng ban chính trong Cài đặt để câu trả lời phù hợp ngữ cảnh của bạn.",
  },
  "tutorial.response.welcome.title": {
    en: "How to read an answer",
    vi: "Cách đọc câu trả lời",
  },
  "tutorial.response.welcome.description": {
    en: "Every answer is grounded in internal documents only. This quick guide shows you what each part of the response means.",
    vi: "Mỗi câu trả lời đều được căn cứ hoàn toàn từ tài liệu nội bộ. Hướng dẫn này giải thích ý nghĩa từng phần của câu trả lời.",
  },
  "tutorial.response.answer.title": {
    en: "The answer",
    vi: "Câu trả lời",
  },
  "tutorial.response.answer.description": {
    en: "The main answer synthesized from indexed documents. It may include a confidence badge (High / Medium / Low) and the AI model used to generate it.",
    vi: "Câu trả lời tổng hợp từ tài liệu đã lập chỉ mục. Có thể kèm nhãn độ tin cậy (Cao / Trung bình / Thấp) và model AI đã tạo ra câu trả lời.",
  },
  "tutorial.response.citations.title": {
    en: "Sources & citations",
    vi: "Nguồn & trích dẫn",
  },
  "tutorial.response.citations.description": {
    en: "Each numbered source links to the exact Confluence page or Drive file. Click any source to open the evidence panel with the matching excerpt. Always verify before acting on policy guidance.",
    vi: "Mỗi nguồn được đánh số dẫn đến đúng trang Confluence hoặc file Drive. Nhấn vào nguồn để mở bảng minh chứng với đoạn trích khớp. Luôn xác minh trước khi áp dụng hướng dẫn chính sách.",
  },
  "tutorial.response.feedback.title": {
    en: "Give feedback",
    vi: "Phản hồi",
  },
  "tutorial.response.feedback.description": {
    en: "Let us know if the answer was helpful. Your feedback improves future answers. Click ? anytime to replay this guide.",
    vi: "Cho chúng tôi biết câu trả lời có hữu ích không. Phản hồi của bạn giúp cải thiện câu trả lời sau này. Nhấn ? bất cứ lúc nào để xem lại hướng dẫn.",
  },
  "tutorial.dashboard.welcome.title": {
    en: "Usage & Health Dashboard",
    vi: "Bảng điều khiển Sử dụng & Sức khoẻ",
  },
  "tutorial.dashboard.welcome.description": {
    en: "Monitor your knowledge agent's usage, sync health, and query history from this page.",
    vi: "Theo dõi mức độ sử dụng, tình trạng đồng bộ và lịch sử truy vấn của trợ lý tri thức tại đây.",
  },
  "tutorial.dashboard.metrics.title": {
    en: "Usage metrics",
    vi: "Số liệu sử dụng",
  },
  "tutorial.dashboard.metrics.description": {
    en: "Key metrics at a glance: total queries, deflection rate, refusal rate, latency, and evaluation scores. Use these to gauge agent effectiveness.",
    vi: "Số liệu chính: tổng truy vấn, tỷ lệ giải quyết, tỷ lệ từ chối, độ trễ và điểm đánh giá. Dùng để đánh giá hiệu quả của trợ lý.",
  },
  "tutorial.dashboard.history.title": {
    en: "Recent query history",
    vi: "Lịch sử truy vấn gần đây",
  },
  "tutorial.dashboard.history.description": {
    en: "Browse recent queries with their status, latency, departments routed to, and the model used. Use this to audit answers or spot patterns.",
    vi: "Duyệt các truy vấn gần đây với trạng thái, độ trễ, phòng ban được định tuyến và model sử dụng. Dùng để kiểm tra câu trả lời hoặc nhận biết xu hướng.",
  },
  "tutorial.settings.welcome.title": {
    en: "Settings",
    vi: "Cài đặt",
  },
  "tutorial.settings.welcome.description": {
    en: "Configure your identity, sync preferences, and runtime config here. Your role and home department are sent with every query to personalize answers.",
    vi: "Cấu hình danh tính, tùy chọn đồng bộ và runtime tại đây. Vai trò và phòng ban chính được gửi kèm mỗi truy vấn để cá nhân hoá câu trả lời.",
  },
  "tutorial.settings.identity.title": {
    en: "Your identity",
    vi: "Danh tính của bạn",
  },
  "tutorial.settings.identity.description": {
    en: "Set your role and home department. These are included in every chat request so the agent can tailor answers to your context.",
    vi: "Đặt vai trò và phòng ban chính của bạn. Thông tin này được gửi kèm mỗi yêu cầu chat để trợ lý điều chỉnh câu trả lời theo ngữ cảnh của bạn.",
  },
  "tutorial.settings.sync.title": {
    en: "Knowledge sync",
    vi: "Đồng bộ tri thức",
  },
  "tutorial.settings.sync.description": {
    en: "Trigger manual sync from Confluence or Google Drive. Use this when the index is pending or documents have been updated.",
    vi: "Kích hoạt đồng bộ thủ công từ Confluence hoặc Google Drive. Dùng khi chỉ mục chưa sẵn sàng hoặc tài liệu đã được cập nhật.",
  },
  "tutorial.admin.welcome.title": {
    en: "Knowledge Sync Admin",
    vi: "Quản trị Đồng bộ Tri thức",
  },
  "tutorial.admin.welcome.description": {
    en: "Trigger Confluence and Drive sync jobs, monitor their status, and view per-department index health from this page.",
    vi: "Kích hoạt job đồng bộ Confluence và Drive, theo dõi trạng thái và xem sức khoẻ chỉ mục theo phòng ban tại đây.",
  },
  "tutorial.admin.cards.title": {
    en: "Index summary",
    vi: "Tóm tắt chỉ mục",
  },
  "tutorial.admin.cards.description": {
    en: "At-a-glance stats: total documents indexed, total chunks, sources synced, and the last update time.",
    vi: "Số liệu tổng quan: tổng tài liệu đã lập chỉ mục, tổng đoạn, nguồn đã đồng bộ và thời gian cập nhật cuối.",
  },
  "tutorial.admin.sources.title": {
    en: "Knowledge sources",
    vi: "Nguồn tri thức",
  },
  "tutorial.admin.sources.description": {
    en: "Per-department sync status table. Shows each Confluence space or Drive folder, page/file count, freshness, and lets you trigger a targeted sync.",
    vi: "Bảng trạng thái đồng bộ theo phòng ban. Hiển thị từng không gian Confluence hoặc thư mục Drive, số trang/file, độ mới và cho phép đồng bộ mục tiêu.",
  },
  "tutorial.admin.jobs.title": {
    en: "Recent sync jobs",
    vi: "Job đồng bộ gần đây",
  },
  "tutorial.admin.jobs.description": {
    en: "Live and historical sync job log. Check status, start time, finish time, and any errors for each job run.",
    vi: "Nhật ký job đồng bộ hiện tại và lịch sử. Kiểm tra trạng thái, thời gian bắt đầu, kết thúc và lỗi của từng lần chạy.",
  },
  tutorialHelp: { en: "Help", vi: "Trợ giúp" },
  tutorialHelpAria: { en: "Help and tutorial", vi: "Trợ giúp và hướng dẫn" },
  tutorialHelpTitle: { en: "Help & tutorial", vi: "Trợ giúp & hướng dẫn" },
  tutorialResponseHelp: { en: "How to read this answer", vi: "Cách đọc câu trả lời này" },
  tutorialResponseHelpAria: { en: "Guide: how to read this answer", vi: "Hướng dẫn đọc câu trả lời" },
  tutorialDismiss: {
    en: "Don't show again on startup",
    vi: "Không hiện lại khi khởi động",
  },
  tutorialNext: { en: "Next", vi: "Tiếp" },
  tutorialBack: { en: "Back", vi: "Quay lại" },
  tutorialDone: { en: "Done", vi: "Xong" },
  tutorialProgress: { en: "{current} / {total}", vi: "{current} / {total}" },
  confidenceHigh: { en: "High", vi: "Cao" },
  confidenceMedium: { en: "Medium", vi: "Trung bình" },
  confidenceLow: { en: "Low", vi: "Thấp" },
  tooltipStatusAnswered: {
    en: "The question was fully answered from indexed documents.",
    vi: "Câu hỏi đã được trả lời đầy đủ từ tài liệu đã lập chỉ mục.",
  },
  tooltipStatusPartial: {
    en: "Some departments had no relevant documentation — answer may be incomplete.",
    vi: "Một số phòng ban không có tài liệu liên quan — câu trả lời có thể chưa đầy đủ.",
  },
  tooltipStatusClarify: {
    en: "Multiple departments could apply. Select one to get a targeted answer.",
    vi: "Câu hỏi liên quan đến nhiều phòng ban. Chọn một phòng ban để nhận câu trả lời chính xác hơn.",
  },
  tooltipStatusRefused: {
    en: "No relevant content found in the indexed documentation.",
    vi: "Không tìm thấy nội dung liên quan trong tài liệu đã lập chỉ mục.",
  },
  tooltipConfidence: {
    en: "Confidence: estimated likelihood the answer is complete and accurate based on retrieved sources.",
    vi: "Độ tin cậy: ước tính khả năng câu trả lời đầy đủ và chính xác dựa trên nguồn truy xuất.",
  },
  tooltipDepartment: {
    en: "Source department for this answer",
    vi: "Phòng ban nguồn cho câu trả lời này",
  },
};

export function syncStateLabel(state: string, locale: Lang): string {
  const key =
    state === "running"
      ? "syncStateRunning"
      : state === "error"
        ? "syncStateError"
        : "syncStateIdle";
  return t(key, locale);
}

export function sourceLabel(source: string, locale: Lang): string {
  if (source === "confluence") return t("sourceConfluence", locale);
  if (source === "gdrive") return t("sourceGdrive", locale);
  return source;
}

export function indexNotReadyMessage(
  locale: Lang,
  autoRoute: boolean,
  departments: Department[],
): string {
  if (!autoRoute && departments.length === 1) {
    return t("indexNotReadyDept", locale, {
      department: departmentLabel(departments[0], locale),
    });
  }
  if (!autoRoute && departments.length > 1) {
    return t("indexNotReadyDepts", locale, {
      departments: departments.map((d) => departmentLabel(d, locale)).join(", "),
    });
  }
  return t("indexNotReadyAuto", locale);
}

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
