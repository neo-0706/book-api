import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ایمپورت اجزای اصلی از فایل main
from main import app, Base, get_db, BookModel
from dotenv import load_dotenv
import os

load_dotenv()

# آدرس دیتابیس (می‌توانید از متغیر محیطی یا آدرس مستقیم استفاده کنید)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:your_password@localhost:5432/book_db")

engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# تابع جایگزین برای تزریق دیتابیس در تست‌ها
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# جایگزین کردن Dependency دیتابیس اصلی با دیتابیس تستی
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    """Clear the books table before and after each test to keep them independent."""
    db = TestingSessionLocal()
    try:
        db.query(BookModel).delete()
        db.commit()
    finally:
        db.close()
    
    yield
    
    db = TestingSessionLocal()
    try:
        db.query(BookModel).delete()
        db.commit()
    finally:
        db.close()


def sample_book():
    return {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "published_year": 2008,
    }


def test_get_books_returns_empty_list_initially():
    response = client.get("/books")

    assert response.status_code == 200
    assert response.json() == []


def test_create_book_returns_created_book():
    response = client.post("/books", json=sample_book())

    data = response.json()
    assert response.status_code == 201
    assert data["id"] is not None  # دیتابیس خودش ID تولید می‌کند
    assert data["title"] == sample_book()["title"]
    assert data["author"] == sample_book()["author"]
    assert data["published_year"] == sample_book()["published_year"]


def test_create_multiple_books_assigns_incrementing_ids():
    first = client.post("/books", json=sample_book())
    second_data = {**sample_book(), "title": "The Pragmatic Programmer"}
    second = client.post("/books", json=second_data)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]  # مطمئن می‌شویم IDها متفاوت و افزایشی هستند


def test_create_book_rejects_invalid_data():
    invalid_book = {**sample_book(), "published_year": 0}

    response = client.post("/books", json=invalid_book)

    assert response.status_code == 422


def test_get_book_by_id_returns_book():
    created = client.post("/books", json=sample_book())
    book_id = created.json()["id"]

    response = client.get(f"/books/{book_id}")

    assert response.status_code == 200
    assert response.json()["id"] == book_id
    assert response.json()["title"] == sample_book()["title"]


def test_get_missing_book_returns_404():
    response = client.get("/books/99999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


def test_patch_updates_only_provided_fields():
    created = client.post("/books", json=sample_book())
    book_id = created.json()["id"]

    response = client.patch(
        f"/books/{book_id}",
        json={"title": "Clean Code: Updated Edition"},
    )

    data = response.json()
    assert response.status_code == 200
    assert data["id"] == book_id
    assert data["title"] == "Clean Code: Updated Edition"
    assert data["author"] == "Robert C. Martin"  # تغییر نکرده است
    assert data["published_year"] == 2008  # تغییر نکرده است


def test_patch_missing_book_returns_404():
    response = client.patch("/books/99999", json={"title": "Unknown Book"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


def test_delete_book_returns_204_and_removes_book():
    created = client.post("/books", json=sample_book())
    book_id = created.json()["id"]

    response = client.delete(f"/books/{book_id}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/books/{book_id}").status_code == 404


def test_delete_missing_book_returns_404():
    response = client.delete("/books/99999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}