# Plan: Make TradeStack Solid

> **Status:** Approved — Phase 1 (reversal position bug) IN PROGRESS
> **Date:** 03 Aug 2026 (created late night, to be executed in a later session)
> **Scope:** Code quality, architecture docs, testing, deployment-readiness — the "Priority #1" upgrade for the interview asset.

---

## Why This Plan

TradeStack is the biggest interview asset. Before adding new features, harden it:

1. **Code quality** — remove 47 hardcoded API URLs, de-duplicate the ~85% identical scanners, tighten TypeScript types, improve error handling + logging.
2. **Architecture docs** — README with the architecture summary + diagram.
3. **Testing** — Python unit tests (indicators, scanner logic, cache, db) + Vitest for pure TS logic (state machines, paper-trader math, IST utils).
4. **Deployment-readiness** — clean setup script + env config (Docker is a follow-up).

**Non-goal:** Do NOT change trading strategy behavior. The state machines, entry/exit gates and scanner math stay identical. This is a refactor/hardening pass, not a strategy pass.

---

## Locked-In Decisions (from planning session)

| Decision | Choice | Why |
|---|---|---|
| Deployment approach | **Setup script now, Docker later** | Windows Docker is heavy (WSL2); live-trader WebSocket/SSE behaves oddly in containers. Setup script works today. |
| Scanner refactor depth | **Shared hooks + thin wrappers** | Extract poll/toast/list hooks + shared subcomponents; Continuation/Reversal become thin config wrappers. Lower risk than a full single-component rewrite. |
| Frontend tests | **Vitest + pure logic tests** | Test state machines, paper-trader P&L/sizing math, IST utils, api.ts helpers. Shows testing skill in BOTH stacks. |

---

## Phases

### Phase 0 — Baseline & Guardrails
Before touching anything, verify the project currently works:
- `cd frontend && bun run lint`
- `cd frontend && npx tsc --noEmit`
- `bun run build`
- `bun run dev` then `curl http://localhost:8001/health` → `{"status":"healthy"}`
- Smoke-test: scanner runs, live-trading status endpoint, settings page loads.
- Record current behavior so refactors don't silently break flows.

### Phase 1 — Central API client (`lib/api.ts`) + env config
- Create `frontend/src/lib/api.ts`:
  - `PY_API = process.env.NEXT_PUBLIC_PY_API ?? "http://127.0.0.1:8001"` (works for browser + Next server).
  - Typed helpers `apiGet<T>` / `apiPost<T>` / `apiPut` / `apiDelete` — timeout, non-2xx handling, consistent error messages.
  - Named endpoint groups: `dataApi`, `scannerApi`, `settingsApi`, `stockListApi`, `tradesApi`, `prepApi`, `tokenApi`, `breadthApi`, `instrumentApi`.
- Replace **all 47 hardcoded URL references** across 12 files:
  - `settings/page.tsx:15`, `CacheData.tsx:26`, `ContinuationScanner.tsx:23`, `ReversalScanner.tsx:25`, `TokenDialog.tsx:25`, `StockList.tsx:15`, `MarketBreadth.tsx:11`, `Navbar.tsx:28`, `ScannerSplitPane.tsx:10`
  - `live-trading/live-trading-utils.tsx:5` (PY_API)
  - Server-side: `lib/live-trader/task-utils.ts:1`, `lib/live-trader/paper-trader.ts:3`, `app/api/live/route.ts:6`
- Add `.env.example` with `NEXT_PUBLIC_PY_API`.

### Phase 2 — Tight TypeScript types
- Create `frontend/src/lib/types.ts` as the single source of truth mirroring Python payloads:
  - `ScanResult`, `ReversalResult`, `OperationStatus`, `CacheInfo`, `StockListItem`, `Trade`, `TradeStats`, `CapitalStats`, `SettingsRow`, `BreadthRow`, `InstrumentKeysResponse`.
- Kill `any` in: scanners (row maps), `StockList`, `CacheData`, `ScannerSplitPane` (`chartCacheRef`), `LiveTrading`, `paper-trader.ts` (`TradableStock` duck-typed contract).
- Move `ScanResult` / `ReversalResult` out of `AppStateContext.tsx` into `types.ts` and re-import.
- Type the config build in `app/api/live/route.ts` (`loadConfigFromPython` currently uses `Record<string,string>`).
- Goal: `npx tsc --noEmit` passes with minimal `any` (only the SDK `.d.ts` structural types remain).

### Phase 3 — De-duplicate scanners + shared UI
- Extract shared hooks (currently duplicated):
  - `useToastStack` — duplicated 5× (CacheData, both scanners, StockList, LiveTrading).
  - `usePollOperation` — the 1s/2s status poll loop (scanners, CacheData, MarketBreadth).
  - `useSavedList(listType)` — stock-list add/remove toggle.
- Build `ScannerBase` driven by a strategy config object: localStorage prefix, accent color, API endpoint, stock-list type, table columns, CSV header, filter definitions.
- `ContinuationScanner` (~446 lines) and `ReversalScanner` (~430 lines) become thin config wrappers (~60 lines each).
- Centralize `cardSx` gradient, toast positioning, theme hex colors.

### Phase 4 — Python tests (pytest)
- Add `pytest` to `backend/requirements.txt` (dev dependency).
- Tests live in root `tests/` per AGENTS.md. Run from backend venv:
  ```
  cd backend
  .\venv\Scripts\python -m pytest ..\tests -q
  ```
- `tests/conftest.py`:
  - Fixture for a **temp SQLite DB** — needs a `DB_PATH` override hook added to `backend/src/db.py` (currently module-level constant).
  - Fixture for a **temp cache dir** (`CacheManager` already accepts `cache_dir`).
- Test files:
  - `test_indicators.py` — SMA, ADR%, MA-angle, price change, high/low distance vs hand-computed values.
  - `test_scanner.py` — synthetic OHLCV DataFrames: 3-phase continuation hit/miss, reversal decline detection + `_check_pattern_logic`, base filters (price range, ADR, liquidity).
  - `test_cache_manager.py` — save/load/update/merge idempotency, cache-index upsert.
  - `test_db.py` — settings CRUD, stock-list CRUD, trade-log P&L auto-calculation.
  - (Optional) `test_server.py` — FastAPI TestClient endpoint smoke tests.

### Phase 5 — Python logging + error handling
- Central logging config (console + file in `data/logs/`).
- Request middleware for access logs; consistent error response shape.
- Ensure background operations never get stuck in `status: "running"` on exception (audit `server.py` background task wrappers).

### Phase 6 — Frontend robustness
- React `ErrorBoundary` wrapping pages.
- `logger` util (dev console; optionally forwarded to backend).
- Unified error surfacing from `api.ts`.
- Structured live-trader logs with severity (keep SSE push via `/api/live/events`).

### Phase 7 — Architecture docs + README
- Rewrite root `README.md` with:
  - Cleaned architecture summary (tri-partite: Next.js UI / Node live trader / Python data microservice / SQLite).
  - **Mermaid diagram** (renders on GitHub) + ASCII fallback.
  - Tech-stack table with "why" column.
  - Run + test commands.
  - End-to-end data flow (scanner → stock list → pre-market → live trader → trade log).
- Update `AGENTS.md` with new lint/test commands.

### Phase 8 — Deployment readiness (setup script)
- `setup.ps1` + `setup.sh`:
  - `bun install` (root + frontend).
  - Python venv + `pip install -r requirements.txt`.
  - Copy `data/complete.csv.gz` (Upstox instrument mapping) if present in old project.
  - Seed DB / cache index.
- `.env.example` + clean setup instructions in README.
- **Docker** (`Dockerfile.frontend`, `Dockerfile.backend`, `docker-compose.yml`) = follow-up task, NOT this pass.

### Phase 9 — Housekeeping sweep
- Remove dead code: `StarBorder.tsx` (imported nowhere).
- Dedupe `secondsUntilIST` (live-trading-utils.tsx + task-utils.ts), `StatusDot`, `cardSx`.
- Resolve unused `trailingSlThreshold` config — either remove from config or document as intentionally unimplemented. **No behavior change.**
- Add root-level test/lint scripts to `package.json` for convenience.

### Phase 10 — Bug fix: Reversal "max positions filled" premature rejection (DONE 06 Aug 26)
**Symptom (user-reported):** Reversal mode, `maxPositions = 2`. 1 trade entered → 1 slot still free, but a 2nd candidate showed "max positions filled" in the reject list. Old code never did this — `active_positions` only incremented when a trade **actually triggered** (`old-legacy-code/.../reversal_monitor.py:_execute_trades`).

**Root cause:** `frontend/src/lib/live-trader/index.ts` start() called `selectStocks()` **once at ENTRY_TIME** (`stock-monitor.ts:145`). It ranked candidates by priority and put everyone beyond `maxPositions` into `notSelected`, then **unsubscribed them from the WebSocket feed permanently** with the reason "Not selected (max positions filled)" — *before any position was actually filled*. Result: if a "selected" stock never triggered entry, its slot stayed empty because the backup had already been killed. The reject reason was also a lie — it was rank-based, not occupancy-based.

**Fix applied (`index.ts:268-278`):** `notSelected` stocks are no longer rejected/unsubscribed at selection time. They stay subscribed as **standby** candidates. The real cap is enforced dynamically at entry time by `checkAndUnsubscribeAfterPositionsFilled()` (`reversal/integration.ts:90`) which only fires when `enteredCount >= maxPositions`. This matches old-code behavior exactly — the limit is about **actual filled positions**, not pre-selected rank.

**Verified:** `npx tsc --noEmit` clean. No trading gates touched (entry/exit conditions identical).

### Phase 11 — Cross-PC Deployment: Docker + Desktop shortcut (PLANNED)
**Goal:** TradeStack should run on ANY PC (Linux/Mac/Windows) with zero manual dependency install, plus a one-click desktop launch. This is a dedicated requirement added 06 Aug 26 — separate from the Phase 8 setup-script work.

**Why Docker:** The user's other PC may not have Python, Node, or bun. Docker bundles everything. (Phase 8's `setup.ps1`/`setup.sh` remains the *native* path; Docker is the *portable* path — both are valuable, and the choice between them is documented in the table below.)

| Concern | Native (Phase 8) | Docker (Phase 11) |
|---|---|---|
| Other PC needs | Python + Node + bun installed | Only Docker |
| Update distribution | Copy folder + re-install deps | Re-export image / git pull + rebuild |
| Windows Docker cost | — | Heavy (WSL2), SSE/WS inside containers behaved oddly per earlier research |
| Fresh-data bootstrapping | Works | Works — `data/` is a bind-mount volume |

**Phase 11 sub-tasks:**
1. **Centralize API URL first (prerequisite)** — 13 files hardcode `http://127.0.0.1:8001`. Create `frontend/src/lib/api.ts` with `PY_API = process.env.NEXT_PUBLIC_PY_API ?? "http://127.0.0.1:8001"`; replace all references (this is already Phase 1 of this doc — do it here first). Docker's frontend container talks to the backend container by service name, not localhost.
2. **`Dockerfile.backend`** — `python:3.11-slim`, copy `backend/`, `pip install -r requirements.txt`, run `uvicorn server:app --host 0.0.0.0 --port 8001`.
3. **`Dockerfile.frontend`** — `oven/bun:1`, copy `frontend/`, `bun install`, `bun run build`, run `next start -p 3000`.
4. **`docker-compose.yml`** — `backend` + `frontend` services, shared `./data:/app/data` bind-mount (settings.db + cache persist across rebuilds), `NEXT_PUBLIC_PY_API=http://localhost:8001` baked at build so the **browser** can reach the backend from the host.
5. **Update CORS in `backend/server.py`** — currently `allow_origins=["http://localhost:3000"]` only. Docker frontend origin is still `http://localhost:3000` from the browser's perspective (host port mapping), so CORS likely OK — but verify; add `http://127.0.0.1:3000` defensively.
6. **Startup scripts + desktop shortcut:**
   - `start.bat` (Windows) + `start.sh` (Linux/Mac): check Docker → `docker compose up -d` → poll `http://localhost:8001/health` until healthy → `start http://localhost:3000` (Windows) / `xdg-open` (Linux) → `docker compose logs -f`.
   - `install-shortcut.bat`: creates a Desktop `.lnk` pointing at `start.bat` (via PowerShell `WScript.Shell`). Double-click → backend + frontend start → browser opens automatically.
   - `stop.bat` / `stop.sh`: `docker compose down`.
7. **`data/complete.csv.gz` strategy (fresh setup):** this file (8635 NSE instrument mappings) is gitignored but REQUIRED for Upstox download. Include it in the Docker image via a `.dockerignore` override (force-copy from a known location) OR instruct first-run to copy it into the mounted `data/` volume. **Decision needed at execution time** — image-include makes the image self-contained (~5MB) and is the recommended default.
8. **Image export/import for offline PC2 (demo/interview path):** `docker save tradestack-backend tradestack-frontend -o tradestack-images.tar` → copy tar via USB → on PC2 `docker load -i tradestack-images.tar` → `docker compose up`. Zero install beyond Docker Desktop. Best for demos because PC2 never needs to rebuild.
9. **Docs:** add "Run on another PC" section to README; note `data/` persists but cache must be re-downloaded on a truly fresh machine (via the Download Data button + Upstox token).

**Files created (Phase 11):** `frontend/src/lib/api.ts`, `Dockerfile.backend`, `Dockerfile.frontend`, `docker-compose.yml`, `start.bat`, `start.sh`, `stop.bat`, `stop.sh`, `install-shortcut.bat`, `.env.example`. Modified: 13 frontend files (URL swap), `backend/server.py` (CORS).

### Frontend tests (Vitest)
- Add `vitest` + config to `frontend/`.
- Test pure logic only (no DOM needed where possible):
  - Continuation + reversal **state machines** (entry gates, SL exits, transitions).
  - **Paper-trader** P&L / risk-based sizing math.
  - **IST utils** (`secondsUntilIST`, `sleepUntilIST`, time math).
  - **api.ts** helper error handling.

---

## Verification (run after every phase)

```powershell
# Frontend
cd frontend
bun run lint
npx tsc --noEmit
bun test            # after Vitest is added
bun run build

# Backend
cd backend
.\venv\Scripts\python -m pytest ..\tests -q

# Smoke test
bun run dev
curl http://localhost:8001/health   # → {"status":"healthy"}
```

---

## Current-State Findings (reference for the working session)

- **47 hardcoded** `http://127.0.0.1:8001` references across 12 frontend files.
- **Scanners are ~85% duplicate** (~876 combined lines), near-clones of each other.
- **Toast stack manager duplicated 5×**.
- **`TokenDialog` vs `TokenTab`** — two implementations of the same token-validate flow.
- **No tests exist yet** — root `tests/` is empty; no Vitest/Jest setup.
- **No Dockerfile**, no setup script, no `.env.example`.
- **`tsconfig` is `strict: true`** already — good baseline; the goal is to stop `any` leaks.
- **db.py `DB_PATH` is module-level** — needs an override hook for testability.
- Dead code: `StarBorder.tsx`. Unused config: `trailingSlThreshold` (not wired into exits).
- **RESOLVED bug (Phase 10, 06 Aug 26):** reversal "max positions filled" premature rejection. `selectStocks()` was pre-emptively unsubscribing backup candidates by rank before positions actually filled, leaving slots empty and showing a false "max positions filled". Fixed in `index.ts:268` — backups stay subscribed as standby; real cap enforced by `checkAndUnsubscribeAfterPositionsFilled()`.

---

## Notes for the Executor (agent)

- **Never change trading behavior.** State machines, scanner math, entry/exit gates must produce identical results. If a refactor *requires* a behavior change, stop and ask.
- Follow the existing conventions in `AGENTS.md`: small focused modules, config in DB not source, frontend follows backend.
- Do Phase 0 first; if the baseline build already fails, fix that before refactoring.
- Commit in logical chunks (one per phase) rather than one giant commit.
