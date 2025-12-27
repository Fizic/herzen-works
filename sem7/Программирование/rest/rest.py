# main.py
import uvicorn
from fastapi import FastAPI, HTTPException, status, Depends, Security
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from collections import Counter
from sqlalchemy.orm import Session
from database import get_db, BookDB # Предполагается, что database.py существует
from auth import verify_api_key      # Предполагается, что auth.py существует

# --- Настройки FastAPI ---
app = FastAPI(
    title="Books API (Лабораторная)",
    description="REST API для управления библиотекой книг на FastAPI.",
    version="1.0.0"
)

# --- Pydantic Модели (Схемы) ---
class BookBase(BaseModel):
    # Field(...) делает поле обязательным
    title: str = Field(..., min_length=1, max_length=200, description="Название книги")
    author: str = Field(..., min_length=1, max_length=100, description="Автор книги")
    # Валидация числовых значений
    year: int = Field(..., ge=1000, le=datetime.now().year, description="Год издания")
    isbn: Optional[str] = Field(None, min_length=10, max_length=13, description="ISBN книги")

class Book(BookBase):
    id: int # ID обязателен при возврате из API

    class Config:
        # Для совместимости с SQLAlchemy
        from_attributes = True 

# Модель для обновления (все поля опциональны)
class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    year: Optional[int] = Field(None, ge=1000, le=datetime.now().year)
    isbn: Optional[str] = Field(None, min_length=10, max_length=13)

# --- Инициализация БД и зависимостей ---

# ВРЕМЕННОЕ ХРАНИЛИЩЕ (для Задания 1 - ДО перехода на БД)
# books_db: List[Book] = [
#     Book(id=1, title="Война и мир", author="Лев Толстой", year=1869, isbn="9785170987654"),
#     # ... другие книги ...
# ]
# next_id = 4 

# --- Эндпоинты API ---

# Корневой эндпоинт
@app.get("/", tags=["Root"])
async def root():
    """Возвращает приветственное сообщение и ссылки на документацию."""
    return {"message": "Добро пожаловать в Books API!", "docs": "/docs", "redoc": "/redoc"}

# GET /api/books - Получение списка всех книг (Задание 4: Фильтрация/Пагинация, Задание 5: Использование БД)
@app.get("/api/books", response_model=List[Book], tags=["Books"])
async def get_books(
    db: Session = Depends(get_db), # Задание 5: Зависимость от БД
    author: Optional[str] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    skip: int = 0,
    limit: int = 10
):
    """Получить список книг с фильтрацией и пагинацией."""
    query = db.query(BookDB)
    
    # Фильтрация
    if author:
        query = query.filter(BookDB.author.ilike(f"%{author}%")) # Регистронезависимый поиск
    if year_from:
        query = query.filter(BookDB.year >= year_from)
    if year_to:
        query = query.filter(BookDB.year <= year_to)

    # Пагинация
    books = query.offset(skip).limit(limit).all()
    return books


# GET /api/books/{book_id} - Получение книги по ID
@app.get("/api/books/{book_id}", response_model=Book, tags=["Books"])
async def get_book(book_id: int, db: Session = Depends(get_db)): # Задание 5: Использование БД
    """Получить книгу по ID. Возвращает ошибку 404, если книга не найдена."""
    book = db.query(BookDB).filter(BookDB.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Книга с ID {book_id} не найдена")
    return book


# POST /api/books - Создание новой книги (Задание 6: Аутентификация)
@app.post("/api/books", response_model=Book, status_code=status.HTTP_201_CREATED, tags=["Books"])
async def create_book(
    book: BookBase, 
    db: Session = Depends(get_db), # Задание 5: Использование БД
    api_key: str = Depends(verify_api_key) # Задание 6: Зависимость от аутентификации
):
    """Создать новую книгу. Требуется заголовок 'X-API-Key'."""
    # Создание экземпляра BookDB из Pydantic-модели BookBase
    db_book = BookDB(**book.model_dump()) 
    
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


# PUT /api/books/{book_id} - Полное обновление книги (Задание 6: Аутентификация)
@app.put("/api/books/{book_id}", response_model=Book, tags=["Books"])
async def update_book(
    book_id: int, 
    updated_book: BookBase, 
    db: Session = Depends(get_db), # Задание 5: Использование БД
    api_key: str = Depends(verify_api_key) # Задание 6: Зависимость от аутентификации
):
    """Полностью обновить информацию о книге. Возвращает ошибку 404, если книга не найдена."""
    db_book = db.query(BookDB).filter(BookDB.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Книга с ID {book_id} не найдена")

    # Обновление полей в объекте БД
    for field, value in updated_book.model_dump().items():
        setattr(db_book, field, value)
    
    db.commit()
    db.refresh(db_book)
    return db_book


# PATCH /api/books/{book_id} - Частичное обновление книги (Задание 6: Аутентификация)
@app.patch("/api/books/{book_id}", response_model=Book, tags=["Books"])
async def partial_update_book(
    book_id: int, 
    book_update: BookUpdate, 
    db: Session = Depends(get_db), # Задание 5: Использование БД
    api_key: str = Depends(verify_api_key) # Задание 6: Зависимость от аутентификации
):
    """Частично обновить информацию о книге. Обновляются только переданные поля."""
    db_book = db.query(BookDB).filter(BookDB.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Книга с ID {book_id} не найдена")

    # model_dump(exclude_unset=True) возвращает только те поля, которые были явно установлены
    update_data = book_update.model_dump(exclude_unset=True) 
    for field, value in update_data.items():
        setattr(db_book, field, value)
    
    db.commit()
    db.refresh(db_book)
    return db_book


# DELETE /api/books/{book_id} - Удаление книги (Задание 6: Аутентификация)
@app.delete("/api/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Books"])
async def delete_book(
    book_id: int, 
    db: Session = Depends(get_db), # Задание 5: Использование БД
    api_key: str = Depends(verify_api_key) # Задание 6: Зависимость от аутентификации
):
    """Удалить книгу по ID. Возвращает код 204."""
    db_book = db.query(BookDB).filter(BookDB.id == book_id).first()
    if db_book is None:
        # Даже если книга не найдена, DELETE часто возвращает 204 для идемпотентности, 
        # но для учебной цели можно вернуть 404.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Книга с ID {book_id} не найдена")

    db.delete(db_book)
    db.commit()
    return # Возврат 204 No Content

# GET /api/books/stats - Статистика (Задание 4: Добавление статистики)
@app.get("/api/books/stats", tags=["Statistics"])
async def get_statistics(db: Session = Depends(get_db)):
    """Получить статистику по книгам (общее количество, по авторам и векам)."""
    all_books = db.query(BookDB).all()
    total_books = len(all_books)
    
    authors = Counter(book.author for book in all_books)
    # Расчет века: (год // 100) + 1
    centuries = Counter(book.year // 100 + 1 for book in all_books) 
    
    return {
        "total_books": total_books,
        "books_by_author": dict(authors),
        "books_by_century": {f"{century} век": count for century, count in centuries.items()}
    }

# --- Точка входа для запуска приложения ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)