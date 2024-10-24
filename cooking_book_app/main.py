from typing import List, AsyncGenerator, Union
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import models
import schemas
from database import engine, async_session

app = FastAPI()


# Функция для обработки жизненного цикла приложения в современных версиях FastAPI
async def lifespan(app: FastAPI) -> AsyncGenerator:
    # Выполняется при запуске приложения
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield
    # Выполняется при завершении работы приложения
    await engine.dispose()


app = FastAPI(lifespan=lifespan)


# Зависимость для получения сессии
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


@app.post('/recipes/', response_model=schemas.RecipeOut)
async def create_recipe(recipe: schemas.RecipeIn, session: AsyncSession = Depends(get_session)) -> models.Recipe:
    # Используем model_dump() вместо dict() в Pydantic 2.x
    new_recipe = models.Recipe(**recipe.model_dump())
    session.add(new_recipe)
    await session.commit()
    await session.refresh(new_recipe)
    return new_recipe


@app.get('/recipes/', response_model=List[schemas.RecipeOut])
async def get_recipes(session: AsyncSession = Depends(get_session)) -> List[models.Recipe]:
    """"Эндпоинт для добавления рецептов"""
    result = await session.execute(
        select(models.Recipe).order_by(desc(models.Recipe.view_count), models.Recipe.cooking_time)
    )

    return result.scalars().all()


@app.get('/recipes/{id}', response_model=schemas.RecipeOut)
async def get_recipe_by_id(id: int, session: AsyncSession = Depends(get_session)) -> models.Recipe:
    """Эндпоинт для получения рецепта по ID с увеличением счетчика просмотров"""
    try:
        result = await session.execute(select(models.Recipe).filter_by(id=id))
        recipe = result.scalars().one_or_none()

        if recipe is None:
            raise HTTPException(status_code=404, detail="Recipe not found")

        recipe.view_count += 1

        # Сохраняем изменения
        session.add(recipe)
        await session.commit()
        await session.refresh(recipe)

        return recipe

    except NoResultFound:
        raise HTTPException(status_code=404, detail="Recipe not found")


@app.put('/recipes/{id}', response_model=schemas.RecipeOut)
async def update_recipe(id: int, recipe_update: schemas.RecipeUpdate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(models.Recipe).filter_by(id=id))
    recipe = result.scalars().one_or_none()

    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    recipe.name = recipe_update.name
    recipe.cooking_time = recipe_update.cooking_time
    recipe.ingredients = recipe_update.ingredients
    recipe.description = recipe_update.description

    session.add(recipe)
    await session.commit()
    await session.refresh(recipe)

    return recipe

@app.delete('/recipes/{id}', response_model=dict)
async def delete_recipe(id: int, session: AsyncSession = Depends(get_session)) -> dict:
    """Эндпоинт для удаления рецепта по ID"""
    result = await session.execute(select(models.Recipe).filter_by(id=id))
    recipe = result.scalars().one_or_none()

    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    await session.delete(recipe)
    await session.commit()

    return {"detail": "Recipe deleted successfully"}