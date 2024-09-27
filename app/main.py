import base64
import secrets
from typing import List

from fastapi import FastAPI, HTTPException, Response, UploadFile, status
from pydantic import ValidationError
from schema import TaskSchemaOut, TaskWithImagesSchemaOut
from service import (
    create_image_service,
    create_task_service,
    delete_task_service,
    get_all_tasks_service,
    get_task_with_images_service,
)
from settings import settings
from sqlalchemy.exc import IntegrityError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class ApidocBasicAuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        auth_header = request.headers.get("Authorization")
        if auth_header:
            try:
                scheme, credentials = auth_header.split()
                if scheme.lower() == "basic":
                    decoded = base64.b64decode(credentials).decode("ascii")
                    username, password = decoded.split(":")
                    correct_username = secrets.compare_digest(username, settings.LOCAL_LOGIN)
                    correct_password = secrets.compare_digest(password, settings.LOCAL_PASSWORD)
                    if correct_username and correct_password:
                        return await call_next(request)
            except Exception:
                pass

        response = Response(content="Unauthorized", status_code=status.HTTP_401_UNAUTHORIZED)
        response.headers["WWW-Authenticate"] = "Basic"
        return response


app = FastAPI()
app.add_middleware(ApidocBasicAuthMiddleware)


@app.post(
    "/tasks/",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "content": {"application/json": {"example": {"task_id": 1}}},
        },
    },
)
async def create_task():
    return {"task_id": await create_task_service()}


@app.post(
    "/tasks/{task_id}/add_image/",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "content": {"application/json": {"example": {"image_id": 1}}},
        },
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {
            "content": {"application/json": {"example": {"detail": "Invalid document type"}}},
        },
        status.HTTP_404_NOT_FOUND: {
            "content": {"application/json": {"example": {"detail": "Not Found"}}},
        },
    },
)
async def add_image_to_task(task_id: int, image_name: str, image: UploadFile):
    if image.content_type != "image/jpeg":
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Invalid document type")
    try:
        return {"image_id": await create_image_service(task_id=task_id, name=image_name, file=image)}
    except IntegrityError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not Found")


@app.delete("/tasks/{task_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int):
    await delete_task_service(task_id=task_id)


@app.get(
    "/tasks/{task_id}/",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "content": {"application/json": {"example": {"detail": "Not Found"}}},
        },
    },
)
async def retrieve_task(task_id: int) -> TaskWithImagesSchemaOut:
    try:
        return await get_task_with_images_service(task_id=task_id)
    except ValidationError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Not Found")


@app.get("/tasks/")
async def retrieve_all_tasks() -> List[TaskSchemaOut]:
    return await get_all_tasks_service()
