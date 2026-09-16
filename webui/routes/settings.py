from fastapi import APIRouter, Request, Response, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from datastore.datastore import get_db_conn

router = APIRouter()

templates = Jinja2Templates(directory="./webui/templates/")

@router.get("/settings")
def list_tunes(request: Request):
    

    return templates.TemplateResponse(
        request = request,
        name = "settings.html"
    )
