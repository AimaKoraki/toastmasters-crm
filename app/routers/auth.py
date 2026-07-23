from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ..config import EXCO_PASSKEY

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    if request.session.get("authenticated"):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request, "login.html")

@router.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, passkey: str = Form(...)):
    if passkey == EXCO_PASSKEY:
        request.session["authenticated"] = True
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"error": "Invalid passkey"})

@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
