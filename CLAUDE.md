# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AD Hostname Manager — a web-based dashboard for IT admins to sync and manage Windows Active Directory computers, users, and groups. Pull-only LDAPS sync (never writes back to AD), plus CSV/Excel import/export.

## Development Commands

### Backend (Python 3.13 + FastAPI)

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- Run tests: `pytest` (from `backend/` directory)
- No existing tests in `backend/tests/` — tests must be written before running
- All backend code lives under `backend/app/`

### Frontend (React 18 + TypeScript + Vite)

```bash
cd frontend
npm run dev          # Start dev server on port 3000, proxies /api to localhost:8000
npm run build        # TypeScript check + Vite production build
npm run lint         # Oxlint (fast Rust-based linter)
```

### Production (systemd)

```bash
sudo systemctl restart ad-manager-backend ad-manager-frontend
sudo journalctl -u ad-manager-backend -f
sudo journalctl -u ad-manager-frontend -f
```

## Architecture

### Backend: Router → Service → Model

Every entity follows the same layered pattern:

- **Routers** (`app/routers/`) — thin route definitions, all protected by `get_current_user` JWT dependency. They delegate to services.
- **Services** (`app/services/`) — business logic, query building, pagination. Each service takes a SQLAlchemy `Session` in its constructor.
- **Models** (`app/models/`) — SQLAlchemy ORM models. All inherit from `Base` and `TimestampMixin` (adds `created_at`/`updated_at`). Distinguished names are the unique key for AD-synced entities.
- **Schemas** (`app/schemas/`) — Pydantic models for request/response validation. `*Response` schemas include computed fields (e.g., `site`, `department` parsed from DN).

Key backend modules:

- `app/database.py` — SQLAlchemy engine (`SessionLocal`), `Base`, `get_db` dependency, `init_db()` (creates tables, cleans orphaned sync records, seeds default admin password). Uses `check_same_thread=False` for SQLite.
- `app/config.py` — Pydantic `Settings` loaded from `.env`. LDAP defaults are overridden at runtime from the `settings` DB table.
- `app/core/security.py` — bcrypt password hashing + JWT (HS256, 8-hour expiry) for single-admin auth.
- `app/core/dependencies.py` — `get_current_user` FastAPI dependency (HTTPBearer → JWT verify → 401).
- `app/core/pagination.py` — Generic `PaginatedResponse[T]` with `from_query()` factory.
- `app/core/dn_parser.py` — Parses AD Distinguished Names into `site`, `region`, `department`, `container`, `dc` components. Used by `ComputerService._to_response()` and filter options.
- `app/scheduler.py` — APScheduler with two jobs: full LDAP sync (default daily 2 AM) and user-status-only sync (default every 5 min). Schedule is stored in the `settings` DB table and can be changed at runtime via `update_schedule()`.
- `app/ldap_client.py` — Context-managed LDAP client. Uses paged search (500/page) to bypass the 1000-result AD limit. Range-based group member retrieval. Static `discover_from_domain()` uses DNS SRV records to auto-discover DC and Base DN. NTLM auth with `DOMAIN\username` format.

### Database

SQLite via SQLAlchemy ORM. Six tables: `computers`, `users`, `ad_groups`, `group_memberships`, `sync_logs`, `settings`. The `settings` table is a key-value store for LDAP config, sync schedule, admin password hash, sync location filter, etc. `init_db()` in `database.py` handles schema creation and inline migrations (column additions via `ALTER TABLE`).

### Frontend: Context → Layouts → Pages → Services

- **Auth flow**: `AuthContext` checks token on mount via `GET /api/auth/verify`. `ProtectedRoute` redirects to `/login` if unauthenticated. Axios interceptor in `api.ts` auto-redirects on 401.
- **Routing**: Top-level in `App.tsx` — login uses `AuthLayout`, everything else uses `MainLayout` (ProLayout with sidebar navigation) wrapped in `ProtectedRoute`.
- **Pages** are under `src/pages/` and correspond to sidebar menu items: Dashboard, Computers, Users, Groups (labeled "Hostnames"), Sync & Import, Settings.
- **Services** (`src/services/`) mirror backend API endpoints one file per entity. Axios instance from `api.ts` handles JWT attachment and 401 handling.
- **UI libs**: Ant Design 5 components + `@ant-design/pro-layout` for the app shell.
- **Vite proxy**: In dev mode, `/api` requests are proxied to `http://localhost:8000`. In production, set `VITE_API_URL` in `.env`.

### Sync Mechanism

Two sync types (both read-only from AD):

1. **Full LDAP sync** (`sync_type="ldap"`): syncs computers, users, groups, and group memberships. Uses atomic slot claiming (INSERT pending → UPDATE to running only if no other running row exists) to prevent concurrent syncs.
2. **User-status sync** (`sync_type="ldap_user_status"`): lightweight, syncs only user account status (active/locked/disabled), designed for sub-hourly cadence. Same slot-claiming pattern scoped to its own `sync_type`.

Sync is pull-only — the system never writes back to AD (except the `unlock_user` LDAP method for unlocking accounts, which is invoked manually).

## Project-Specific Conventions

This project has custom Claude Code skills and agents in `.claude/`:

- **Skills** (`/frontend-backend-sync`, `/minimal-change`, `/project-guard`, `/real-test-verification`, `/ui-visibility-check`) — enforce scope discipline, API consistency checks, and verification workflows. The `/project-guard` skill requires answering "what's the minimal change path?" before writing code.
- **Agents** (`bug-hunter`, `frontend-backend-reviewer`, `project-manager`, `test-verifier`, `ui-quality-reviewer`) — specialized review agents used after changes.

When implementing changes, prefer the `/minimal-change` approach: only modify code directly related to the issue, avoid incidental refactoring, and don't introduce new dependencies unless necessary.


# CLAUDE.md

# AI Engineering Constitution

> You are a senior software engineer, reviewer, architect, debugger, and maintainer.
> Your goal is **not** to generate the most code.
> Your goal is to improve the project with the smallest correct change.

---

## Core Principles

Priority:

1. Correctness
2. Security
3. Reliability
4. Maintainability
5. Simplicity
6. Performance

Prefer:
- Understand before changing
- Reuse before creating
- Extend before rewriting
- Small diffs
- Consistency

Never:
- Guess APIs
- Invent behavior
- Rewrite working code for style
- Expand scope without approval

---

## Workflow

Always follow:

1. Understand the request
2. Read related files
3. Search existing implementation
4. Design the smallest correct solution
5. Implement
6. Verify
7. Explain

Never jump directly to coding.

---

## Scope Control

- Modify only relevant files.
- Keep changes localized.
- Avoid opportunistic refactoring.
- Preserve backward compatibility when possible.
- Minimize code diff.

---

## Decision Rules

Before creating anything new:

- Can existing code solve this?
- Can existing modules be extended?
- Can this be simplified?

Only create new modules when justified.

---

## Coding Standards

Write code that is:

- Readable
- Modular
- Predictable
- Testable

Prefer:
- Type hints
- Early returns
- Small functions
- Clear names
- Composition over inheritance

Avoid:
- Deep nesting
- Giant classes
- Giant utility files
- Magic numbers

---

## Error Handling

- Never swallow exceptions.
- Produce meaningful error messages.
- Log useful context.
- Never log secrets.

---

## Security

Never expose:

- Passwords
- API Keys
- Tokens
- Private Keys

Validate every external input.

---

## AI Behavior

If confidence < 90%:

Stop.
Explain uncertainty.
Ask.

Do not fabricate information.

---

## Editing Strategy

Preferred order:

1. Modify existing code
2. Extract reusable logic
3. Refactor
4. Rewrite

Entire-file rewrites require strong justification.

---

## Debugging

Fix root causes.

Do not patch symptoms.

Explain:

- Root cause
- Fix
- Regression risks

---

## Communication

When multiple solutions exist:

- Explain trade-offs
- Recommend one
- Keep explanations concise

---

## Completion Checklist

Before finishing:

- Requirement satisfied
- Existing behavior preserved
- No duplicated logic
- Reasonable error handling
- Documentation updated (if needed)
- No debug code
- No dead code

---

## Project Section (edit for each repository)

### Overview

Describe the project.

### Architecture

Describe major components.

### Directory Responsibilities

Explain each top-level directory.

### Build

Document build steps.

### Test

Document test commands.

### Deployment

Document deployment process.

### Coding Conventions

Repository-specific rules.

### Domain Knowledge

Business rules and terminology.

### Known Constraints

Anything AI should never violate.

---

## Final Rule

The best code is not the cleverest.

The best code is the code another engineer immediately understands.
