# Product Requirements Document (PRD)
## APIIT Kandy Club CRM

### 1. Goal & Vision
A lightweight, high-speed internal management system built for the Vice President Membership (VPM) and Executive Committee (Exco) of APIIT Kandy Club. The system streamlines prospective guest tracking, member management, meeting attendance, role history, and executive decision-making through an intuitive, action-oriented dashboard.

---

### 2. Feature & Implementation Status Summary

| Module | Name | Status | Implemented Components | Pending Deliverables |
|---|---|---|---|---|
| **Core** | Access & Auth | ✅ Complete | Passkey verification, session cookie, route guards, login page | Hardened secret loading from env |
| **Module A** | Executive Dashboard | ✅ Complete | Metric cards, upcoming meeting hero, activity feed, pipeline preview, all 5 quick actions wired | — |
| **Module B** | Guest & Prospect Pipeline | ✅ Complete | Guest table view, guest creation endpoint, stage progression (`POST /stage`), auto-onboarding, stage history modal, stage filter tabs | — |
| **Module C** | Member Management | ✅ Complete | Roster directory UI (`partials/members.html`), CRUD endpoints in `members.py`, status filtering, renewal cycle tracking, modals | — |
| **Module D** | Meeting & Attendance | ✅ Complete | Meeting creation, meeting list with stats, batch attendance logger (`POST /attendance`), interactive check-in UI | — |
| **Module E** | Roles & History Matrix | ✅ Complete | Role catalog, dynamic cross-tabulation frequency matrix, multi-role assignment (`POST /roles/assign`), member role history modal | — |
| **Module F** | Reports & Exports | ✅ Complete | Reports overview dashboard (`partials/reports.html`), export modal, CSV download generator (`GET /reports/download`) | — |

---

### 3. Access & Authentication

- **Access Model:** Simple Exco Passkey authentication.
- **Session Management:** Users enter a shared Exco passkey stored in `.env`. Once validated, an HTTP-only session cookie grants administrative access across all routes.
- **Implementation State:**
  - [x] Passkey validation via `POST /login`
  - [x] Session cookie persistence using Starlette `SessionMiddleware`
  - [x] Route protection dependency with HTMX redirect support (`dependencies.py`)
  - [x] Branded login UI (`login.html`)

---

### 4. UI/UX Design System & Aesthetics

- **Design Philosophy:** Modern, clean admin UI inspired by **Linear, Notion, and GitHub** (not generic Bootstrap templates).
- **Brand Palette:**
  - **Navigation Base:** Deep Slate (`#0f172a` / `#1e293b`)
  - **Primary Buttons & Active Items:** Bright Blue (`#2563eb`)
  - **Accent Underlines & Highlights:** Amber Accent (`#fbbf24`)
  - **Background:** Light Neutral (`#F7F9FA`)
  - **Surface & Cards:** Pure White (`#FFFFFF`) with `14px` border-radius and soft shadow (`0 6px 24px rgba(0,0,0,0.05)`).
- **Typography Scale:**
  - Page Title: `32px` / Bold (700)
  - Section Title: `20px` / Semibold (600)
  - Table Headers: `13px` / Semibold (600) / Uppercase (`letter-spacing: 0.08em`)
  - Body: `15px`
- **Component Patterns:**
  - **Avatar Tables:** Combined initials badge + full name + stacked email layout.
  - **Polished Empty States:** Custom illustration/emoji (`📭`, `📅`, `🎭`), friendly microcopy, and direct CTA buttons when tables are empty.
  - **Lucide Icons:** Client-side icon rendering with HTMX lifecycle hook (`htmx:afterSettle`).

---

### 5. Navigation Architecture (Sidebar Shell)

Fixed left sidebar (`w-64`) with Lucide icons, categorized into clear operational domains:

- **Dashboard:** `/` (✅ Implemented)
- **CRM:**
  - Guests: `hx-get="/prospects"` (✅ Implemented)
  - Members: `hx-get="/members"` (⏳ Pending implementation)
  - Follow-ups: `hx-get="/follow-ups"` (⏳ Pending implementation)
- **Meetings:**
  - Attendance: `hx-get="/meetings"` (✅ Implemented)
  - Agenda: `hx-get="/agenda"` (⏳ Pending implementation)
  - Evaluations: `hx-get="/evaluations"` (⏳ Pending implementation)
- **Management:**
  - Role Matrix: `hx-get="/roles"` (✅ Implemented)
  - Reports: `hx-get="/reports"` (⏳ Pending implementation)
- **Footer:**
  - Settings: `hx-get="/settings"` (⏳ Pending implementation)
  - Logout: `/logout` (✅ Implemented)

---

### 6. Core Functional Modules

#### Module A: Executive Dashboard & Quick Actions
- **Metric Summary Cards:** Real-time counters for Active Members, Total Guests, Active Prospects, and Average Attendance Rate (with division-by-zero protection). *(✅ Implemented)*
- **Gold Accent:** Decorative Gold underline (`#fbbf24`, `4px` height) under the main Dashboard title. *(✅ Implemented)*
- **Upcoming Meeting Hero Card:** Highlights Date, Theme, Meeting Host, and Venue. *(✅ Implemented)*
- **Quick Actions Panel:** One-click triggers for heavy meeting-day workflows:
  - `＋ Add Guest` *(✅ Implemented - opens Add Guest modal)*
  - `＋ Record Attendance` *(✅ Implemented - loads attendance check-in view)*
  - `＋ Assign Roles` *(✅ Implemented - opens Assign Role modal)*
  - `＋ Start Meeting` *(✅ Implemented - loads Live Meeting Console)*
  - `＋ Export Report` *(✅ Implemented - opens Export Report modal)*
- **Recent Activity Feed:** Real-time timeline feed showing recent guest registrations, attendance logs, and role updates. *(✅ Implemented)*

#### Module B: Guest & Prospect Pipeline
- **Guest Logging:** Log new meeting guests (Name, Email, Phone, First Visit Date, Notes). *(✅ Implemented)*
- **Pipeline Stages:** `1st Visit` -> `2nd Visit` -> `Form Sent` -> `Payment Pending` -> `Onboarded`. *(✅ Implemented with append-only logging in `prospect_logs`)*
- **Dynamic Status Badges:** `1st Visit` = Sky Blue, `2nd Visit` = Blue, `Form Sent` = Indigo, `Payment Pending` = Amber, `Onboarded` = Emerald Green. *(✅ Implemented)*
- **Delivered Features:**
  - [x] Implemented `POST /prospects/{id}/stage` in `app/routers/prospects.py`.
  - [x] Inline stage advancement fast-track button and "Update Stage" modal in `partials/prospects.html`.
  - [x] Automatic member status transition to `'Active'` upon reaching `Onboarded` stage.
  - [x] Stage progression history timeline modal (`GET /prospects/{id}/history`).
  - [x] Stage filter tabs (`All`, `1st Visit`, `2nd Visit`, `Form Sent`, `Payment Pending`, `Onboarded`).

#### Module C: Member Management
- **Member Profiles:** Full Name, Contact Details, Join Date, Status (`Active`/`Inactive`/`Alumni`), Pathways Level. *(✅ Implemented)*
- **Semi-annual Renewal Tracking:** March & September renewal cycle urgency indicators. *(✅ Implemented)*
- **Delivered Features:**
  - [x] Implemented `app/routers/members.py` with `GET /members`, `GET /members/new`, `POST /members`, `GET /members/{id}/edit`, `POST /members/{id}`.
  - [x] Built `app/templates/partials/members.html` with status filter tabs (`All`, `Active`, `Inactive`, `Alumni`) and KPI summary strip.
  - [x] Built standalone Add Member and Edit Member modals (`partials/member_modal.html`, `partials/member_edit_modal.html`).
  - [x] Added dynamic semi-annual dues renewal calculation (March 31 / September 30 Toastmasters cycles).
  - [x] Automated test suite `test_members.py` verified.

#### Module D: Meeting & Attendance Tracking
- **Meeting Records:** Create upcoming or past meetings (Meeting #, Date, Theme, Host). *(✅ Implemented)*
- **Batch Check-in Interface:** Mark members/guests as `Present`, `Absent`, `Excused`, or `Guest`. *(✅ Implemented)*
- **Delivered Features:**
  - [x] Implemented `POST /attendance` batch save endpoint in `app/routers/meetings.py`.
  - [x] Built interactive attendance check-in table partial (`partials/attendance.html`) with bulk action helpers and live search.
  - [x] Connected "Mark Attendance" action button in `partials/meetings.html`.
  - [x] Display real-time attendance counts (`X Present / Y Absent / Z Excused`) per meeting.

#### Module E: Flexible Role Assignments & History Matrix
- **Master Catalogue of Club Roles:** Pre-populated standard roles (Meeting Host, Topics Master, General Evaluator, Speaker, Timer, Filler Word Counter, Language Evaluator, etc.). *(✅ Implemented in `SCHEMA.sql`)*
- **Multi-role Support:** Allow assigning multiple functional roles to a single member in one meeting (e.g., Timer + Filler Word Counter combined). *(✅ Implemented via composite uniqueness)*
- **Member Role Frequency Matrix:** View role distribution across meetings to ensure equitable assignments. *(✅ Implemented)*
- **Delivered Features:**
  - [x] Implemented dynamic cross-tabulation frequency matrix in `app/routers/roles.py`.
  - [x] Replaced numeric ID inputs with dynamic `<select>` dropdowns for meetings, members, and roles in `partials/roles.html`.
  - [x] Added member role history timeline modal (`GET /roles/member/{id}/history`).
  - [x] Added category filter tabs (`All Roles`, `Major Roles`, `Functional Roles`) and roster search.

#### Module F: Reports & Exports
- **CSV & PDF Report Generation:** Export guest conversion rates, meeting attendance logs, and member role participation history. *(✅ Implemented)*
- **Delivered Features:**
  - [x] Implemented `app/routers/reports.py` with streaming CSV export for attendance, guests, roles, and overall club summary.
  - [x] Created `partials/export_modal.html` and `partials/reports.html`.
  - [x] Wired sidebar "Reports" link and dashboard "Export Report" quick action.