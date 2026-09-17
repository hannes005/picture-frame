from fastapi import APIRouter, Request, Response, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from datastore.datastore import get_db_conn

router = APIRouter()

templates = Jinja2Templates(directory="./webui/templates/")

@router.get("/")
def show_index(request: Request):    

    return RedirectResponse(url="/library", status_code=303)
