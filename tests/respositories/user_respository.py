from typing import Type

from raw_dbmodel import Repository
from tests.domain import User


class UserRepository(Repository[User]):

    def __init__(self, **kwargs) -> None:
        super().__init__(User, **kwargs)

    @property
    def model(self) -> Type[User]:
        return User
