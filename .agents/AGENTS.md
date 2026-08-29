# Workspace Rules for AI Agent Execution

You are working in the Club CRM repository. To ensure high-quality and consistent codebase modifications, you must adhere to the rules defined below.

### 1. Mandatory Context Gathering
Before starting any coding task, plan, or implementation:
- **Read [AGENT.md](file:///c:/Users/panth/Documents/toastmasters-crm/AGENT.md):** Understand the core coding laws, HTMX rules, and UI/UX design tokens.
- **Read [ARCHITECTURE.md](file:///c:/Users/panth/Documents/toastmasters-crm/ARCHITECTURE.md):** Understand the current technology stack, project directory structure, and database schema.
- **Check the `.tokensave` folder/state:** Inspect state logs/checkpoints to restore context and track task progress.

### 2. Context Retention & Checkpoints
- After completing any significant step or sub-task, log a progress checkpoint in the `.tokensave` directory (or use its corresponding tools/mechanisms) with completed tasks, current state, and next steps.
- Ensure the state is properly saved before finishing your turn.

### 3. Technical Constraints
- **HTMX calls** must only return HTML partials from `app/templates/partials/`, never raw JSON.
- **Lucide Icons** must be re-initialized when elements are dynamically rendered by HTMX.
- **UI/UX Design:** Adhere strictly to the standard palette (Slate, Blue, Amber) and card/typography scales.
