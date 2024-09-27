from typing import List

from constants import GenderEnum
from database import sync_engine
from sqlalchemy import ForeignKey, String, inspect
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):

    def to_dict(self):
        """Функция для представления атрибутов модели в виде словаря."""

        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class Task(Base):
    __tablename__ = "task_table"

    id: Mapped[int] = mapped_column(primary_key=True)

    images: Mapped[List["Image"]] = relationship(back_populates="task")


class Image(Base):
    __tablename__ = "image_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    path: Mapped[str] = mapped_column(String(255))
    task_id: Mapped[int] = mapped_column(ForeignKey("task_table.id", ondelete="CASCADE"))

    persons: Mapped[List["Person"]] = relationship(back_populates="image")
    task: Mapped["Task"] = relationship(back_populates="images")


class Person(Base):
    __tablename__ = "person_table"

    id: Mapped[int] = mapped_column(primary_key=True)
    gender: Mapped[GenderEnum]
    age: Mapped[int]

    bbox_height: Mapped[int]
    bbox_width: Mapped[int]
    bbox_x: Mapped[int]
    bbox_y: Mapped[int]

    image_id: Mapped[int] = mapped_column(ForeignKey("image_table.id", ondelete="CASCADE"))

    image: Mapped["Image"] = relationship(back_populates="persons")


# В рамках тестового задания не расписываю миграции и при перезапуске, сбрасываю БД
Base.metadata.drop_all(sync_engine)
Base.metadata.create_all(sync_engine)
