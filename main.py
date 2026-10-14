from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="Book API",
    description="A simple REST API for managing books",
    version="1.0.0",
)


class BookCreate(BaseModel):
    title: str = Field(min_length=1)
    author: str = Field(min_length=1)
    published_year: int = Field(gt=0)


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    author: str | None = Field(default=None, min_length=1)
    published_year: int | None = Field(default=None, gt=0)


class Book(BookCreate):
    id: int


books: dict[int, Book] = {}
next_id = 1


@app.get("/books", response_model=list[Book])
def get_books():
    return list(books.values())


@app.post(
    "/books",
    response_model=Book,
    status_code=status.HTTP_201_CREATED,
)
def create_book(book: BookCreate):
    global next_id

    new_book = Book(id=next_id, **book.model_dump())
    books[next_id] = new_book
    next_id += 1

    return new_book


@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int):
    book = books.get(book_id)

    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    return book


@app.patch("/books/{book_id}", response_model=Book)
def update_book(book_id: int, updates: BookUpdate):
    book = books.get(book_id)

    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    updated_data = updates.model_dump(exclude_unset=True)
    updated_book = book.model_copy(update=updated_data)

    books[book_id] = updated_book
    return updated_book


@app.delete(
    "/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_book(book_id: int):
    if book_id not in books:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    del books[book_id]
