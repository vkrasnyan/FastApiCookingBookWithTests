from pydantic import BaseModel


class BaseRecipe(BaseModel):
    name: str
    cooking_time: int
    ingredients: str
    description: str
    view_count: int

class RecipeIn(BaseRecipe):
    ...

class RecipeOut(BaseRecipe):
    id: int

    class Config:
        from_orm = True


class RecipeUpdate(BaseRecipe):
    name: str
    cooking_time: int
    ingredients: str
    description: str

    class Config:
        from_orm = True
