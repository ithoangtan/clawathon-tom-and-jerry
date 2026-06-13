import { describe, expect, it } from "vitest";
import { t } from "./i18n";

describe("i18n", () => {
  it("returns English strings for en locale", () => {
    expect(t("appTitle", "en")).toBe("ZaloPay Knowledge");
    expect(t("send", "en")).toBe("Send");
    expect(t("citations", "en")).toBe("Sources");
  });

  it("returns Vietnamese strings for vi locale", () => {
    expect(t("appTitle", "vi")).toBe("Tri thức ZaloPay");
    expect(t("send", "vi")).toBe("Gửi");
    expect(t("citations", "vi")).toBe("Nguồn tham khảo");
  });

  it("returns key when string is missing", () => {
    expect(t("nonexistentKey" as "appTitle", "en")).toBe("nonexistentKey");
  });

  it("covers status and error strings", () => {
    expect(t("statusAnswered", "en")).toBe("Answered");
    expect(t("statusRefused", "vi")).toBe("Không có thông tin trong tài liệu");
    expect(t("refusalTitle", "en")).toBe("Not covered in the docs");
    expect(t("errorTimeout", "en")).toBe("Request timed out. Try a narrower question.");
    expect(t("deprecatedWarning", "vi")).toBe("Tài liệu đã lỗi thời");
  });

  it("covers access denial and locale-specific chat copy", () => {
    expect(t("accessDeniedTitle", "en")).toBe("Access denied");
    expect(t("statusAccessDenied", "vi")).toBe("Không có quyền truy cập");
    expect(t("emptyChatTitle", "vi")).toBe("Tôi có thể giúp gì?");
    expect(t("indexNotReady", "en")).toMatch(/not synced/i);
  });
});
