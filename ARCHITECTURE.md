# Technical Architecture & Guidelines

### 1. Technology Stack
- **Backend:** Python 3.11+ with FastAPI
- **Authentication:** Starlette Session Middleware + Passkey Check (`EXCO_PASSKEY`)
- **Template Engine:** Jinja2 templates returning HTML partials for HTMX
- **Frontend Interactivity:** HTMX (v1.9+) via CDN + Tailwind CSS via CDN
- **Database:** Supabase (PostgreSQL) using official `supabase-py` SDK

### 2. Project Directory Structure
```text
toastmasters-crm/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app & Passkey auth middleware
│   ├── config.py                # Environment variables & Supabase client
│   ├── dependencies.py          # Session authentication dependency
│   ├── routers/
│   │   ├── auth.py              # Login/Logout passkey views
│   │   ├── prospects.py         # Guest pipeline endpoints
│   │   ├── members.py           # Member management endpoints
│   │   ├── meetings.py          # Meetings & attendance endpoints
│   │   └── roles.py             # Role assignments & history matrix
│   ├── templates/
│   │   ├── base.html            # Layout wrapper
│   │   ├── login.html           # Simple passkey prompt
│   │   ├── index.html           # Main dashboard container
│   │   └── partials/            # HTMX target snippets
│   └── static/
├── .env.example
├── requirements.txt
├── PRD.md
├── ARCHITECTURE.md
├── SCHEMA.sql
└── AGENT_INSTRUCTIONS.md