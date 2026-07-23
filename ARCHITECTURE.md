# Technical Architecture & Guidelines
## APIIT Kandy Toastmasters CRM

---

### 1. Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| **Language** | Python 3.11+ | — |
| **Web Framework** | FastAPI | ASGI, async-ready |
| **Authentication** | Starlette `SessionMiddleware` + `itsdangerous` | Shared Exco passkey stored in `.env`; HTTP-only session cookie |
| **Template Engine** | Jinja2 | Returns full pages and HTMX partials |
| **Frontend** | HTMX (v1.9+ via CDN) + Tailwind CSS (via CDN) | No build step required |
| **Icons** | Lucide Icons (via CDN) | Sidebar & UI icons |
| **Database** | Supabase (PostgreSQL) | `supabase-py` SDK |
| **Static Files** | FastAPI `StaticFiles` | Served from `app/static/` |

---

### 2. Project Directory Structure

```text
toastmasters-crm/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI app, middleware, root dashboard route
│   ├── config.py                 # Env vars & Supabase client initialisation
│   ├── dependencies.py           # Session authentication dependency (get_current_user)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py               # GET /login, POST /login, POST /logout
│   │   ├── prospects.py          # GET /prospects, POST /prospects, POST /prospects/{id}/stage
│   │   ├── meetings.py           # GET /meetings, POST /meetings, POST /attendance
│   │   └── roles.py              # GET /roles, POST /roles, GET /roles/matrix
│   ├── templates/
│   │   ├── base.html             # Layout wrapper (sidebar, topbar, content slot)
│   │   ├── login.html            # Passkey prompt page
│   │   ├── index.html            # Main dashboard (metrics, pipeline table, activity feed)
│   │   └── partials/
│   │       ├── prospects.html    # HTMX target: guest pipeline table
│   │       ├── meetings.html     # HTMX target: meetings & attendance form
│   │       └── roles.html        # HTMX target: role assignment & matrix view
│   └── static/
│       └── css/
│           └── style.css         # Custom overrides on top of Tailwind CDN
├── .env                          # Secret keys & Supabase credentials (gitignored)
├── .env.example                  # Template for required environment variables
├── requirements.txt              # Python dependencies
├── SCHEMA.sql                    # PostgreSQL schema (Supabase)
├── PRD.md                        # Product Requirements Document
├── ARCHITECTURE.md               # This file
└── AGENT_INSTRUCTIONS.md         # Build roadmap for AI agent execution
```

---

### 3. Authentication & Session Flow

```
Browser                     FastAPI (main.py)               Supabase
  │                               │                              │
  │── GET /  ────────────────────>│                              │
  │          SessionMiddleware checks session cookie             │
  │          If no session → redirect to /login                 │
  │                               │                              │
  │── POST /login (passkey) ─────>│                              │
  │          Compare against EXCO_PASSKEY env var               │
  │          On match → set session["authenticated"] = True     │
  │          Redirect to /                                       │
  │                               │                              │
  │── GET / (authenticated) ─────>│── Supabase queries ────────>│
  │                               │<── Aggregated data ─────────│
  │<── 200 index.html ────────────│                              │
```

- **Dependency:** `get_current_user` in `dependencies.py` is injected into all protected routes via `Depends(get_current_user)`.
- **Logout:** `POST /logout` clears the session and redirects to `/login`.

---

### 4. Data Architecture (Supabase / PostgreSQL)

#### Enum Types
| Enum | Values |
|---|---|
| `member_status` | `Prospect`, `Active`, `Inactive`, `Alumni` |
| `prospect_stage` | `1st Visit`, `2nd Visit`, `Form Sent`, `Payment Pending`, `Onboarded` |
| `attendance_status` | `Present`, `Absent`, `Excused`, `Guest` |

#### Tables

| Table | Purpose | Key Relationships |
|---|---|---|
| `members` | Central record for all people (guests → members) | — |
| `prospect_logs` | Pipeline stage history per member | `member_id → members.id` |
| `meetings` | Meeting records (number, date, theme) | — |
| `role_catalog` | Master list of Toastmasters roles | — |
| `role_assignments` | Links members to roles per meeting (multi-role allowed) | `meeting_id`, `member_id`, `role_id`; UNIQUE per trio |
| `attendance` | Per-meeting attendance status per member | `meeting_id`, `member_id`; UNIQUE per pair |

#### Key Design Decisions
- A single `members` table handles all lifecycle stages; `status` (`member_status` enum) drives filtering.
- `prospect_logs` is append-only stage history — the latest row per `member_id` represents the current pipeline stage.
- `role_assignments` allows multiple rows per `(meeting_id, member_id)` with different `role_id` values, supporting combined roles (e.g., Timer + Ah-Counter).
- `UNIQUE(meeting_id, member_id, role_id)` on `role_assignments` prevents duplicate role entries.
- Attendance tracking uses `UNIQUE(meeting_id, member_id)` to prevent double entries.

---

### 5. Request/Response Patterns

#### Full-Page Navigation
- Sidebar links perform standard `GET` requests.
- The root `/` route aggregates all dashboard data in a single handler and renders `index.html`.

#### HTMX Partial Rendering
- Actions within each module (add guest, update stage, record attendance, assign role) use HTMX `hx-post` / `hx-get` targeting a named `<div>` in `index.html`.
- The router handlers return Jinja2 `TemplateResponse` pointing to a file inside `templates/partials/`.

#### Dashboard Data Aggregation (`main.py /`)
The root route performs several Supabase queries in sequence:
1. **Active Members count** — `members` table, `status = Active`
2. **Guest count** — `members` table, `status = Prospect`
3. **Active Prospects count** — latest stage per `member_id` in `prospect_logs`, excluding `Onboarded`
4. **Attendance Rate** — `(Present records / total member-meeting records) * 100`
5. **Upcoming Meeting** — latest row from `meetings`, with TMOD resolved via `role_assignments`
6. **Recent Activity Feed** — latest 5 entries each from `prospect_logs`, `attendance`, and `role_assignments`; merged and sorted by timestamp, trimmed to top 5
7. **Guest Pipeline Table** — `Prospect`-status members with latest `prospect_stage` applied

---

### 6. Router Endpoints Reference

#### `auth.py`
| Method | Path | Description |
|---|---|---|
| `GET` | `/login` | Render login page |
| `POST` | `/login` | Validate passkey, set session, redirect |
| `POST` | `/logout` | Clear session, redirect to `/login` |

#### `prospects.py`
| Method | Path | Description |
|---|---|---|
| `GET` | `/prospects` | Render guest pipeline partial |
| `POST` | `/prospects` | Add new guest/prospect |
| `POST` | `/prospects/{id}/stage` | Update a prospect's pipeline stage |

#### `meetings.py`
| Method | Path | Description |
|---|---|---|
| `GET` | `/meetings` | Render meetings & attendance partial |
| `POST` | `/meetings` | Create a new meeting record |
| `POST` | `/attendance` | Batch-record attendance for a meeting |

#### `roles.py`
| Method | Path | Description |
|---|---|---|
| `GET` | `/roles` | Render role assignment partial |
| `POST` | `/roles` | Assign a role to a member for a meeting |
| `GET` | `/roles/matrix` | Render role frequency matrix view |

---

### 7. UI/UX Design System

#### Brand Palette
| Token | Hex | Usage |
|---|---|---|
| Loyal Navy | `#002B49` / `#004165` | Sidebar background |
| True Maroon | `#772432` | Primary buttons, active nav items |
| Toastmasters Gold | `#F2DF00` | Accent underlines, highlights |
| Light Neutral | `#F7F9FA` | Page background |
| Pure White | `#FFFFFF` | Cards & surfaces |

#### Card Style
- `border-radius: 14px`
- `box-shadow: 0 6px 24px rgba(0,0,0,0.05)`

#### Typography Scale
| Role | Size | Weight |
|---|---|---|
| Page Title | `32px` | Bold (700) |
| Section Title | `20px` | Semibold (600) |
| Table Headers | `13px` | Semibold (600) / Uppercase / `letter-spacing: 0.08em` |
| Body | `15px` | Regular (400) |

#### Status Badge Colours
| Status | Colour |
|---|---|
| Guest / 1st Visit | Sky Blue |
| Prospect (active pipeline) | Amber |
| Member / Onboarded | Emerald Green |

---

### 8. Environment Variables

| Variable | Required | Description |
|---|---|---|
| `EXCO_PASSKEY` | ✅ | Shared passkey for Exco access |
| `SESSION_SECRET` | ✅ | Secret key for `SessionMiddleware` / `itsdangerous` |
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase `anon` or `service_role` API key |

Defined in `.env` (gitignored). See `.env.example` for the template.

---

### 9. Python Dependencies (`requirements.txt`)

| Package | Purpose |
|---|---|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `jinja2` | HTML templating |
| `supabase` | Supabase Python SDK |
| `python-dotenv` | `.env` file loading |
| `python-multipart` | Form data parsing |
| `itsdangerous` | Session cookie signing |

---

### 10. Running Locally

```bash
# 1. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your Supabase credentials and passkey

# 4. Start the development server
uvicorn app.main:app --reload
# App available at http://127.0.0.1:8000
```

---

### 11. Developer & AI Agent Guidelines

- **AI Agent Directives:** Refer to [AGENT.md](file:///c:/Users/panth/Documents/toastmasters-crm/AGENT.md) for critical constraints, including HTMX Protocol rules, UI/UX Design System standards, and session context retention directives.
- **Implementation Roadmap:** Refer to [AGENT_INSTRUCTIONS.md](file:///c:/Users/panth/Documents/toastmasters-crm/AGENT_INSTRUCTIONS.md) for the active build state and execution checklist.
- **Context Retention:** Respect the `.tokensave` protocol for capturing session checkpoints and restoring context.

