from collections.abc import Generator
from contextlib import contextmanager
from typing import Protocol

from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app import crud
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import User, UserCreate, UserUpdate
from app.tests.utils.utils import random_email, random_lower_string


def user_authentication_headers(
    *, client: TestClient, email: str, password: str
) -> dict[str, str]:
    data = {"username": email, "password": password}

    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    assert r.status_code == 200
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


def create_random_user(
    db: Session,
    email: str | None = None,
    password: str | None = None,
    full_name: str | None = None,
    is_active: bool | None = None,
    is_superuser: bool | None = None,
    *,
    hash_password: bool = True,
    commit: bool = True,
) -> User:
    """
    Create a random user in the given database session.

    Provided parameters will overwrite random values.
    By default, password will not be hashed to increase performance of tests.

    :param db: Database session to add the user to.
    :param email: Overwrite ``username``.
    :param password: Overwrite ``password``.
    :param full_name: Overwrite ``full_name``
    :param is_active: Overwrite ``is_active``.
    :param is_superuser: Overwrite ``is_superuser``.
    :param hash_password: Whether to hash the password or not. (default ``True``)
    :param commit: Whether to commit the transaction to the database. (default: ``True``)
    :return: Created user.
    """
    if email is None:
        email = random_email()
    if password is None:
        password = random_lower_string()
    password = get_password_hash(password) if hash_password else password
    user = User(
        email=email,
        hashed_password=password,
        full_name=full_name,
        is_active=is_active,
        is_superuser=is_superuser,
    )
    db.add(user)
    if commit:
        db.commit()
        db.refresh(user)
    return user


class CreateUserProtocol(Protocol):
    def __call__(
        self,
        email: str | None = ...,
        password: str | None = ...,
        full_name: str | None = ...,
        is_active: bool | None = ...,
        is_superuser: bool | None = ...,
        *,
        hash_password: bool = ...,
        commit: bool = ...,
        cleanup: bool = ...,
    ) -> User:
        ...


@contextmanager
def create_user_context(db: Session) -> Generator[CreateUserProtocol, None, None]:
    """
    Context Manager to return a user factory that can be used to create users in the given database.
    """
    created = []

    def factory(
        email: str | None = None,
        password: str | None = None,
        full_name: str | None = None,
        is_active: bool | None = None,
        is_superuser: bool | None = None,
        *,
        hash_password: bool = True,
        commit: bool = True,
        cleanup: bool = True,
    ) -> User:
        user = create_random_user(
            db=db,
            email=email,
            password=password,
            full_name=full_name,
            is_active=is_active,
            is_superuser=is_superuser,
            hash_password=hash_password,
            commit=commit,
        )
        if cleanup:
            created.append(user)
        return user

    yield factory
    # cleanup
    stmt = delete(User).where(User.id.in_(u.id for u in created))
    db.execute(stmt)


def authentication_token_from_email(
    *, client: TestClient, email: str, db: Session
) -> dict[str, str]:
    """
    Return a valid token for the user with given email.

    If the user doesn't exist it is created first.
    """
    password = random_lower_string()
    user = crud.get_user_by_email(session=db, email=email)
    if not user:
        user_in_create = UserCreate(email=email, password=password)
        user = crud.create_user(session=db, user_create=user_in_create)
    else:
        user_in_update = UserUpdate(password=password)
        if not user.id:
            raise Exception("User id not set")
        user = crud.update_user(session=db, db_user=user, user_in=user_in_update)

    return user_authentication_headers(client=client, email=email, password=password)
