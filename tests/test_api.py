
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db
from app.models import Base
from app.auth import get_current_user

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine)


def override_get_db():
    try:
        db = TestSessionLocal()
        yield db
    finally:
        db.close()


def override_get_current_user():
    from app.auth import AuthUser
    mock_claims = {
        "sub": "test-user-123",
        "email": "test@example.com",
        "name": "Test User",
        "roles": ["user"],
        "scope": "bookverse:api"
    }
    return AuthUser(mock_claims)


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def setup_database():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def test_health_endpoint(setup_database, client):
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["service"] == "BookVerse Inventory Service"
    assert "timestamp" in data


def test_info_endpoint(setup_database, client):
    response = client.get("/info")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "BookVerse Inventory Service"
    assert "version" in data


def test_list_books_empty(setup_database, client):
    response = client.get("/api/v1/books")
    assert response.status_code == 200

    data = response.json()
    assert "books" in data
    assert "pagination" in data
    assert data["pagination"]["total"] == 0
    assert len(data["books"]) == 0


def test_create_book(setup_database, client):
    book_data = {
        "title": "Test Book",
        "subtitle": "A Demo Book",
        "authors": ["Test Author"],
        "genres": ["test", "demo"],
        "description": "This is a test book for demo purposes.",
        "price": "19.99",
        "cover_image_url": "https://example.com/cover.jpg"
    }

    response = client.post("/api/v1/books", json=book_data)
    assert response.status_code == 201

    data = response.json()
    assert data["title"] == book_data["title"]
    assert data["authors"] == book_data["authors"]
    assert "id" in data
    assert "created_at" in data


def test_get_book_not_found(setup_database, client):
    fake_id = "123e4567-e89b-12d3-a456-426614174000"
    response = client.get(f"/api/v1/books/{fake_id}")
    assert response.status_code == 404


def test_list_inventory_empty(setup_database, client):
    response = client.get("/api/v1/inventory")
    assert response.status_code == 200

    data = response.json()
    assert "inventory" in data
    assert "pagination" in data
    assert data["pagination"]["total"] == 0


def test_list_transactions_empty(setup_database, client):
    response = client.get("/api/v1/transactions")
    assert response.status_code == 200

    data = response.json()
    assert "transactions" in data
    assert "pagination" in data
    assert data["pagination"]["total"] == 0


def test_inventory_adjust_nonexistent_book(setup_database, client):
    fake_id = "123e4567-e89b-12d3-a456-426614174000"
    adjustment_data = {
        "quantity_change": 10,
        "notes": "Test adjustment"
    }

    response = client.post(
        f"/api/v1/inventory/adjust?book_id={fake_id}",
        json=adjustment_data
    )
    assert response.status_code == 200

    data = response.json()
    assert data["quantity_change"] == 10
    assert data["transaction_type"] == "stock_in"


if __name__ == "__main__":
    pytest.main([__file__])
