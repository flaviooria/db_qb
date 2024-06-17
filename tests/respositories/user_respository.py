from raw_dbmodel import Repository
from tests.domain import User


class UserRepository(Repository[User]):

    @property
    def model(self):
        return User
