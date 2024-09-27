from typing import List
from fastapi import FastAPI, Response, UploadFile
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from schema import TaskSchemaOut, TaskWithImagesSchemaOut
from service import create_task_service, delete_task_service, get_all_tasks_service, get_task_with_images_service, create_image_service


app = FastAPI()


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
