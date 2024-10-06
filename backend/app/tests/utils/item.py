import uuid

from sqlmodel import Session

from app.models import Item, User
from app.tests.utils.user import create_random_user
from app.tests.utils.utils import random_lower_string


def create_random_item(
    db: Session,
    title: str | None = None,
    description: str | None = None,
    user: User | uuid.UUID | None = None,
    *,
    commit: bool = True,
) -> Item:
    """
    Create random item in the given database session.

    :param db: Database session to add the item to.
    :param title: Overwrite title.
    :param description: Overwrite item description.
    :param user: Overwrite item owner, either ``ìnt`` or :class:`User
    :param commit: Whether to commit the transaction or not. (default: ``True``).
    :return: Created item.
    """
    if user is None:
        user = create_random_user(db)
    if isinstance(user, int):
        user_key = "owner_id"
    else:
        user_key = "owner"
    if title is None:
        title = random_lower_string()
    if description is None:
        description = random_lower_string()
    item = Item(title=title, description=description, **{user_key: user})
    db.add(item)
    if commit:
        db.commit()
        db.refresh(item)
    return item
