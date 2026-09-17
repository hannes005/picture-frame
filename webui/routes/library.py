from fastapi import APIRouter, Request, Response, Form
from fastapi import APIRouter, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from datastore.datastore import get_db_conn
from datastore import datastore as datastore

router = APIRouter()

templates = Jinja2Templates(directory="./webui/templates/")

@router.get("/library")
def show_events(request: Request):

    events = datastore.get_events()

    return templates.TemplateResponse(
        request = request,
        name = "library.html",
        context = {
            "events": [dict(e) for e in events]
        }
    )

@router.post("/library/newevent")
def create_event(
        request: Request,
        title: str = Form(...)
    ):

    datastore.add_event(title)

    return RedirectResponse(url="/library", status_code=303)


@router.get("/library/events/{event_id:int}")
def show_event(
    request: Request,
    event_id: int
    ):

    event = datastore.get_event(event_id)
    images = datastore.get_images_for_event(event_id)

    return templates.TemplateResponse(
        request=request,
        name="show_event.html",
        context={
            "event": dict(event),
            "images": [dict(image) for image in images]
        }
    )

@router.post("/library/events/{event_id:int}/upload")
def upload_images(
    event_id: int,
    images: list[UploadFile] = File(...)
):
    for image in images:
        datastore.add_image(image, event_id)

    return RedirectResponse(
        url=f"/library/events/{event_id}",
        status_code=303
    )

@router.post("/library/images/{image_id:int}/delete")
def delete_image(image_id: int):

    #Get event id from image to redirect afterwards
    image = datastore.get_image(image_id)
    if image is None:
        return
    event_id = image["event_id"]

    #Delete image
    datastore.delete_image(image_id)

    return RedirectResponse(
        url=f"/library/events/{event_id}",
        status_code=303
    )


@router.post("/library/events/{event_id:int}/rename")
def rename_event(
    event_id: int,
    new_title: str = Form(...)
    ):

    datastore.rename_event(event_id, new_title)
    
    return RedirectResponse(
        url=f"/library/events/{event_id}",
        status_code=303
    )


@router.post("/library/events/{event_id:int}/delete")
def delete_event(event_id: int):

    datastore.delete_event(event_id)
    
    return RedirectResponse(
        url=f"/library",
        status_code=303
    )