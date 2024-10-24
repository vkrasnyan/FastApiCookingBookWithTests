from sqlalchemy import Column, String, Integer, Text

from database import Base

class Recipe(Base):
    """Модель представления рецепта в базе данных"""
    __tablename__ = 'Recipes'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    cooking_time = Column(Integer, index=True)
    ingredients = Column(String)
    description = Column(Text)
    view_count = Column(Integer, default=0)