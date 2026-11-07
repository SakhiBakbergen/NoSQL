from pydantic import BaseModel, Field
from typing import Optional

class BookCreate(BaseModel):
    isbn: str = Field(..., description="ISBN книги")
    title: str = Field(..., description="Название")
    author: str = Field(..., description="Автор")
    category: str = Field(..., description="Категория")
    year: int = Field(..., description="Год")
    price: float = Field(..., gt=0, description="Цена")

class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    year: Optional[int] = None
    price: Optional[float] = Field(None, gt=0)

class BookResponse(BookCreate):
    pass