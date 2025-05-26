from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette import status

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel

from schemas.movies import (
    MovieListResponseSchema,
    MovieDetailResponseSchema,
    MovieCreateSchema, MovieUpdateSchema,
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def read_movies(
    page: int = Query(1, ge=1, description="The actual page number."),
    per_page: int = Query(
        10, ge=1, le=20, description="Count movies on page"
    ),
    db: AsyncSession = Depends(get_db),
):
    total_items = await db.execute(select(func.count()).select_from(MovieModel))
    total_items = total_items.scalar_one()
    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    offset = (page - 1) * per_page
    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    result = await db.execute(
        select(MovieModel).order_by(MovieModel.id.desc())
        .offset(offset).limit(per_page)
    )
    movies = result.scalars().all()
    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}"
        if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages else None
    )

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post(
    "/movies/",
    response_model=MovieDetailResponseSchema,
    status_code=status.HTTP_201_CREATED
)
async def create_movie(
        movie: MovieCreateSchema,
        db: AsyncSession = Depends(get_db),
):
    existing_movie = await db.execute(
        select(MovieModel).where(
            MovieModel.name == movie.name,
            MovieModel.date == movie.date
        )
    )
    existing_movie = existing_movie.scalars().first()
    if existing_movie:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{movie.name}' "
                   f"and release date '{movie.date}' already exists."
        )

    country = await db.execute(
        select(CountryModel).where(CountryModel.code == movie.country))
    country_result = country.scalar_one_or_none()
    if not country_result:
        country_result = CountryModel(code=movie.country)
        db.add(country_result)
        await db.flush()

    genres_list = []
    for genre_name in movie.genres:
        get_genre = await db.execute(
            select(GenreModel).where(GenreModel.name == genre_name))
        result_genre = get_genre.scalar_one_or_none()
        if not result_genre:
            result_genre = GenreModel(name=genre_name)
            db.add(result_genre)
            await db.flush()
        genres_list.append(result_genre)

    actors_list = []
    for actor_name in movie.actors:
        get_actor = await db.execute(
            select(ActorModel).where(ActorModel.name == actor_name))
        result_actor = get_actor.scalar_one_or_none()
        if not result_actor:
            result_actor = ActorModel(name=actor_name)
            db.add(result_actor)
            await db.flush()
        actors_list.append(result_actor)

    languages_list = []
    for language_name in movie.languages:
        language = await db.execute(
            select(LanguageModel).where(LanguageModel.name == language_name))
        result_language = language.scalar_one_or_none()
        if not result_language:
            result_language = LanguageModel(name=language_name)
            db.add(result_language)
            await db.flush()
        languages_list.append(result_language)

    new_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country_id=country_result.id,
        country=country_result,
        genres=genres_list,
        actors=actors_list,
        languages=languages_list,
    )

    db.add(new_movie)
    await db.commit()
    await db.refresh(
        new_movie, attribute_names=["country", "genres", "actors", "languages"]
    )
    return new_movie


@router.get(
    "/movies/{movie_id}/",
    response_model=MovieDetailResponseSchema
)
async def movie_detail(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id).options(
            selectinload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
    )
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(
            status_code=404,
            detail="Movie with the given ID was not found."
        )
    return movie


@router.delete(
    "/movies/{movie_id}/",
)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )
    await db.delete(movie)
    await db.commit()
    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
        content="Movie was deleted successfully."
    )


@router.patch(
    "/movies/{movie_id}/",
    response_model=MovieDetailResponseSchema
)
async def update_movie(
    movie_id: int,
    update_data: MovieUpdateSchema,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MovieModel).where(MovieModel.id == movie_id)
    )
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found."
        )

    for key, value in update_data.model_dump(exclude_unset=True).items():
        setattr(movie, key, value)
    await db.commit()
    await db.refresh(movie)
    raise HTTPException(
        status_code=status.HTTP_200_OK,
        detail="Movie updated successfully."
    )
