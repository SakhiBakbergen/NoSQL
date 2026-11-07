from fastapi import FastAPI, HTTPException, status, Query
from pymongo.errors import PyMongoError, DuplicateKeyError
from typing import List, Optional

import config
from models import BookCreate, BookUpdate, BookResponse
from repository import BookRepository

app = FastAPI(title="Library API - Variant 9")
repo = BookRepository(config.MONGODB_URI, config.DB_NAME)

@app.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate):
    try:
        if repo.get_by_isbn(book.isbn):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Книга уже существует")
        return repo.create(book.model_dump())
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Книга уже существует")
    except PyMongoError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Хранилище недоступно")

@app.get("/books", response_model=List[BookResponse])
def get_books(author: Optional[str] = Query(None), category: Optional[str] = Query(None)):
    try:
        return repo.get_all(author=author, category=category)
    except PyMongoError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Хранилище недоступно")

@app.get("/books/{isbn}", response_model=BookResponse)
def get_book(isbn: str):
    try:
        book = repo.get_by_isbn(isbn)
        if not book:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не найдено")
        return book
    except PyMongoError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Хранилище недоступно")

@app.put("/books/{isbn}", response_model=BookResponse)
def update_book(isbn: str, book_data: BookUpdate):
    try:
        updated = repo.update(isbn, book_data.model_dump())
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не найдено")
        return updated
    except PyMongoError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Хранилище недоступно")

@app.delete("/books/{isbn}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(isbn: str):
    try:
        success = repo.delete(isbn)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Не найдено")
        return None
    except PyMongoError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Хранилище недоступно")