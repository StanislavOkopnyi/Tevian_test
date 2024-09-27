from dataclasses import dataclass
from uuid import uuid4

import aiofiles
import httpx
import requests
from constants import GenderEnum
from fastapi import UploadFile
from repository import (
    ImageRepository,
    PersonRepository,
    TaskRepository,
    image_repository,
    person_repository,
    task_repository,
)
from schema import ImageAnalysisSchemaIn, TaskSchemaOut, TaskWithImagesSchemaOut
from settings import settings


@dataclass(frozen=True, slots=True)
class CreateTaskService:

    task_repository: TaskRepository = task_repository

    async def __call__(self) -> int:
        task_id = await self.task_repository.create()
        return task_id


create_task_service = CreateTaskService()


@dataclass(frozen=True, slots=True)
class DeleteTaskService:

    task_repository: TaskRepository = task_repository

    async def __call__(self, task_id: int):
        await self.task_repository.delete_with_images(task_id=task_id)


delete_task_service = DeleteTaskService()


@dataclass(frozen=True, slots=True)
class GetAllTasksService:

    task_repository: TaskRepository = task_repository
    pydantic_class: type[TaskSchemaOut] = TaskSchemaOut

    async def __call__(self):
        tasks = await self.task_repository.get_all()
        return [self.pydantic_class.model_validate(task) for task in tasks]


get_all_tasks_service = GetAllTasksService()


class GetStatisticsFromImageAnalysisService:

    __slots__ = ()

    def __call__(self, data: TaskWithImagesSchemaOut) -> dict[str, int]:
        person_num = self._get_persons_num(data=data)
        male_num = self._get_male_num(data=data)
        female_num = self._get_female_num(data=data)
        male_mean_age = self._get_male_mean_age(data=data)
        female_mean_age = self._get_female_mean_age(data=data)

        return {
            "person_num": person_num,
            "male_num": male_num,
            "female_num": female_num,
            "male_mean_age": male_mean_age,
            "female_mean_age": female_mean_age,
        }

    def _get_persons_num(self, data: TaskWithImagesSchemaOut) -> int:
        images = data.images
        i = 0
        for image in images:
            i += len(image.persons)
        return i

    def _get_male_num(self, data: TaskWithImagesSchemaOut) -> int:
        images = data.images
        i = 0
        for image in images:
            for person in image.persons:
                if person.gender == GenderEnum.male:
                    i += 1
        return i

    def _get_female_num(self, data: TaskWithImagesSchemaOut) -> int:
        images = data.images
        i = 0
        for image in images:
            for person in image.persons:
                if person.gender == GenderEnum.female:
                    i += 1
        return i

    def _get_male_mean_age(self, data: TaskWithImagesSchemaOut) -> int:
        ages = []
        images = data.images
        for image in images:
            for person in image.persons:
                if person.gender == GenderEnum.male:
                    ages.append(person.age)
        return sum(ages) // len(ages) if ages else 0

    def _get_female_mean_age(self, data: TaskWithImagesSchemaOut) -> int:
        ages = []
        images = data.images
        for image in images:
            for person in image.persons:
                if person.gender == GenderEnum.female:
                    ages.append(person.age)
        return sum(ages) // len(ages) if ages else 0


get_statistics_from_image_analysis_service = GetStatisticsFromImageAnalysisService()


@dataclass(frozen=True, slots=True)
class GetTaskWithImagesService:

    task_repository: TaskRepository = task_repository
    task_pydantic_class: type[TaskWithImagesSchemaOut] = TaskWithImagesSchemaOut
    get_statistics_service: GetStatisticsFromImageAnalysisService = get_statistics_from_image_analysis_service

    async def __call__(self, task_id: int) -> TaskWithImagesSchemaOut:
        task_instance = await self.task_repository.get_task_with_persons_and_images(task_id=task_id)
        validated_data = self.task_pydantic_class.model_validate(task_instance)
        statistics = self.get_statistics_service(data=validated_data)

        for key, value in statistics.items():
            setattr(validated_data, key, value)

        return validated_data


get_task_with_images_service = GetTaskWithImagesService()


class GetImageAnalysisService:

    __slots__ = "access_token", "pydantic_class"

    def __init__(self, pydantic_class: type[ImageAnalysisSchemaIn] = ImageAnalysisSchemaIn) -> None:
        # Запрашиваем один раз при запуске приложения
        login_path = f"{settings.API_HOST}/api/v1/login"
        response = requests.post(login_path, json={"email": settings.EMAIL, "password": settings.PASSWORD})
        self.access_token = response.json()["data"]["access_token"]
        self.pydantic_class = pydantic_class

    async def __call__(self, image: UploadFile) -> list[ImageAnalysisSchemaIn]:
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "image/jpeg"}
        async with httpx.AsyncClient(headers=headers) as client:
            image_analysis_path = f"{settings.API_HOST}/api/v1/detect"
            params = {"demographics": "true"}
            response = await client.post(image_analysis_path, params=params, content=image.file.read())
            result = response.json()
            print(result)
            result = result["data"]
            return [self.pydantic_class.model_validate(i) for i in result]


get_image_analysis_service = GetImageAnalysisService()


@dataclass(frozen=True, slots=True)
class CreateImageService:

    image_repository: ImageRepository = image_repository
    person_repository: PersonRepository = person_repository
    image_analysis_service: GetImageAnalysisService = get_image_analysis_service

    async def __call__(self, name: str, file: UploadFile, task_id: int) -> int:
        path = f"images/{file.filename}_{uuid4()}.jpeg"

        image_id = await self.image_repository.create(name=name, path=path, task_id=task_id)
        image_analysis = await self.image_analysis_service(image=file)

        async with aiofiles.open(path, "wb") as out_file:
            while content := await file.read(1024):
                await out_file.write(content)

        for person_data in image_analysis:
            await self.person_repository.create_from_image_analysis_data(image_id=image_id, data=person_data)

        return image_id


create_image_service = CreateImageService()
