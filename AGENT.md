# AI Agent Instructions & Operating System (`AGENT.md`)
## APIIT Kandy Club CRM

> **PRIMARY OPERATING DIRECTIVE:** Read this document and check the `.tokensave` file/directory before executing any task or modifying code in this repository.

---

## 1. Context Retention & `.tokensave` Protocol

To prevent context loss across agent sessions or token budget resets, adhere strictly to the `.tokensave` protocol:

1. **Session Initialization (Mandatory First Step):**
   - At the start of every session or task execution, inspect `.tokensave` (or the `.tokensave/` state folder) to restore past architectural decisions, completed steps, and active pending tasks.
   - If `.tokensave` contains state logs or checkpoint summaries, synthesize them into your working memory before generating any code.

2. **Session Progress & Checkpoint Logging:**
   - Whenever you complete a key implementation step (e.g., adding a route, updating a database query, or refactoring a UI component), update `.tokensave` with:
     - **Completed:** Brief summary of changes made.
     - **Current State:** Active files modified and verified.
     - **Next Up:** Immediate next task for continuity.

3. **Session Closure:**
   - Before finishing a prompt execution or handing off a multi-step workflow, ensure `.tokensave` reflects the exact current working state.

---

## 2. Project Architecture & Tech Stack

- **Backend:** Python 3.11+ with FastAPI
- **Template Engine:** Jinja2 templates (returning server-rendered HTML partials)
- **Frontend Interactivity:** HTMX (v1.9+ via CDN) + Lucide Icons (via CDN)
- **CSS Design System:** Tailwind CSS via CDN + custom variables in `app/static/css/style.css`
- **Database:** Supabase (PostgreSQL) using official `supabase-py` SDK
- **Auth:** Passkey validation stored in `.env` (`EXCO_PASSKEY`) using Starlette Session Middleware

---

## 3. Core Coding Laws for AI Agents

### A. HTMX Protocol Rules
1. **Never Return JSON to HTMX Calls:** Any route called by `hx-get`, `hx-post`, `hx-put`, or `hx-delete` MUST return a `TemplateResponse` rendering an HTML fragment from `app/templates/partials/`.
2. **Out-of-Band Updates (`hx-swap-oob="true"`):** When an action updates secondary UI elements (like updating a stat counter badge when a new guest is created), return the OOB fragment alongside the main partial.
3. **Explicit Targets:** Always ensure HTMX forms define `hx-target` and `hx-swap`. Use `hx-on::after-request="this.reset()"` on creation forms to clear input fields on success.
4. **Re-initialize Lucide Icons:** Because HTMX injects dynamic HTML into the DOM, ensure `lucide.createIcons()` is re-triggered on `htmx:afterSettle`.

### B. UI & Design System Rules (Linear / Notion Style)
1. **Color Variables:**
   - Deep Slate (`#0f172a` / `#1e293b`): Navigation background and secondary text.
   - Bright Blue (`#2563eb`): Primary buttons (`.btn-primary`), active menu items, and key numbers.
   - Amber Accent (`#fbbf24`): Underlines (`.gold-underline`), badges, and subtle hover highlights. Never use as a solid main background.
   - Surface (`#FFFFFF`) / Background (`#F7F9FA`): Card containers and page body.
2. **Typography Scale:**
   - Dashboard Title: `32px` / Bold (700) with `.gold-underline`
   - Section Title: `20px` / Semibold (600)
   - Table Headers: `13px` / Semibold (600) / Uppercase (`letter-spacing: 0.08em`)
   - Body Text: `15px`
3. **Elevated Cards:** Use class `.card` (`border-radius: 14px`, `box-shadow: 0 6px 24px rgba(0,0,0,0.05)`, `border: 1px solid #E5E9E8`).
4. **Empty States:** Tables with 0 rows must render the `.empty-state` component (`📭` icon, clear copy, and primary action button).

---
