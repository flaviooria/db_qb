import unittest

import tests.domain.models as models
from assertpy import add_extension, assert_that, fail
from db_query_builder import InitConnection
from tests.domain import User
from tests.domain.schema import UserSchema
from tests.respositories.user_respository import UserRepository


def exist_field_in_model(self, field: str):
    _field = self.val.model_fields.get(field)

    if _field is None:
        return self.error(f"{field} not found in {self.val.model_fields.keys()}")

    return self


# He creado mi propio método de test para añadirlo como extensión de assertpy
add_extension(exist_field_in_model)


class TestUserRepository(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        InitConnection(models)

    def setUp(self):
        self.userRepository = UserRepository()

    def test_create_user(self):
        user = UserSchema(name='test', email='test@dev', password='test')
        user_to_create = User.model_validate(user)
        user_created = self.userRepository.insert(user_to_create)

        assert_that(user_to_create).is_same_as(user_created)

    def test_insert_all(self):

        user = UserSchema(name='test', email='test@dev', password='test')
        user2 = UserSchema(name='test2', email='tes2t@dev', password='test2')
        user_to_create = User.model_validate(user)
        user_to_create2 = User.model_validate(user2)
        is_insert_all_users = self.userRepository.insert_all(
            models=[user_to_create, user_to_create2])

        assert_that(is_insert_all_users).is_true()

    def test_list_users_is_not_empty(self):
        users = self.userRepository.get_all()

        assert_that(users).is_not_empty()

    def test_field_exist_in_user_model(self):
        user = self.userRepository.fields("name").get_data().to_dict()

        assert_that(user).contains('name')

    def test_validate_user_is_not_none(self):
        user = self.userRepository.get_one(where={'name': 'User'}).to_model()

        assert_that(user).is_not_none()

    def test_validate_that_user_is_instance_user_model(self):
        user = self.userRepository.get_one(where={'name': 'User'}).to_model()

        assert_that(user).is_instance_of(User)

    def test_validate_field_exists_in_user(self):
        user = self.userRepository.get_one(where={'name': 'User'}).to_model()

        users = [user.model_dump()]

        # Evaluamos la listas de users, para ver si la formación existe
        assert_that(users).extracting('name').contains('User')
        assert_that(users).extracting('name').is_equal_to(['User'])

        # Usamos el has_atributo de la clase
        assert_that(user).has_name('User')
        # Usamos nuestra propia función para evaluar el test
        assert_that(user).exist_field_in_model('name')

    def test_validate_if_user_is_type_dict(self):
        user = self.userRepository.get_one(where={'name': 'User'}).to_dict()

        assert_that(user).is_instance_of(dict)

    def test_validate_if_user_is_updated(self):
        is_user_updated = self.userRepository.update(
            {'email': None}, "id = '64653a59-ac2f-4386-a41a-f891bc5ae5cd'")

        assert_that(is_user_updated).is_true()

    def test_validate_if_user_is_deleted(self):
        is_user_deleted = self.userRepository.delete({'email': 'test@dev'})

        assert_that(is_user_deleted).is_true()

    # Failed tests
    def test_validate_if_user_is_not_none_failure(self):
        try:
            user_none = self.userRepository.get_one(
                where={'id': '1'}).to_model()

            assert_that(user_none).is_not_none()
            fail("should have a raise error")
        except AssertionError as ex:
            assert_that(str(ex)).contains('Expected not <None>, but was.')

    def test_validate_if_user_instance_of_model_failure(self):
        try:
            user = self.userRepository.get_one(where={'id': 'User'}).to_model()

            assert_that(user).is_instance_of(User)
            fail("shoul have a raise error")
        except AssertionError as ex:
            assert_that(str(ex)).contains(
                "to be instance of class <User>, but was not")

    def test_validate_if_user_instance_of_dict_failure(self):
        try:
            user = self.userRepository.get_one(where={'id': 'User'}).to_dict()

            assert_that(user).is_instance_of(dict)
            fail("shoul have a raise error")
        except AssertionError as ex:
            assert_that(str(ex)).contains(
                "to be instance of class <dict>, but was not")

    def test_validate_if_field_exist_in_model_failure(self):
        try:
            user = self.userRepository.get_one(
                where={'name': 'User'}).to_dict()

            assert_that([user]).extracting('first_name').contains(['User'])
            fail("should have a raise error")
        except ValueError as ex:
            assert_that(str(ex)).contains('did not contain key <first_name>')

    def test_validate_if_user_is_updated_failure(self):
        try:
            is_user_updated = self.userRepository.update(
                set_fields={'name': 'Carlos'}, where="id = '1'")

            assert_that(is_user_updated).is_true()
            fail("should have a raise error")
        except Exception as ex:
            assert_that(str(ex)).contains('Expected <True>, but was not.')

    def test_validate_if_user_is_deleted_failure(self):
        try:
            is_user_deleted = self.userRepository.delete(where="id = '1'")

            assert_that(is_user_deleted).is_true()
            fail("should have a raise error")
        except Exception as ex:
            assert_that(str(ex)).contains('Expected <True>, but was not.')

    def test_field_exist_in_user_failure(self):
        user = self.userRepository.fields("name").get_data().to_dict()

        assert_that(user).does_not_contain('email')


if __name__ == '__main__':
    unittest.main()
