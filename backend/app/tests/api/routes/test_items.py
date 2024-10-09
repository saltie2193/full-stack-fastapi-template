import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import Item, User
from app.tests.conftest import CreateItemProtocol, CreateItemsProtocol
from app.tests.utils.user import CreateUserProtocol, user_authentication_headers
from app.tests.utils.utils import random_lower_string


@pytest.mark.parametrize(
    "is_superuser", (True, False), ids=lambda x: "superuser" if x else "normal user"
)
def test_create_item(
    db: Session, client: TestClient, create_user: CreateUserProtocol, is_superuser: bool
) -> None:
    password = random_lower_string()
    user = create_user(is_superuser=is_superuser, password=password)
    auth_headers = user_authentication_headers(
        client=client, email=user.email, password=password
    )
    data = {"title": random_lower_string(), "description": random_lower_string()}

    response = client.post(
        f"{settings.API_V1_STR}/items/",
        headers=auth_headers,
        json=data,
    )

    assert response.status_code == 200
    api_item = response.json()
    assert api_item
    assert "id" in api_item
    assert api_item["title"] == data["title"]
    assert api_item["description"] == data["description"]
    assert api_item["owner_id"] == str(user.id)

    # item exists in database and values match the api output?
    stmt = select(Item).filter_by(title=data["title"], description=data["description"])
    db_item = db.exec(stmt).one_or_none()
    assert db_item
    # api response as expected data since we already checked the relevant fields
    assert db_item.model_dump(mode="json") == api_item

    # cleanup
    db.delete(db_item)
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


@pytest.mark.parametrize("item_count", (0, 1, 10))
def test_read_items_as_superuser(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    create_items: CreateItemsProtocol,
    item_count: int,
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


@pytest.mark.parametrize("owned_count", (0, 1, 10))
def test_read_items_as_normal_user(
    db: Session,
    client: TestClient,
    normal_user: User,
    normal_user_token_headers: dict[str, str],
    create_item: CreateItemProtocol,
    owned_count: int,
) -> None:
    owned_tmp = [
        create_item(commit=False, user=normal_user) for _ in range(owned_count)
    ]
    foreign_tmp = [create_item(commit=False) for _ in range(10)]
    db.commit()

    items: dict[uuid.UUID, list[dict[str, str]]] = {}
    for item in (*owned_tmp, *foreign_tmp):
        db.refresh(item)
        key = item.owner_id
        if key not in items:
            items[key] = [item.model_dump(mode="json", exclude={"hashed_password"})]
        else:
            items[key].append(item.model_dump(mode="json", exclude={"hashed_password"}))

    response = client.get(
        f"{settings.API_V1_STR}/items/",
        headers=normal_user_token_headers,
    )

    assert response.status_code == 200
    content = response.json()
    assert content["count"] == len(content["data"])
    assert content["count"] == owned_count
    assert len(content["data"]) == owned_count

    assert sorted(content["data"], key=lambda i: i["id"]) == sorted(
        items.get(normal_user.id, []), key=lambda i: i["id"]
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
