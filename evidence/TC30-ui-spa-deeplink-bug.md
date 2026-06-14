# TC30 — UI: SPA deep-link routing bug — black screen on direct navigation

| Field | Value |
|-------|-------|
| **Test ID** | TC30 |
| **Mode** | UI — Browser direct URL navigation |
| **Type** | 🔴 BUG — SPA deep-link routing failure |
| **Verdict** | 🔴 FAIL (bug confirmed) |

---

## 🖱️ UI Interaction

| Step | Action | Observed |
|------|--------|----------|
| 1 | In running app, navigate via `window.location.href = 'http://localhost:5173/chat'` | Black screen |
| 2 | Refresh page at `/chat` URL | Still black screen |
| 3 | Navigate to root `http://localhost:5173/` | App loads normally |
| 4 | App navigation (clicking Chat/Dashboard/Settings) | Works normally |

**Test also applies to:**
- Direct navigation to `/chat/sess-<uuid>` → black screen
- Any SPA route navigated to directly in the browser address bar (not via in-app links)

---

## 📸 Observed UI State

**When navigating directly to `/chat`:**
- Entire page is **solid black** (`#000` background)
- No content rendered
- No React app mounted
- Browser tab title: "Zalopay Knowledge" (JS loaded but React failed to render)
- No console errors visible in preview (React crash silenced)

**When navigating from root (`/`) then clicking Chat in nav:**
- Works perfectly — full app renders

---

## 🔍 Root Cause Analysis

| Aspect | Detail |
|--------|--------|
| **Root cause** | Vite dev server does not fall back to `index.html` for SPA routes — `/chat` returns 404 or empty, React Router cannot mount |
| **Scope** | All direct navigations to `/chat`, `/dashboard`, `/settings`, `/admin`, `/chat/<session-id>` |
| **Workaround** | Always start from root `/` — app works correctly with in-app navigation |
| **Production fix** | Nginx/server config must serve `index.html` for all routes: `try_files $uri /index.html` |
| **Dev server fix** | Add `--base /` and configure `vite.config.ts` with `historyApiFallback: true` (if using vite preview) or use `vite` dev server (already handles SPA routing via internal middleware) |

---

## 📝 Ghi chú

- Vite dev server (`npm run dev`) does NOT reproduce this bug — handles SPA routing via `/@vite/client`
- Bug reproducible when navigating programmatically via `window.location.href` (simulates browser address bar)
- Production deployment must configure web server to serve `index.html` for all paths
- Related: Nginx config in `docker-compose.yml` should include `try_files $uri $uri/ /index.html`
- **Severity:** Medium — không ảnh hưởng đến users navigate qua UI, chỉ ảnh hưởng deep-link sharing
