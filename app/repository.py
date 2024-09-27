import os

from dataclasses import dataclass
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import subqueryload
from schema import ImageAnalysisSchemaIn, PersonSchemaIn
from models import Image, Person, Task

from database import async_session


@dataclass(frozen=True, slots=True)
class ImageRepository:

    async_session: async_sessionmaker[AsyncSession] = async_session

    async def create(self, name: str, path: str, task_id: int) -> int:
        async with self.async_session() as session:
            new_image = Image(name=name, path=path, task_id=task_id)
            session.add(new_image)
            await session.flush()
            id = new_image.id
            await session.commit()
            return id

    async def delete(self, image_id: int) -> None:
        async with self.async_session() as session:
            stmt = delete(Image).where(Image.id == image_id).returning(Image.path)
            path = await session.execute(stmt)
            path = path.scalar_one()
            await session.commit()
            os.remove(path)

image_repository = ImageRepository()


@dataclass(frozen=True, slots=True)
class TaskRepository:

    async_session: async_sessionmaker[AsyncSession] = async_session
    image_repository: ImageRepository = image_repository

    async def create(self) -> int:

        async with self.async_session() as session:
            new_task = Task()
            session.add(new_task)
            await session.flush()
            id = new_task.id
            await session.commit()
            return id

    async def get_task_with_persons_and_images(self, task_id: int) -> Task | None:

        async with self.async_session() as session:
            stmt = select(Task).where(Task.id == task_id).options(subqueryload(Task.images).subqueryload(Image.persons))
            task = await session.scalars(stmt)
            return task.one_or_none()

    async def delete_with_images(self, task_id: int) -> None:

        task = await self.get_task_with_persons_and_images(task_id=task_id)

        if not task:
            return

        async with self.async_session() as session:
            for image in task.images:
                await self.image_repository.delete(image_id=image.id)


            stmt = delete(Task).where(Task.id == task_id)
            await session.execute(stmt)
            await session.commit()

    async def get_all(self):

        async with self.async_session() as session:
            stmt = select(Task)
            tasks = await session.scalars(stmt)
            return tasks.all()


task_repository = TaskRepository()


@dataclass(frozen=True, slots=True)
class PersonRepository:

    async_session: async_sessionmaker[AsyncSession] = async_session
    person_pydantic_class: type[PersonSchemaIn] = PersonSchemaIn

    async def create_from_image_analysis_data(self, data: ImageAnalysisSchemaIn, image_id: int) -> int:
        async with self.async_session() as session:
            person_create_data = self.person_pydantic_class(
                image_id=image_id,
                gender=data.demographics.gender,
                age=int(data.demographics.age.mean),
                bbox_height=data.bbox.height,
                bbox_width=data.bbox.width,
                bbox_x=data.bbox.x,
                bbox_y=data.bbox.y,
            )
            new_person = Person(**person_create_data.model_dump())
            session.add(new_person)
            await session.flush()
            id = new_person.id
            await session.commit()

            return id

person_repository = PersonRepository()
