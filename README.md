# 🎙️ APIIT Kandy Toastmasters Club CRM

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![HTMX](https://img.shields.io/badge/HTMX-1.9%2B-3366cc.svg?logo=htmx&logoColor=white)](https://htmx.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-CDN-38bdf8.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![Supabase](https://img.shields.io/badge/Database-Supabase%20PostgreSQL-3ecf8e.svg?logo=supabase&logoColor=white)](https://supabase.com)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

> A modern, ultra-responsive internal operations platform and CRM built specifically for the Executive Committee (Exco), Vice President Membership (VPM), and meeting organizers of **APIIT Kandy Toastmasters Club**.

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Project Directory Structure](#-project-directory-structure)
- [Database Schema & Data Model](#-database-schema--data-model)
- [Getting Started & Local Setup](#-getting-started--local-setup)
- [Environment Variables](#-environment-variables)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Deployment](#-deployment)
- [UI & Design System Guidelines](#-ui--design-system-guidelines)
- [License](#-license)

---

## 🌟 Overview

Managing a thriving Toastmasters club demands high operational rigor: tracking first-time guests, converting prospects into members, monitoring semi-annual dues renewals, scheduling meetings, logging attendance, balancing meeting roles across the roster, and reporting metrics to the District.

**APIIT Kandy Club CRM** is built without complex JavaScript framework build steps. Instead, it utilizes **FastAPI**, **HTMX**, **Jinja2 templates**, and **Tailwind CSS** to provide a fast single-page application (SPA) user experience directly backed by **Supabase PostgreSQL**.

---

## 🚀 Key Features

### 1. 📊 Executive Dashboard & Quick Actions
- **Live KPI Counters:** Real-time metrics for Active Members, Total Guests, Active Prospects, and Average Attendance Rate (with division-by-zero resilience).
- **Upcoming Meeting Hero Card:** Highlights meeting number, date, venue, and automatically resolves the Toastmaster of the Day (TMOD / Meeting Host).
- **Real-Time Activity Stream:** Aggregated chronological audit log of recent guest registrations, attendance records, and role assignments.
- **Immediate Quick Actions:** 1-click modal shortcuts from the dashboard:
  - `＋ Add Guest` (Opens Guest Intake Modal)
  - `＋ Record Attendance` (Loads separated batch check-in view)
  - `＋ Assign Roles` (Opens Meeting Role Assignment Modal)
  - `＋ Start Meeting` (Launches Live Meeting Console)
  - `＋ Export Report` (Opens CSV/Data Export Modal)

### 2. 🎯 Guest & Prospect Conversion Pipeline (Module B)
- **5-Stage Conversion Funnel:** Follows guests through:
  $$\text{1st Visit} \longrightarrow \text{2nd Visit} \longrightarrow \text{Form Sent} \longrightarrow \text{Payment Pending} \longrightarrow \text{Onboarded}$$
- **Automated Onboarding:** Marking a prospect as `Onboarded` automatically elevates their status to `Active` member in the central roster.
- **Stage Progression & History:** Detailed audit trail of stage changes, timestamps, and notes with timeline modal viewing (`GET /prospects/{id}/history`).
- **Contact Editing:** Update phone, email, and notes on the fly.

### 3. 👥 Comprehensive Member Management (Module C)
- **Central Roster Directory:** Filterable by status (`All`, `Active`, `Inactive`, `Alumni`) with instant client/server search.
- **Pathways Progress Tracking:** Manage educational progress from Level 1 through Level 5 and DTM.
- **Semi-Annual Dues Renewal Tracker:** Dynamic urgency badges tracking Toastmasters International renewal deadlines (**March 31** and **September 30**).

### 4. 📅 Meeting & Batch Attendance Management (Module D)
- **Meeting Scheduler:** Schedule upcoming meetings with meeting numbers, themes, and dates.
- **Split Batch Attendance Logger:** Separate batch attendance check-in sheets for **Club Members Roster** and **Meeting Guests Roster**.
- **1-Click Bulk Attendance:** Instant batch action buttons ("All Present", "All Absent", "All Excused").
- **Live Meeting Mode:** Real-time meeting console for running live club sessions.

### 5. 🎭 Role Assignments & Cross-Tabulation Matrix (Module E)
- **Dynamic Heatmap Frequency Matrix:** Cross-tabulation table calculating how many times each member has filled each club role.
- **Multi-Role Assignment Support:** Unique composite constraint allowing members to hold multiple functional roles during the same meeting (e.g., Timer + Ah-Counter).
- **Role Category Filtering:** Filter roles by `All Roles`, `Major Roles` (TMOD, Evaluator, Speaker, GE, TTM), or `Functional Roles` (Timer, Grammarian, Ah-Counter).
- **Member Role History Modal:** Timeline modal showing every role a member has performed across past meetings.

### 6. 📈 Reports & Data Exports (Module F)
- **Analytics Overview:** Visual summaries of attendance consistency, guest conversion rates, and role fulfillment.
- **Streaming CSV Exports:** Downloadable raw datasets:
  - Meeting Attendance Roster
  - Guest & Prospect Pipeline History
  - Member Role Assignment Matrix
  - Full Club KPI Executive Summary

### 7. 🔐 Security & Access Control
- **Exco Passkey Authentication:** Shared Executive Committee passkey stored securely in environment variables.
- **Cryptographic Session Cookies:** Powered by Starlette `SessionMiddleware` and `itsdangerous`.
- **HTMX-Aware Route Guards:** Unauthenticated HTMX requests receive `401 Unauthorized` with `HX-Redirect: /login` to prevent broken UI injection states.

---

## 🏗️ Architecture & Tech Stack

```mermaid
flowchart TD
    subgraph Browser ["Client (Browser)"]
        UI["Tailwind CSS + Lucide Icons"]
        HTMX["HTMX (Partial Swaps & OOB)"]
    end

    subgraph Server ["Backend (FastAPI / Starlette)"]
        App["FastAPI (app/main.py)"]
        AuthMid["Session Middleware & Passkey Guard"]
        Jinja["Jinja2 Template Engine"]
        Routers["Routers:\n/auth, /prospects, /meetings,\n/roles, /members, /reports"]
    end

    subgraph Database ["Cloud Database (Supabase)"]
        PG["PostgreSQL Tables & Custom Enums"]
    end

    HTMX -->|HTTP GET/POST with hx-headers| AuthMid
    AuthMid --> Routers
    Routers -->|Python SDK Queries| PG
    PG -->|Data Records| Routers
    Routers --> Jinja
    Jinja -->|HTML Partials (partials/*.html)| HTMX
    HTMX -->|DOM Settle & lucide.createIcons()| UI
```

| Layer | Technology | Details |
|---|---|---|
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) | Python 3.11+, ASGI asynchronous framework |
| **Session Security** | Starlette `SessionMiddleware` + `itsdangerous` | Encrypted HTTP-only cookies with shared Exco passkey |
| **Templating** | [Jinja2](https://palletsprojects.com/p/jinja/) | Server-rendered full pages and modular HTMX partials |
| **Frontend Interactivity**| [HTMX 1.9+](https://htmx.org/) | Dynamic swaps, modal injection, OOB updates (No JS build step) |
| **Styling & Design** | [Tailwind CSS CDN](https://tailwindcss.com/) + Custom Tokens | Slate, Bright Blue, and Amber Accent design palette |
| **Icons** | [Lucide Icons](https://lucide.dev/) | Dynamic client-side reinitialization on `htmx:afterSettle` |
| **Database** | [Supabase](https://supabase.com/) | Managed PostgreSQL with `supabase-py` SDK |

---

## 📁 Project Directory Structure

```text
toastmasters-crm/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application setup & root dashboard logic
│   ├── config.py                   # Environment variables & Supabase client initialization
│   ├── dependencies.py             # Session authentication dependency (get_current_user)
│   ├── routers/
│   │   ├── auth.py                 # /login, /logout endpoints
│   │   ├── prospects.py            # Guest & pipeline management, stage progression
│   │   ├── meetings.py             # Meeting scheduling & batch attendance tracking
│   │   ├── roles.py                # Role assignments & frequency matrix
│   │   ├── members.py              # Member directory, status, and renewal tracking
│   │   └── reports.py              # Analytics overview & CSV streaming exports
│   ├── templates/
│   │   ├── base.html               # Shell layout (sidebar, topbar, HTMX & Lucide bootstrap)
│   │   ├── index.html              # Executive dashboard (metrics, hero card, feed, pipeline)
│   │   ├── login.html              # Branded split-screen passkey authentication page
│   │   └── partials/               # Modular HTML components rendered by HTMX
│   │       ├── attendance.html     # Batch attendance check-in table
│   │       ├── export_modal.html   # Report download modal
│   │       ├── live_meeting.html   # Live meeting management console
│   │       ├── meeting_modal.html  # Schedule new meeting modal
│   │       ├── meetings.html       # Meetings list view
│   │       ├── member_modal.html   # Add new member modal
│   │       ├── member_edit_modal.html # Edit member modal
│   │       ├── members.html        # Member directory partial
│   │       ├── prospect_modal.html # Add new guest modal
│   │       ├── prospect_edit_modal.html # Edit guest contact modal
│   │       ├── prospect_history_modal.html # Stage timeline modal
│   │       ├── prospects.html      # Guest pipeline table partial
│   │       ├── role_assign_modal.html # Role assignment modal
│   │       ├── roles.html          # Role frequency matrix partial
│   │       └── reports.html        # Reports overview partial
│   └── static/
│       └── css/
│           └── style.css           # Custom design system tokens, cards, and scrollbar styles
├── .env.example                    # Environment variable configuration template
├── Procfile                        # Production process runner for PaaS (Heroku, Railway)
├── runtime.txt                     # Python runtime version pinning (python-3.11.9)
├── requirements.txt                # Python package dependencies
├── SCHEMA.sql                      # PostgreSQL database schema & initial seed data
├── PRD.md                          # Product Requirements Document
├── ARCHITECTURE.md                 # Technical Architecture & Guidelines
├── AGENT.md                        # AI Agent operating directives
├── AGENT_INSTRUCTIONS.md           # Implementation milestone roadmap
├── test_app.py                     # Health & auth integration tests
├── test_meetings.py                # Meeting & attendance tests
├── test_members.py                 # Member CRUD & renewal tests
├── test_prospects.py               # Guest intake & stage progression tests
├── test_quick_actions.py           # Dashboard quick action verification tests
├── test_roles.py                   # Role assignment & matrix tests
└── README.md                       # Repository documentation (this file)
```

---

## 🗄️ Database Schema & Data Model

The application uses PostgreSQL (via Supabase). The schema is defined in [`SCHEMA.sql`](./SCHEMA.sql).

### Custom Enum Types
- `member_status`: `'Prospect'`, `'Active'`, `'Inactive'`, `'Alumni'`
- `prospect_stage`: `'1st Visit'`, `'2nd Visit'`, `'Form Sent'`, `'Payment Pending'`, `'Onboarded'`
- `attendance_status`: `'Present'`, `'Absent'`, `'Excused'`, `'Guest'`

### Core Tables
1. **`members`**: Single contact table storing all people (guests, active members, alumni) with their email, phone, status, and Pathways level.
2. **`prospect_logs`**: Append-only log tracking stage transitions, timestamps, and follow-up notes for every prospect.
3. **`meetings`**: Meeting records (`meeting_number`, `meeting_date`, `theme`).
4. **`role_catalog`**: Master list of club roles categorized as `Major` or `Functional`.
5. **`role_assignments`**: Maps members to roles per meeting. Supports multi-role assignments via composite uniqueness `UNIQUE(meeting_id, member_id, role_id)`.
6. **`attendance`**: Records attendance status per member per meeting (`UNIQUE(meeting_id, member_id)`).

---

## ⚙️ Getting Started & Local Setup

### 1. Prerequisites
- **Python 3.11+** installed
- **Git** installed
- A free **[Supabase](https://supabase.com/)** account & project

### 2. Clone the Repository
```bash
git clone https://github.com/AimaKoraki/toastmasters-crm.git
cd toastmasters-crm
```

### 3. Create & Activate a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Database in Supabase
1. Open your project on [Supabase Console](https://app.supabase.com).
2. Navigate to the **SQL Editor**.
3. Copy the contents of [`SCHEMA.sql`](./SCHEMA.sql) and paste it into the editor.
4. Click **Run** to execute the table creation and role catalog seeding.

### 6. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and fill in your Supabase credentials and chosen passkey:
```ini
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-supabase-anon-key
EXCO_PASSKEY=your-secret-exco-passkey
SESSION_SECRET=generate-a-secure-random-32-char-string
PORT=8000
```

### 7. Run the Application
```bash
uvicorn app.main:app --reload --port 8000
```

Open your browser and navigate to:
```text
http://127.0.0.1:8000
```
Log in using the `EXCO_PASSKEY` configured in your `.env`.

---

## 🔒 Environment Variables

| Variable | Required | Description | Example |
|---|:---:|---|---|
| `SUPABASE_URL` | **Yes** | Project URL from Supabase Project Settings → API | `https://xyz.supabase.co` |
| `SUPABASE_KEY` | **Yes** | Supabase `anon` / `public` API key | `eyJhbGciOi...` |
| `EXCO_PASSKEY` | **Yes** | Secret passkey for Exco admin login | `kandy-exco-2026` |
| `SESSION_SECRET` | **Yes** | Cryptographic key for signing session cookies | `a-secure-32-character-key` |
| `PORT` | No | Server port (Defaults to `8000`) | `8000` |

---

## 🧪 Testing & Quality Assurance

The codebase comes with a comprehensive suite of automated integration and endpoint tests:

```bash
# Run core health & auth verification
python test_app.py

# Run meeting & attendance tests
python test_meetings.py

# Run member directory & renewal calculation tests
python test_members.py

# Run guest pipeline & stage transition tests
python test_prospects.py

# Run role assignment & frequency matrix tests
python test_roles.py

# Run dashboard quick actions tests
python test_quick_actions.py
```

Or execute all tests using `pytest` (if installed):
```bash
pytest
```

---

## ☁️ Deployment

The application is pre-configured for instant deployment on container or PaaS hosts (e.g., Heroku, Railway, Render, Fly.io).

- **`Procfile`:**
  ```text
  web: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers
  ```
- **`runtime.txt`:** Pins Python runtime to `python-3.11.9`.
- **Health Probe:** Built-in lightweight health check endpoint at `/healthz`.

### Deploying to Railway / Render / Heroku:
1. Connect your GitHub repository.
2. Ensure Python 3.11 is detected.
3. Configure the environment variables in your cloud dashboard (`SUPABASE_URL`, `SUPABASE_KEY`, `EXCO_PASSKEY`, `SESSION_SECRET`).
4. Launch the build!

---

## 🎨 UI & Design System Guidelines

The visual interface adheres strictly to a clean, productivity-focused design inspired by **Linear** and **Notion**:

- **Color Tokens:**
  - **Deep Slate (`#0f172a` / `#1e293b`):** Sidebar navigation and header bars.
  - **Bright Blue (`#2563eb`):** Primary action buttons (`.btn-primary`) and active indicators.
  - **Amber Accent (`#fbbf24`):** Dashboard decorative title underlines (`.gold-underline`) and alert badges.
  - **Surface (`#FFFFFF`) & Background (`#F7F9FA`):** High-contrast, clean card surfaces.
- **Card Aesthetics:** Elevated cards (`.card`) with `border-radius: 14px`, subtle borders (`#E5E9E8`), and soft box shadows (`0 6px 24px rgba(0,0,0,0.05)`).
- **HTMX Rule:** All interactive endpoints return partial templates from `app/templates/partials/`. Lucide icons automatically re-render via `htmx:afterSettle`.

---

## 📄 License

This project is licensed under the [GNU General Public License v3.0 (GPL-3.0)](./LICENSE).

---

<p align="center">
  Built with ❤️ for <b>APIIT Kandy Toastmasters Club</b>
</p>
