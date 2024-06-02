import unittest

import tests.domain.models as models
from db_query_builder import InitConnection
from tests.domain import User
from tests.domain.schema import UserSchema
from tests.respositories.user_respository import UserRepository


class MyTestCase(unittest.TestCase):

    def setUp(self):
        InitConnection(models)
        self.userRepository = UserRepository()

    def test_create_table(self):
        user = UserSchema(name='test', email='test@dev', password='test')
        user_to_create = User.model_validate(user)
        user_created = self.userRepository.create(user_to_create)

        self.assertEqual(user_created, user_to_create)

    def test_get_all(self):
        users = self.userRepository.get_all()

        self.assertGreater(len(users), 1, "List is empty")


if __name__ == '__main__':
    unittest.main()
