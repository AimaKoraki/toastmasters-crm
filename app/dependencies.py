from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse

def get_current_user(request: Request):
    user = request.session.get("authenticated")
    if not user:
        # For HTMX requests, we might want to return a specific header
        if request.headers.get("HX-Request"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                headers={"HX-Redirect": "/login"}
            )
        # For regular requests, redirect to login
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/login"}
        )
    return user
