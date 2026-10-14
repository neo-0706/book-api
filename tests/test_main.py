import pytest
from fastapi.testclient import TestClient

from main import app, books


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_books():
    """Keep each test independent by resetting the in-memory store."""
    books.clear()
    # The application assigns IDs using a module-level counter.
    import main
    main.next_id = 1
    yield
    books.clear()
    main.next_id = 1


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

    assert response.status_code == 201
    assert response.json() == {"id": 1, **sample_book()}


def test_create_multiple_books_assigns_incrementing_ids():
    first = client.post("/books", json=sample_book())
    second_data = {**sample_book(), "title": "The Pragmatic Programmer"}
    second = client.post("/books", json=second_data)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == 1
    assert second.json()["id"] == 2


def test_create_book_rejects_invalid_data():
    invalid_book = {**sample_book(), "published_year": 0}

    response = client.post("/books", json=invalid_book)

    assert response.status_code == 422


def test_get_book_by_id_returns_book():
    created = client.post("/books", json=sample_book())
    book_id = created.json()["id"]

    response = client.get(f"/books/{book_id}")

    assert response.status_code == 200
    assert response.json() == created.json()


def test_get_missing_book_returns_404():
    response = client.get("/books/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


def test_patch_updates_only_provided_fields():
    created = client.post("/books", json=sample_book())
    book_id = created.json()["id"]

    response = client.patch(
        f"/books/{book_id}",
        json={"title": "Clean Code: Updated Edition"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": book_id,
        "title": "Clean Code: Updated Edition",
        "author": "Robert C. Martin",
        "published_year": 2008,
    }


def test_patch_missing_book_returns_404():
    response = client.patch("/books/999", json={"title": "Unknown Book"})

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
    response = client.delete("/books/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}
