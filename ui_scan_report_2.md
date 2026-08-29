# UI/UX & Frontend Architecture Audit Report

**Date:** 2026-08-29
**Scope:** Global frontend scan focusing on HTMX integration, responsive design, component patterns, and user feedback loops.

## 🔴 High Priority Issues (User Feedback & Error Handling)

### 1. Missing Global Toast/Notification System & Silent Failures
**Problem:** Currently, when HTMX forms are submitted, there is no global system for success or error feedback.
- If a form succeeds, `meetings.html` and `roles.html` render hardcoded inline "Success Banners" at the top of the page. `prospects.html` renders **no success message at all**.
- If a form fails (e.g., a `400 Bad Request` or `422 Unprocessable Entity` from FastAPI due to a duplicate meeting number), HTMX receives JSON instead of HTML and silently fails. The user sees absolutely nothing happening.
**Recommendation:** Implement a global toast notification container in `base.html`. Use an `htmx:afterRequest` event listener or the `HX-Trigger` response header from FastAPI to trigger toast notifications uniformly for both successes and errors.

### 2. Missing Loading States (`hx-indicator`)
**Problem:** A `grep` search for `hx-indicator` across the `app/templates/` directory yielded zero results. When a user clicks a button that triggers an HTMX request (like "Save Attendance", "Mark Present", or submitting a form), there is no visual feedback that a network request is in flight. 
**Recommendation:** Add a global HTMX loading indicator in `base.html` (e.g., a slim progress bar at the top of the page) or attach specific `.htmx-indicator` spinners to primary action buttons.

## 🟡 Medium Priority Issues (Component Architecture)

### 3. Divergent Modal Implementations (Technical Debt)
**Problem:** The application is currently maintaining two separate patterns for the exact same modals:
- **Type A (Inline CSS toggle):** Modals like `#add-prospect-modal` are hardcoded directly into `partials/prospects.html`. They are toggled by manually changing the `.hidden` CSS class via `onclick`.
- **Type B (HTMX Standalone):** The Dashboard Quick Actions load a completely separate file (`partials/prospect_modal.html` with ID `#add-prospect-modal-standalone`) via `hx-get` into the global `#modal-container`.
**Recommendation:** Standardize on **Type B (HTMX Standalone)**. Remove the inline modals from the partials and use `hx-get` to fetch modals into `#modal-container` everywhere. This ensures DRY code and prevents potential ID collisions.

## 🟢 Low Priority Issues (Polish)

### 4. Icon Inconsistency
**Problem:** The app strictly uses Lucide icons (`<i data-lucide="..."></i>`) which are re-initialized on every HTMX swap. However, the **Recent Activity Feed** in `index.html` uses a hardcoded inline `<svg>` for its checkmark icon.
**Recommendation:** Replace the inline SVG with `<i data-lucide="check"></i>` for consistency with the rest of the UI.

### 5. Sticky Table Rows Hover Conflict
**Problem:** In the Role Matrix (`partials/roles.html`), the sticky member name column is an excellent UX choice for horizontal scrolling. However, it applies `hover:bg-slate-50/70` independently of the `matrix-row` hover, meaning if you hover over a member's name, only that cell highlights, not the entire row.
**Recommendation:** Move the hover styling to the parent `<tr>` and set the sticky `<td>` background to inherit or apply a uniform transparent overlay.

---
*Would you like me to create an implementation plan to resolve these findings, starting with the Toast Notification system and Modal standardization?*
