from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.db import engine
from app.main import app
from app.models import Item, User
from app.tests.utils.user import (
    CreateUserProtocol,
    create_user_context,
    user_authentication_headers,
)
from app.tests.utils.utils import random_lower_string


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
        statement = delete(Item)
        session.execute(statement)
        statement = delete(User)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def create_user(db: Session) -> Generator[CreateUserProtocol]:
    """Returns factory to create function scoped users."""
    with create_user_context(db) as factory:
        yield factory


@pytest.fixture(scope="function")
def normal_user_and_pwd(create_user: CreateUserProtocol) -> tuple[User, str]:
    """Get a function scoped active non superuser and the unhashed password."""
    password = random_lower_string()
    user = create_user(password=password)
    return user, password


@pytest.fixture(scope="function")
def normal_user(normal_user_and_pwd: tuple[User, str]) -> User:
    """Get function scoped active non superuser.

    To get matching authentication headers use ``normal_user_token_headers`` fixture.
    """
    return normal_user_and_pwd[0]


@pytest.fixture(scope="function")
def superuser_token_headers(
    client: TestClient, create_user: CreateUserProtocol
) -> dict[str, str]:
    """Get authentication headers for existing active superuser."""
    password = random_lower_string()
    user = create_user(is_superuser=True, password=password)
    return user_authentication_headers(
        client=client, email=user.email, password=password
    )


@pytest.fixture(scope="function")
def normal_user_token_headers(
    client: TestClient, normal_user_and_pwd: tuple[User, str]
) -> dict[str, str]:
    """Get authentication headers for existing active non superuser.

    Get authentication headers for user returned by ``normal_user`` fixture.
    """
    password = random_lower_string()
    user, password = normal_user_and_pwd
    return user_authentication_headers(
        client=client, email=user.email, password=password
    )
