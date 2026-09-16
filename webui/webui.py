from fastapi import FastAPI, HTTPException, Request, Response, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from contextlib import asynccontextmanager

from webui.routes.library import router as library_router
from webui.routes.settings import router as settings_router
from webui.routes.index import router as index_router

from datastore.datastore import initialize_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield

print("Start")

app = FastAPI(lifespan=lifespan)

app.include_router(library_router)
app.include_router(settings_router)
app.include_router(index_router)

app.mount("/static/", StaticFiles(directory="./webui/static/"), name="static")
app.mount("/datastore/media/thumbnail/", StaticFiles(directory="./datastore/media/thumbnail/"), name="thumbnail")


templates = Jinja2Templates(directory="./templates/")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)