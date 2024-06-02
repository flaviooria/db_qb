from typing import Type

from db_query_builder import Repository
from tests.domain import User


class UserRepository(Repository[User]):

    def __init__(self, **kwargs) -> None:
        super().__init__(User, **kwargs)

    @property
    def model(self) -> Type[User]:
        return User
