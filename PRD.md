# Product Requirements Document (PRD)
## APIIT Kandy Toastmasters CRM

### 1. Goal & Vision
A lightweight, high-speed internal management system built for the Vice President Membership (VPM) and Executive Committee (Exco) of APIIT Kandy Toastmasters. The system streamlines prospective guest tracking, member management, meeting attendance, role history, and executive decision-making through an intuitive, action-oriented dashboard.

---

### 2. Access & Authentication
- **Access Model:** Simple Exco Passkey authentication.
- **Session Management:** Users enter a shared Exco passkey stored in `.env`. Once validated, an HTTP-only session cookie grants administrative access across all routes.

---

### 3. UI/UX Design System & Aesthetics
- **Design Philosophy:** Modern, clean admin UI inspired by **Linear, Notion, and GitHub** (not generic Bootstrap templates).
- **Brand Palette (Toastmasters Official):**
  - **Navigation Base:** Loyal Navy (`#002B49` / `#004165`)
  - **Primary Buttons & Active Items:** True Maroon (`#772432`)
  - **Accent Underlines & Highlights:** Toastmasters Gold (`#F2DF00`)
  - **Background:** Light Neutral (`#F7F9FA`)
  - **Surface & Cards:** Pure White (`#FFFFFF`) with `14px` border-radius and soft shadow (`0 6px 24px rgba(0,0,0,0.05)`).
- **Typography Scale:**
  - Page Title: `32px` / Bold (700)
  - Section Title: `20px` / Semibold (600)
  - Table Headers: `13px` / Semibold (600) / Uppercase (`letter-spacing: 0.08em`)
  - Body: `15px`
- **Component Patterns:**
  - **Avatar Tables:** Combined initials badge + full name + stacked email layout.
  - **Polished Empty States:** Custom illustration/emoji (`📭`), friendly microcopy, and a direct CTA button when tables are empty.

---

### 4. Navigation Architecture (Sidebar Shell)
Fixed left sidebar (`w-64`) with Lucide icons, categorized into clear operational domains:

- **Dashboard**
- **CRM:** Guests, Members, Follow-ups
- **Meetings:** Attendance, Agenda, Evaluations
- **Management:** Role Matrix, Reports
- **Footer:** Settings, Logout

---

### 5. Core Functional Modules

#### Module A: Executive Dashboard & Quick Actions
- **Metric Summary Cards:** Real-time counters for Active Members, Total Guests, Active Prospects, and Average Attendance Rate (with division-by-zero protection).
- **Gold Accent:** Decorative Gold underline (`#F2DF00`, `4px` height) under the main Dashboard title.
- **Upcoming Meeting Hero Card:** Highlights Date, Theme, Toastmaster of the Day, and Venue.
- **Quick Actions Panel:** One-click triggers for heavy meeting-day workflows:
  - `＋ Add Guest`
  - `＋ Record Attendance`
  - `＋ Assign Roles`
  - `＋ Start Meeting`
  - `＋ Export Report`
- **Recent Activity Feed:** Real-time timeline feed showing recent guest registrations, attendance logs, and role updates.

#### Module B: Guest & Prospect Pipeline
- Log new meeting guests (Name, Email, Phone, First Visit Date, Notes).
- Pipeline Stages: `1st Visit` -> `2nd Visit` -> `Form Sent` -> `Payment Pending` -> `Onboarded`.
- Dynamic status badges (`Guest` = Sky Blue, `Prospect` = Amber, `Member` = Emerald Green).

#### Module C: Member Management
- Member profiles (Full Name, Contact Details, Join Date, Status: `Active`/`Inactive`/`Alumni`, Pathways Level).
- Semi-annual renewal tracking (March & September renewal cycles).

#### Module D: Meeting & Attendance Tracking
- Create upcoming or past meetings (Meeting #, Date, Theme, TMOD).
- Batch check-in interface to mark members/guests as `Present`, `Absent`, or `Excused`.

#### Module E: Flexible Role Assignments & History Matrix
- Master catalogue of Toastmasters roles.
- **Multi-role support:** Allow assigning multiple functional roles to a single member in one meeting (e.g., Timer + Ah-Counter combined).
- Member Role Frequency Matrix: View role distribution across meetings to ensure equitable assignments.

#### Module F: Reports & Exports
- Generate and export CSV/PDF reports for guest conversion rates, meeting attendance logs, and member role participation history.