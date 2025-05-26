import datetime

from typing import Optional, Literal
from pydantic import BaseModel, Field


class ConfigMixin:
    class Config:
        from_attributes = True


class LanguageSchema(BaseModel, ConfigMixin):
    id: int
    name: str


class ActorSchema(BaseModel, ConfigMixin):
    id: int
    name: str


class GenreSchema(BaseModel, ConfigMixin):
    id: int
    name: str


class CountrySchema(BaseModel, ConfigMixin):
    id: int
    code: str
    name: Optional[str]


class MovieDetailSchema(BaseModel, ConfigMixin):
    id: int
    name: str
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str


class MovieDetailResponseSchema(MovieDetailSchema):
    status: Literal["Released", "Post Production", "In Production"]
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: CountrySchema
    genres: list[GenreSchema]
    actors: list[ActorSchema]
    languages: list[LanguageSchema]


class MovieCreateSchema(BaseModel, ConfigMixin):
    name: str
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: Literal["Released", "Post Production", "In Production"]
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieListResponseSchema(BaseModel, ConfigMixin):
    movies: list[MovieDetailSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[
        Literal[
            "Released", "Post Production", "In Production"
        ]
    ] = None
    budget: Optional[float] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)
    country: Optional[str] = Field(None, min_length=3, max_length=3)
    genres: Optional[list[str]] = None
    actors: Optional[list[str]] = None
    languages: Optional[list[str]] = None
