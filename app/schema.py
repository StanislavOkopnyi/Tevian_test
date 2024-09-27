from constants import GenderEnum
from pydantic import BaseModel, ConfigDict


class PersonSchemaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    gender: GenderEnum
    age: int
    bbox_height: int
    bbox_width: int
    bbox_x: int
    bbox_y: int


class ImageSchemaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    persons: list[PersonSchemaOut]


class TaskWithImagesSchemaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    images: list[ImageSchemaOut]
    person_num: int | None = None
    male_num: int | None = None
    female_num: int | None = None
    male_mean_age: int | None = None
    female_mean_age: int | None = None


class TaskSchemaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int


class BoundingBox(BaseModel):
    height: int
    width: int
    x: int
    y: int


class AgeInfoSchemaIn(BaseModel):
    mean: int
    variance: float


class DemographicsInfoSchemaIn(BaseModel):
    gender: GenderEnum
    ethnicity: str
    age: AgeInfoSchemaIn


class ImageAnalysisSchemaIn(BaseModel):
    bbox: BoundingBox
    demographics: DemographicsInfoSchemaIn
    score: float


class PersonSchemaIn(BaseModel):
    gender: GenderEnum
    age: int

    bbox_height: int
    bbox_width: int
    bbox_x: int
    bbox_y: int

    image_id: int
