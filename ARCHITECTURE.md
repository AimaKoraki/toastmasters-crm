# Technical Architecture & Guidelines
## APIIT Kandy Club CRM

---

### 1. Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| **Language** | Python 3.11+ | Running on local venv |
| **Web Framework** | FastAPI | ASGI, async-ready |
| **Authentication** | Starlette `SessionMiddleware` + `itsdangerous` | Shared Exco passkey stored in `.env`; HTTP-only session cookie |
| **Template Engine** | Jinja2 | Returns full pages and HTMX partials |
| **Frontend** | HTMX (v1.9+ via CDN) + Tailwind CSS (via CDN) | No build step required |
| **Icons** | Lucide Icons (via CDN) | Dynamic DOM re-init via `htmx:afterSettle` |
| **Database** | Supabase (PostgreSQL) | Official `supabase-py` SDK |
| **Static Files** | FastAPI `StaticFiles` | Served from `app/static/` |

---

### 2. Project Directory Structure

```text
toastmasters-crm/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app, session middleware, root dashboard aggregation
│   ├── config.py                 # Environment variables & Supabase client initialization
│   ├── dependencies.py           # Session authentication dependency (get_current_user)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py               # [✅] GET /login, POST /login, GET /logout
│   │   ├── prospects.py          # [⚠️] GET /prospects, POST /prospects, [⏳] POST /prospects/{id}/stage
│   │   ├── meetings.py           # [⚠️] GET /meetings, POST /meetings, [⏳] POST /attendance
│   │   ├── roles.py              # [⚠️] GET /roles, POST /roles/assign, [⏳] GET /roles/matrix
│   │   ├── members.py            # [⏳] GET /members, POST /members, GET /members/{id} (Upcoming)
│   │   └── reports.py            # [⏳] GET /reports, GET /reports/export (Upcoming)
│   ├── templates/
│   │   ├── base.html             # Shell layout (sidebar, topbar, HTMX hook, Lucide re-init)
│   │   ├── login.html            # Branded split-screen passkey login page
│   │   ├── index.html            # Executive dashboard (metrics, upcoming meeting, feed, pipeline)
│   │   └── partials/
│   │       ├── prospects.html    # [✅] HTMX target: guest pipeline table & add-guest modal
│   │       ├── meetings.html     # [✅] HTMX target: meetings list & add-meeting modal
│   │       ├── roles.html        # [⚠️] HTMX target: role assignment modal & matrix placeholder
│   │       ├── members.html      # [⏳] HTMX target: member directory with status filters (Upcoming)
│   │       └── attendance.html   # [⏳] HTMX target: batch meeting check-in table (Upcoming)
│   └── static/
│       └── css/
│           └── style.css         # Design system tokens & overrides on top of Tailwind
├── .env                          # Secret keys & Supabase credentials (gitignored)
├── .env.example                  # Template for required environment variables
├── requirements.txt              # Python dependencies
├── SCHEMA.sql                    # PostgreSQL schema definition (Supabase)
├── PRD.md                        # Product Requirements Document
├── ARCHITECTURE.md               # Technical architecture & guidelines (This file)
├── AGENT.md                      # AI agent operating directives & constraints
├── AGENT_INSTRUCTIONS.md         # Active build roadmap and execution checklist
└── .tokensave/                   # Agent context memory and checkpoint logs
```

---

### 3. Authentication & Session Flow

```
Browser                     FastAPI (main.py)               Supabase
  │                               │                              │
  │── GET /  ────────────────────>│                              │
  │          SessionMiddleware checks session cookie             │
  │          If no session → redirect to /login                 │
  │          If HTMX request → HX-Redirect: /login               │
  │                               │                              │
  │── POST /login (passkey) ─────>│                              │
  │          Compare against EXCO_PASSKEY env var               │
  │          On match → set session["authenticated"] = True     │
  │          Redirect to / (303 See Other)                       │
  │                               │                              │
  │── GET / (authenticated) ─────>│── Supabase queries ────────>│
  │                               │<── Aggregated data ─────────│
  │<── 200 index.html ────────────│                              │
```

- **Authentication Guard:** `get_current_user` in `dependencies.py` checks `request.session.get("authenticated")`. Unauthenticated standard requests receive a `303 See Other` redirect to `/login`; unauthenticated HTMX requests receive `401 Unauthorized` with `HX-Redirect: /login`.
- **Session Logout:** `GET /logout` clears the session dictionary and redirects to `/login`.

---

### 4. Data Architecture (Supabase / PostgreSQL)

#### Enum Types
| Enum | Values |
|---|---|
| `member_status` | `'Prospect'`, `'Active'`, `'Inactive'`, `'Alumni'` |
| `prospect_stage` | `'1st Visit'`, `'2nd Visit'`, `'Form Sent'`, `'Payment Pending'`, `'Onboarded'` |
| `attendance_status` | `'Present'`, `'Absent'`, `'Excused'`, `'Guest'` |

#### Tables

| Table | Purpose | Key Relationships & Constraints |
|---|---|---|
| `members` | Central record for all contacts (guests → prospects → active members) | `id` (PK), `email` (UNIQUE), `status` (`member_status`) |
| `prospect_logs` | Append-only pipeline stage history per member | `member_id → members.id` (ON DELETE CASCADE), `stage` (`prospect_stage`) |
| `meetings` | Meeting metadata (number, date, theme) | `id` (PK), `meeting_number` (INT UNIQUE), `meeting_date` (DATE) |
| `role_catalog` | Master directory of club roles | `id` (PK), `role_name` (UNIQUE), `category` |
| `role_assignments` | Links members to roles per meeting (multi-role support) | `meeting_id`, `member_id`, `role_id`; `UNIQUE(meeting_id, member_id, role_id)` |
| `attendance` | Per-meeting check-in record per member | `meeting_id`, `member_id`; `UNIQUE(meeting_id, member_id)` |

#### Data Flow & Aggregation Decisions
- **Single Contact Table (`members`):** All people exist in `members`. A person starts with `status = 'Prospect'`, and transitions to `'Active'` upon onboarding.
- **Append-Only Pipeline History (`prospect_logs`):** Every stage transition adds a row. The latest row sorted by `created_at DESC` represents the active stage.
- **Multi-Role Assignment:** Because the unique constraint is composite on `(meeting_id, member_id, role_id)`, a single member can hold multiple distinct roles in the same meeting (e.g. Timer and Speech Evaluator).

---

### 5. Request & Response Patterns

#### Full-Page Navigation
- The root `/` route queries Supabase in sequence to assemble metric counters, upcoming meeting details, recent activity logs, and pipeline preview data before returning `index.html`.

#### HTMX Partial Rendering
- Sidebar navigation and module switches issue `hx-get` targeting `#main-content`.
- Modal forms issue `hx-post` targeting `#main-content` and return an updated table partial from `app/templates/partials/`.
- All HTMX endpoints return Jinja2 `TemplateResponse` referencing files inside `app/templates/partials/`.

#### Out-of-Band (OOB) Metric Updates
- Future mutations (such as adding a guest or marking attendance) will return `hx-swap-oob="true"` blocks targeting `#stat-members`, `#stat-guests`, `#stat-prospects`, and `#stat-attendance` to keep dashboard numbers synchronized without a full reload.

---

### 6. Router Endpoints Reference & Status

#### `auth.py`
| Method | Path | Status | Description |
|---|---|---|---|
| `GET` | `/login` | ✅ Complete | Render login page or redirect if authenticated |
| `POST` | `/login` | ✅ Complete | Validate passkey, set session, redirect to `/` |
| `GET` | `/logout` | ✅ Complete | Clear session cookie, redirect to `/login` |

#### `prospects.py`
| Method | Path | Status | Description |
|---|---|---|---|
| `GET` | `/prospects` | ✅ Complete | Render guest pipeline table partial |
| `POST` | `/prospects` | ✅ Complete | Insert guest into `members` & add initial stage log |
| `POST` | `/prospects/{id}/stage` | ✅ Complete | Progress prospect stage, append notes, auto-onboard to `Active` |
| `GET` | `/prospects/{id}/history` | ✅ Complete | Render stage timeline history modal partial |
| `GET` | `/prospects/new` | ✅ Complete | Render add-guest modal partial (for quick actions) |

#### `meetings.py`
| Method | Path | Status | Description |
|---|---|---|---|
| `GET` | `/meetings` | ✅ Complete | Render meetings list partial with attendance stats |
| `POST` | `/meetings` | ✅ Complete | Create new meeting record |
| `GET` | `/meetings/{id}/attendance` | ✅ Complete | Render batch attendance check-in matrix view |
| `GET` | `/meetings/attendance` | ✅ Complete | Quick action helper for latest meeting attendance |
| `GET` | `/meetings/new` | ✅ Complete | Render standalone Add Meeting modal partial |
| `GET` | `/meetings/live` | ✅ Complete | Render Live Meeting Mode console partial |
| `POST` | `/attendance` | ✅ Complete | Batch-record attendance statuses for a meeting |

#### `roles.py`
| Method | Path | Status | Description |
|---|---|---|---|
| `GET` | `/roles` | ✅ Complete | Render dynamic role history frequency matrix partial |
| `POST` | `/roles/assign` | ✅ Complete | Assign role to member (multi-role supported) |
| `GET` | `/roles/assign` | ✅ Complete | Render standalone assign role modal partial |
| `GET` | `/roles/member/{id}/history` | ✅ Complete | Render member role participation timeline modal |

#### `reports.py`
| Method | Path | Status | Description |
|---|---|---|---|
| `GET` | `/reports` | ✅ Complete | Render reports overview page partial |
| `GET` | `/reports/export` | ✅ Complete | Render standalone export report modal partial |
| `GET` | `/reports/download` | ✅ Complete | Stream CSV export of attendance, guests, roles, or summary |

#### `members.py` *(Upcoming)*
| Method | Path | Status | Description |
|---|---|---|---|
| `GET` | `/members` | ⏳ Pending | Render member directory partial with status filter |
| `POST` | `/members` | ⏳ Pending | Add / edit member record |
| `GET` | `/members/{id}` | ⏳ Pending | Member detail & Pathways profile view |

---

### 7. UI/UX Design System Tokens

#### Brand Palette
| Token | Hex Value | Purpose |
|---|---|---|
| Deep Slate | `#0f172a` / `#1e293b` | Sidebar, dark panels, headers |
| Bright Blue | `#2563eb` | Primary buttons (`.btn-primary`), active nav indicators |
| Bright Blue Hover | `#1d4ed8` | Button hover state |
| Amber Accent | `#fbbf24` | Underline accents (`.gold-underline`), badges |
| Light Neutral | `#F7F9FA` | Body page background |
| Pure White | `#FFFFFF` | Card surfaces (`.card`) |
| Border Slate | `#E5E9E8` | Card borders and divider lines |

#### Card & Component Rules
- **Cards:** `.card` with `border-radius: 14px`, `box-shadow: 0 6px 24px rgba(0,0,0,0.05)`, border `1px solid #E5E9E8`.
- **Buttons:** `.btn-primary` with bright blue background, white text, `8px` rounded corners, and subtle hover elevation.
- **Empty States:** Renders standard empty card with emoji (`📭`, `📅`, `🎭`), friendly copy, and primary action button.

---

### 8. Environment Variables

| Variable | Required | Description | Current Status |
|---|---|---|---|
| `EXCO_PASSKEY` | ✅ | Shared passkey for Exco administrative access | Configured in `.env` |
| `SESSION_SECRET` | ✅ | Secret key used by `SessionMiddleware` | Needs dynamic binding in `main.py` |
| `SUPABASE_URL` | ✅ | Supabase project URL (`https://xyz.supabase.co`) | Configured in `.env` |
| `SUPABASE_KEY` | ✅ | Supabase `anon` public key | Configured in `.env` |

---

### 9. Python Dependencies (`requirements.txt`)

- `fastapi` (Web framework)
- `uvicorn` (ASGI web server)
- `jinja2` (Server-side HTML rendering)
- `supabase` (Supabase Python client SDK)
- `python-dotenv` (Environment variable loader)
- `python-multipart` (Form data parsing)
- `itsdangerous` (Session cryptographic signing)

---

### 10. Technical Gap Analysis & Audit Findings

During the codebase audit, the following technical gaps were documented:

1. **Dashboard Quick Action Handlers:**
   - The Quick Action buttons on `index.html` use `hx-get` targeting `/prospects/new`, `/meetings/attendance`, `/roles/assign`, `/meetings/live`, and `/reports/export`. These routes either do not exist or expect `POST` methods.
   - *Action:* Create lightweight modal endpoints or unify them with a global modal trigger.

2. **Prospect Stage Workflow:**
   - The UI displays pipeline stages (`1st Visit`, `2nd Visit`, `Form Sent`, `Payment Pending`, `Onboarded`), but there is no handler in `prospects.py` to transition an existing prospect between stages.
   - *Action:* Implement `POST /prospects/{id}/stage` and wire status-click actions.

3. **Attendance Logging Implementation:**
   - `meetings.py` creates meetings, but attendance recording (`POST /attendance`) and the check-in matrix view are unimplemented.
   - *Action:* Implement batch attendance submission and interactive checkbox check-in view.

4. **Dynamic Role Frequency Matrix:**
   - `roles.py` returns `matrix: []`. The UI shows a table shell with "No role history found".
   - *Action:* Write aggregation query to compute `(member_name, role_name) -> count` across meetings.

5. **Session Secret Environment Binding:**
   - `main.py` uses hardcoded `secret_key="super-secret-exco-key"` instead of `os.getenv("SESSION_SECRET")`.
   - *Action:* Bind `SESSION_SECRET` from `.env` with a secure fallback.

---

### 11. Developer & AI Agent Operating Directives

- **AI Agent Directives:** Refer to [AGENT.md](file:///c:/Users/panth/Documents/toastmasters-crm/AGENT.md) for HTMX protocol rules, UI token constraints, and `.tokensave` context management.
- **Execution Checklist:** Refer to [AGENT_INSTRUCTIONS.md](file:///c:/Users/panth/Documents/toastmasters-crm/AGENT_INSTRUCTIONS.md) for task status and immediate priorities.
- **Checkpoints:** Update `.tokensave` after completing key sub-tasks.
