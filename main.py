import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class BookModel(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    published_year = Column(Integer, nullable=False)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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

    class Config:
        from_attributes = True


app = FastAPI(
    title="Book API",
    description="A simple REST API for managing books with PostgreSQL",
    version="2.0.0",
)


@app.get("/books", response_model=list[Book])
def get_books(db: Session = Depends(get_db)):
    books = db.query(BookModel).all()
    return books


@app.post(
    "/books",
    response_model=Book,
    status_code=status.HTTP_201_CREATED,
)
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    db_book = BookModel(
        title=book.title,
        author=book.author,
        published_year=book.published_year
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(BookModel).filter(BookModel.id == book_id).first()

    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    return book


@app.patch("/books/{book_id}", response_model=Book)
def update_book(book_id: int, updates: BookUpdate, db: Session = Depends(get_db)):
    book = db.query(BookModel).filter(BookModel.id == book_id).first()

    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    update_data = updates.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(book, key, value)

    db.commit()
    db.refresh(book)
    return book


@app.delete(
    "/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(BookModel).filter(BookModel.id == book_id).first()

    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    db.delete(book)
    db.commit()
    return None