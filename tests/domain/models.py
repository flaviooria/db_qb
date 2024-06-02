from uuid import uuid4

from sqlmodel import Field

from tests.domain.schema import UserBase


class User(UserBase, table=True):
    __tablename__ = 'usuarios'

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
