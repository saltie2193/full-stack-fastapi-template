import uuid
from collections.abc import Generator, Iterable, Sequence
from typing import Protocol

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.db import engine
from app.main import app
from app.models import Item, User
from app.tests.utils.item import create_random_item
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


class CreateItemProtocol(Protocol):
    def __call__(
        self,
        title: str | None = ...,
        description: str | None = ...,
        user: User | uuid.UUID | None = ...,
        *,
        cleanup: bool = True,
        commit: bool = True,
    ) -> Item:
        ...


@pytest.fixture(scope="function")
def create_item(
    db: Session, create_user: CreateUserProtocol
) -> Generator[CreateItemProtocol, None, None]:
    """Returns factory to create function scoped items.

    Factory will create random users with the same scope if they are not provided.
    Passwords of created users will NOT be hashed. Thus authenticating as them is not directly possible.
    """
    created: list[Item] = []

    def factory(
        title: str | None = None,
        description: str | None = None,
        user: User | uuid.UUID | None = None,
        *,
        cleanup: bool = True,
        commit: bool = True,
    ) -> Item:
        """Create a function scoped random item, with the provided overrides.

        If a user is not provided a random function scoped user will be created.
        """
        if user is None:
            user = create_user(hash_password=False)
        item = create_random_item(
            db=db, title=title, description=description, user=user, commit=commit
        )
        if cleanup:
            created.append(item)
        return item

    yield factory


class CreateItemsProtocol(Protocol):
    def __call__(
        self,
        count: int,
        user: User | uuid.UUID | None = ...,
        users: Iterable[User | uuid.UUID | None] | None = ...,
        *,
        commit: bool = ...,
        cleanup: bool = ...,
    ) -> Sequence[Item]:
        ...


@pytest.fixture(scope="function")
def create_items(db: Session, create_item: CreateItemProtocol) -> CreateItemsProtocol:
    """Get factory to create items in bulck

    Factory will create the given number of items per specified user.
    Providing ``count=5`` and a total number of 4 users will create 20 itmes in total.
    Users can either be provided via ``user`` or ``users``. If both are provided, the ``user`` will be added to ``users``.
    If a user is present multiple times he will process multiple times.
    If no user is provided, the items will be created using random new users with the same scope.
    Providing ``None`` in ``users`` will result in creation of a random user.
    """

    def factory(
        count: int,
        user: User | uuid.UUID | None = None,
        users: Iterable[User | uuid.UUID | None] | None = None,
        *,
        commit: bool = True,
        cleanup: bool = True,
    ) -> Sequence[Item]:
        if users is None:
            users = ()
        _users = (user, *users)

        items: list[Item] = []
        for _ in range(count):
            items.extend(
                create_item(user=_user, commit=False, cleanup=cleanup)
                for _user in _users
            )
        if commit:
            db.commit()
            for item in items:
                db.refresh(item)

        return items

    return factory
