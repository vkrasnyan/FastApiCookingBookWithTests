import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from main import app, get_session
from models import Base, Recipe
import schemas

# Создаем тестовую базу данных (SQLite in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Настройка SQLAlchemy для тестовой базы данных
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)


# Переопределяем зависимость get_session для использования тестовой базы данных
async def override_get_session() -> AsyncSession:
    async with TestingSessionLocal() as session:
        yield session


# Применяем переопределение зависимости
app.dependency_overrides[get_session] = override_get_session

# Создаем TestClient для тестирования FastAPI приложения
client = TestClient(app)


@pytest.fixture(autouse=True)
async def setup_database():
    """Функция для создания базы данных перед каждым тестом"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def test_create_recipe():
    """Тестирование эндпоинта для создания нового рецепта"""
    response = client.post("/recipes/", json={
        "name": "Test Recipe",
        "cooking_time": 30,
        "ingredients": "ingredient1, ingredient2",
        "description": "Test description",
        "view_count": 0
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Recipe"
    assert data["cooking_time"] == 30
    assert data["view_count"] == 0



def test_get_recipes():
    """Тестирование эндпоинта, выводящего несколько рецептов"""
    client.post("/recipes/",
                json={"name": "Recipe 1", "cooking_time": 20, "ingredients": "ing1", "description": "desc1",
                      "view_count": 5})
    client.post("/recipes/",
                json={"name": "Recipe 2", "cooking_time": 15, "ingredients": "ing2", "description": "desc2",
                      "view_count": 10})

    response = client.get("/recipes/")
    assert response.status_code == 200
    data = response.json()

    assert data[0]["name"] == "Recipe 2"
    assert data[1]["name"] == "Recipe 1"


def test_get_recipe_by_id():
    """Тестирование эндпоинта для получения рецепта по ID"""
    response = client.post("/recipes/", json={
        "name": "Test Recipe",
        "cooking_time": 30,
        "ingredients": "ingredient1, ingredient2",
        "description": "Test description",
        "view_count": 0
    })
    assert response.status_code == 200

    data = response.json()
    recipe_id = data["id"]

    response = client.get(f"/recipes/{recipe_id}")
    assert response.status_code == 200

    assert response.json() == {
        "id": 1,
        "name": "Test Recipe",
        "cooking_time": 30,
        "ingredients": "ingredient1, ingredient2",
        "description": "Test description",
        "view_count": 1
    }


def test_update_recipe():
    """Тестирование эндпоинта для обновления рецепта"""
    response = client.post("/recipes/", json={
        "name": "Old Recipe",
        "cooking_time": 40,
        "ingredients": "ingredient1, ingredient2",
        "description": "Old description",
        "view_count": 0
    })
    assert response.status_code == 200

    data = response.json()
    recipe_id = data["id"]

    response = client.put(f"/recipes/{recipe_id}", json={
        "name": "Updated Recipe",
        "cooking_time": 50,
        "ingredients": "ingredient1, ingredient2",
        "description": "Updated description",
        "view_count": 0
    })

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "Updated Recipe",
        "cooking_time": 50,
        "ingredients": "ingredient1, ingredient2",
        "description": "Updated description",
        "view_count": 0
    }


def test_delete_recipe():
    """Тестирование эндпоинта для удаления рецепта"""
    response = client.post("/recipes/", json={
        "name": "Recipe to delete",
        "cooking_time": 30,
        "ingredients": "ingredient1, ingredient2",
        "description": "Test description",
        "view_count": 0
    })
    data = response.json()
    recipe_id = data["id"]

    response = client.delete(f"/recipes/{recipe_id}")
    assert response.status_code == 200
    assert response.json() == {"detail": "Recipe deleted successfully"}

    response = client.get(f"/recipes/{recipe_id}")
    assert response.status_code == 404
