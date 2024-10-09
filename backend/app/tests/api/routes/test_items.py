import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.models import Item
from app.tests.conftest import CreateItemProtocol, CreateItemsProtocol
from app.tests.utils.utils import random_lower_string


def test_create_item(
    db: Session, client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"title": random_lower_string(), "description": random_lower_string()}
    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert "id" in content
    assert "owner_id" in content

    # cleanup
    stmt = delete(Item).filter_by(title=data["title"], description=data["description"])
    db.execute(stmt)
    db.commit()


def test_read_item(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    create_item: CreateItemProtocol,
) -> None:
    item = create_item()
    response = client.get(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == item.title
    assert content["description"] == item.description
    assert content["id"] == str(item.id)
    assert content["owner_id"] == str(item.owner_id)


def test_read_item_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_read_item_not_enough_permissions(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    create_item: CreateItemProtocol,
) -> None:
    item = create_item()
    response = client.get(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_read_items(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    create_items: CreateItemsProtocol,
) -> None:
    item_count = 2
    items = [
        item.model_dump(mode="json", exclude={"hashed_password"})
        for item in create_items(item_count)
    ]

    response = client.get(
        f"{settings.API_V1_STR}/items/",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["count"] == item_count
    assert len(content["data"]) == item_count
    assert sorted(content["data"], key=lambda i: i["id"]) == sorted(
        items, key=lambda i: i["id"]
    )


def test_update_item(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    create_item: CreateItemProtocol,
) -> None:
    item = create_item()
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["description"] == data["description"]
    assert content["id"] == str(item.id)
    assert content["owner_id"] == str(item.owner_id)


def test_update_item_not_found(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    create_item: CreateItemProtocol,
) -> None:
    create_item()
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
        json=data,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_update_item_not_enough_permissions(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    create_item: CreateItemProtocol,
) -> None:
    item = create_item()
    data = {"title": "Updated title", "description": "Updated description"}
    response = client.put(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
        json=data,
    )
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Not enough permissions"


def test_delete_item(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    create_item: CreateItemProtocol,
) -> None:
    item = create_item()
    response = client.delete(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    content = response.json()
    assert content["message"] == "Item deleted successfully"


def test_delete_item_not_found(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    create_item: CreateItemProtocol,
) -> None:
    create_item()
    response = client.delete(
        f"{settings.API_V1_STR}/items/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    content = response.json()
    assert content["detail"] == "Item not found"


def test_delete_item_not_enough_permissions(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    create_item: CreateItemProtocol,
) -> None:
    item = create_item()
    response = client.delete(
        f"{settings.API_V1_STR}/items/{item.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 400
    content = response.json()
    assert content["detail"] == "Not enough permissions"
