# Product Requirements Document (PRD)
## APIIT Kandy Toastmasters CRM

### 1. Goal & Vision
A lightweight, high-speed internal management system built for the Vice President Membership (VPM) and Executive Committee (Exco) of APIIT Kandy Toastmasters. The system handles prospective guest tracking, member management, meeting attendance, and member role history.

### 2. Access & Authentication
- **Access Model:** Simple Exco Passkey authentication. Users enter a shared Exco passkey stored in `.env`. Once validated, an HTTP-only session cookie grants full administrative access.

### 3. Core Functional Modules

#### Module A: Guest & Prospect Pipeline
- Log new meeting guests (Name, Email, Phone, First Visit Date, Notes).
- Pipeline Stages: `1st Visit` -> `2nd Visit` -> `Form Sent` -> `Payment Pending` -> `Onboarded`.

#### Module B: Member Management
- Member profiles (Full Name, Contact Details, Join Date, Status: `Active`/`Inactive`/`Alumni`, Pathways Level).
- Renewal tracking (March & September renewal cycles).

#### Module C: Meeting & Attendance Tracking
- Create upcoming or past meetings (Meeting #, Date, Theme, TMOD).
- Batch check-in interface to mark members/guests as `Present`, `Absent`, or `Excused`.

#### Module D: Flexible Role Assignments & History
- Master catalogue of Toastmasters roles.
- Support assigning **multiple roles to a single member** in a single meeting (e.g., Timer + Ah-Counter combined).
- Member Role Frequency Matrix: View role distribution across meetings to ensure equitable assignments.
