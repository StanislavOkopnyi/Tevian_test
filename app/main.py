import secrets
import base64

from typing import List
from fastapi import FastAPI, Response, UploadFile
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from settings import settings
from schema import TaskSchemaOut, TaskWithImagesSchemaOut
from service import create_task_service, delete_task_service, get_all_tasks_service, get_task_with_images_service, create_image_service



class ApidocBasicAuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                scheme, credentials = auth_header.split()
                if scheme.lower() == 'basic':
                    decoded = base64.b64decode(credentials).decode('ascii')
                    username, password = decoded.split(':')
                    correct_username = secrets.compare_digest(
                        username, settings.LOCAL_LOGIN)
                    correct_password = secrets.compare_digest(
                        password, settings.LOCAL_PASSWORD)
                    if correct_username and correct_password:
                        return await call_next(request)
            except Exception:
                pass

        response = Response(content='Unauthorized', status_code=401)
        response.headers['WWW-Authenticate'] = 'Basic'
        return response


app = FastAPI()
app.add_middleware(ApidocBasicAuthMiddleware)


@app.post("/tasks/", status_code=201)
async def create_task() -> int:
    return await create_task_service()


@app.post("/tasks/{task_id}/add_image/", status_code=201)
async def add_image_to_task(task_id: int, image_name: str, image: UploadFile) -> int:
    try:
        return await create_image_service(task_id=task_id, name=image_name, file=image)
    except IntegrityError:
        return Response(status_code=404)



@app.delete("/tasks/{task_id}/", status_code=204)
async def delete_task(task_id: int):
    await delete_task_service(task_id=task_id)


@app.get("/tasks/{task_id}/")
async def retrieve_task(task_id: int) -> TaskWithImagesSchemaOut:
    try:
        return await get_task_with_images_service(task_id=task_id)
    except ValidationError:
        return Response(status_code=404)


@app.get("/tasks/")
async def retrieve_all_tasks() -> List[TaskSchemaOut]:
    return await get_all_tasks_service()
