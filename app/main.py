from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from app.routers import auth, prospects, meetings, roles
from app.dependencies import get_current_user
from fastapi import Depends

app = FastAPI(title="Toastmasters CRM")

# Add Session Middleware
app.add_middleware(SessionMiddleware, secret_key="super-secret-exco-key")

# Static and Templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include Routers
app.include_router(auth.router)
app.include_router(prospects.router)
app.include_router(meetings.router)
app.include_router(roles.router)

@app.get("/")
def read_root(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse(request, "index.html")
