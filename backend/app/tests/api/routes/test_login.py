from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.core.security import verify_password
from app.models import User
from app.tests.utils.user import CreateUserProtocol, user_authentication_headers
from app.tests.utils.utils import random_lower_string
from app.utils import generate_password_reset_token


def test_get_access_token(client: TestClient, create_user: CreateUserProtocol) -> None:
    password = random_lower_string()
    user = create_user(password=password)
    login_data = {"username": user.email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]


def test_get_access_token_incorrect_password(
    client: TestClient, normal_user: User
) -> None:
    login_data = {"username": normal_user.email, "password": "incorrect"}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 400


def test_use_access_token(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers=superuser_token_headers,
    )
    result = r.json()
    assert r.status_code == 200
    assert "email" in result


def test_recovery_password(client: TestClient, create_user: CreateUserProtocol) -> None:
    password = random_lower_string()
    user = create_user(is_superuser=False, password=password)
    auth_headers = user_authentication_headers(
        client=client, email=user.email, password=password
    )
    with (
        patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("app.core.config.settings.SMTP_USER", "admin@example.com"),
    ):
        r = client.post(
            f"{settings.API_V1_STR}/password-recovery/{user.email}",
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json() == {"message": "Password recovery email sent"}


def test_recovery_password_user_not_exits(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    email = "jVgQr@example.com"
    r = client.post(
        f"{settings.API_V1_STR}/password-recovery/{email}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404


def test_reset_password(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
    create_user: CreateUserProtocol,
) -> None:
    user = create_user(is_superuser=True)
    token = generate_password_reset_token(email=user.email)
    data = {"new_password": random_lower_string(), "token": token}
    r = client.post(
        f"{settings.API_V1_STR}/reset-password/",
        headers=superuser_token_headers,
        json=data,
    )
    assert r.status_code == 200
    assert r.json() == {"message": "Password updated successfully"}

    db.refresh(user)
    assert verify_password(data["new_password"], user.hashed_password)


def test_reset_password_invalid_token(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    data = {"new_password": random_lower_string(), "token": "invalid"}
    r = client.post(
        f"{settings.API_V1_STR}/reset-password/",
        headers=superuser_token_headers,
        json=data,
    )
    response = r.json()

    assert "detail" in response
    assert r.status_code == 400
    assert response["detail"] == "Invalid token"
