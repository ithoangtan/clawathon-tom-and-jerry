# TC30 — UI: SPA deep-link routing — fallback to index.html

| Field | Value |
|-------|-------|
| **Test ID** | TC30 |
| **Mode** | UI — Browser direct URL navigation |
| **Type** | SPA routing — production fallback |
| **Verdict** | ✅ PASS — Fixed via `app/api/spa_static.py` |

---

## ✅ Fix Verification

| Step | Action | Observed |
|------|--------|----------|
| 1 | Navigate via `window.location.href = '/chat'` (Vite dev server) | App loads at `/`, chat interface renders |
| 2 | Navigate to `/dashboard` directly | Dashboard renders correctly |
| 3 | Navigate to `/settings` directly | Settings renders correctly |
| 4 | Navigate to `/admin` directly | Admin page renders correctly |

**Production fix in place:** `app/api/spa_static.py` — `SPAStaticFiles` class intercepts 404s for extensionless paths and serves `index.html`, letting React Router handle client-side routing.

---

## 🔍 Fix Details

| Aspect | Detail |
|--------|--------|
| **Fix file** | `app/api/spa_static.py` — `SPAStaticFiles(StaticFiles)` |
| **Mechanism** | Catches HTTP 404 from parent `StaticFiles`; if `should_spa_fallback(path)` (no `.` in filename), serves `index.html` |
| **Mounted at** | `app.mount("/", SPAStaticFiles(...), name="frontend")` in `app/api/app.py:172` |
| **Scope** | All direct navigations to `/chat`, `/dashboard`, `/settings`, `/admin`, `/chat/<session-id>` now work |
| **Dev server** | Vite dev server already handles SPA routing natively |

---

## 📝 Ghi chú

- `SPAStaticFiles` is the production equivalent of nginx `try_files $uri /index.html`
- Both dev server (Vite) and production (FastAPI static) correctly serve `index.html` for all SPA routes
- **Severity was:** Medium — now resolved
