# Antigravity Agent Execution Instructions & Roadmap
## APIIT Kandy Club CRM

---

### Project Status Overview

| Phase / Milestone | Status | Completion % |
|---|---|---|
| **Phase 1: Foundation & Auth** | ✅ Complete | 100% |
| **Phase 2: Core Dashboard & Metrics** | ✅ Complete | 95% |
| **Phase 3: Guest & Prospect Pipeline** | ✅ Complete | 100% |
| **Phase 4: Meeting & Attendance Tracking** | ✅ Complete | 100% |
| **Phase 5: Role Assignments & Matrix** | ✅ Complete | 100% |
| **Phase 6: Member Management Module** | ⏳ Pending | 0% |
| **Phase 7: Reports & Exports** | ⏳ Pending | 0% |

---

### Execution Roadmap & Checklist

- [x] **Step 1: Project Setup & Architecture**
  - [x] Folder structure (`app/`, `app/routers/`, `app/templates/`, `app/static/`, etc.)
  - [x] `requirements.txt` with FastAPI, Uvicorn, Jinja2, Supabase, Python-dotenv, Python-multipart, itsdangerous
  - [x] `.env.example` template with required keys
  - [x] `SCHEMA.sql` database schema definition (PostgreSQL / Supabase)

- [x] **Step 2: Authentication & Session Security**
  - [x] Starlette `SessionMiddleware` configuration in `app/main.py`
  - [x] Passkey verification login flow in `app/routers/auth.py` (`GET /login`, `POST /login`, `GET /logout`)
  - [x] Route protection dependency in `app/dependencies.py` (`get_current_user` with HTMX 401 `HX-Redirect` and standard 303 redirect)
  - [x] Branded split-screen login page (`app/templates/login.html`)

- [x] **Step 3: Database & Config Integration**
  - [x] Supabase client initialization in `app/config.py` with environment variable loading
  - [x] Environment variable fallback defaults

- [x] **Step 4: Executive Dashboard & UI Shell**
  - [x] Base layout template (`app/templates/base.html`) with fixed left sidebar navigation and global `#modal-container`
  - [x] Lucide icons integration with `htmx:afterSettle` auto-reinitialization
  - [x] Dashboard view (`app/templates/index.html`) with:
    - [x] 4-column metric counter cards (Active Members, Total Guests, Active Prospects, Attendance Rate with division-by-zero protection)
    - [x] Upcoming meeting hero card (dynamic host & date resolution)
    - [x] Real-time activity timeline feed aggregating `prospect_logs`, `attendance`, and `role_assignments`
    - [x] Guest pipeline summary table with avatar initials and matching stage badges
    - [x] Quick Action `＋ Add Guest` linked via HTMX to `/prospects/new` modal
    - [x] Quick Action `＋ Record Attendance` linked via HTMX to `/meetings/attendance` check-in view
    - [x] Quick Action `＋ Assign Roles` linked via HTMX to `/roles/assign` modal

- [x] **Step 5: Design Tokens & Styling**
  - [x] Tailwind CSS CDN integration with custom color scheme
  - [x] Custom CSS tokens in `app/static/css/style.css` (Slate `#0f172a` / `#1e293b`, Bright Blue `#2563eb`, Amber Accent `#fbbf24`, Neutral `#F7F9FA`)
  - [x] Modern elevated cards (`.card`, `.card-hover`, `border-radius: 14px`)
  - [x] Gold underline accent (`.gold-underline`) on dashboard title
  - [x] Standard empty states with `📭` / `📅` / `🎭` emojis and primary action triggers

- [x] **Step 6: Guest Pipeline & Stage Progression (Module B)**
  - [x] `GET /prospects`: Renders pipeline table partial with stage filters (`app/templates/partials/prospects.html`)
  - [x] `GET /prospects/new`: Renders standalone Add Guest modal (`app/templates/partials/prospect_modal.html`)
  - [x] `POST /prospects`: Creates new guest record in `members` and initial `1st Visit` log in `prospect_logs`
  - [x] `POST /prospects/{id}/stage`: Validates and transitions prospect stage (`1st Visit` → `2nd Visit` → `Form Sent` → `Payment Pending` → `Onboarded`)
  - [x] Automatic Onboarding logic: Upgrades member `status = 'Active'` when transition to `Onboarded` occurs
  - [x] `GET /prospects/{id}/history`: Returns stage history timeline modal (`app/templates/partials/prospect_history_modal.html`)
  - [x] Stage badges color-coded (Sky Blue, Blue, Indigo, Amber, Emerald)
  - [x] Inline fast-track advance button + modal stage selector with progress notes

- [x] **Step 7: Meeting Management & Batch Attendance Logger (Module D)**
  - [x] `GET /meetings`: Renders meetings list partial with attendance summary counts (`app/templates/partials/meetings.html`)
  - [x] `GET /meetings/new`: Renders standalone Add Meeting modal (`app/templates/partials/meeting_modal.html`)
  - [x] `POST /meetings`: Creates new meeting record (`meeting_number`, `meeting_date`, `theme`)
  - [x] `GET /meetings/{meeting_id}/attendance`: Renders interactive batch check-in matrix (`app/templates/partials/attendance.html`)
  - [x] `GET /meetings/attendance`: Quick action helper auto-selecting latest meeting
  - [x] `POST /attendance`: Batch upsert/save attendance records (`Present`, `Absent`, `Excused`, `Guest`)
  - [x] Segmented radio buttons per member row with bulk actions ("All Present", "All Absent", "All Excused")
  - [x] Live roster search filtering

- [x] **Step 8: Role Assignments & History Matrix (Module E)**
  - [x] `GET /roles`: Dynamic cross-tabulation matrix with heatmap frequency counters and category filter tabs (`app/templates/partials/roles.html`)
  - [x] `GET /roles/assign`: Standalone modal with friendly dropdowns for meetings, members, and roles (`app/templates/partials/role_assign_modal.html`)
  - [x] `POST /roles/assign`: Inserts `(meeting_id, member_id, role_id, speech_title)` into `role_assignments` with multi-role support
  - [x] `GET /roles/member/{member_id}/history`: Member role participation timeline modal (`app/templates/partials/member_role_history_modal.html`)
  - [x] Role matrix search filter and category filtering (`All`, `Major`, `Functional`)
  - [x] Heatmap count badges (soft gray for 0, subtle blue for 1-2, gold for 3+)

- [ ] **Step 9: Dedicated Member Management Module**
  - [ ] `app/routers/members.py` (`GET /members`, `POST /members`, `GET /members/{id}`)
  - [ ] Member directory partial (`app/templates/partials/members.html`) with status filters (`Active`, `Inactive`, `Alumni`)
  - [ ] Semi-annual renewal cycle tracker (March / September)
  - [ ] Pathways level management and progress tracking

- [ ] **Step 10: Quick Action Wiring & Modal Unification**
  - [x] `＋ Add Guest` (wired to `/prospects/new` modal container)
  - [x] `＋ Record Attendance` (wired to `/meetings/attendance` check-in view)
  - [x] `＋ Assign Roles` (wired to `/roles/assign` modal container)
  - [ ] `＋ Start Meeting` / Meeting Live Mode
  - [ ] `＋ Export Report`

- [ ] **Step 11: Reports & Data Exports**
  - [ ] `app/routers/reports.py` (`GET /reports`, `GET /reports/export`)
  - [ ] CSV/Excel export for:
    - [ ] Guest conversion rate & pipeline velocity
    - [ ] Meeting attendance logs
    - [ ] Member role participation history matrix

---

### Immediate Next Tasks (Priority Order)

1. **Implement Members Router & View:** Add `app/routers/members.py` and `app/templates/partials/members.html` with status filtering (`Active`, `Inactive`, `Alumni`) and renewal tracking.
2. **Reports & Exports Module:** Implement `app/routers/reports.py` with CSV export functionality.
3. **Wire Remaining Dashboard Quick Actions:** `＋ Start Meeting` & `＋ Export Report`.