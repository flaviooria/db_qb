from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

import pandas as pd
from sqlalchemy import Connection, text
from sqlalchemy.exc import OperationalError
from sqlmodel import SQLModel
from typing_extensions import Generic

from db_query_builder.database import engine as engine

_T = TypeVar(name='_T', bound=SQLModel)


class RepositoryBase(Generic[_T]):

    def __init__(self, **kwargs) -> None:

        try:
            if engine is None:
                raise Exception('Engine not could None')

            self.__engine = engine
            self.__connection = self.__get_connection()
        except Exception as ex:
            print('Aquí el error', ex)

        self.__model: Optional[Type[_T]] = None
        self.__fields = "*"
        self.__query = ""

    @classmethod
    def __get_value_formated(cls, value: str, separator: str):
        new_value = ''
        if isinstance(value, str):
            new_value = f"'{value}'{separator}"
        if isinstance(value, int):
            new_value = f"{value}{separator}"
        if isinstance(value, float):
            new_value = f"{value}{separator}"
        if isinstance(value, bool):
            new_value = f"{value}{separator}"
        if isinstance(value, datetime):
            new_value = f"'{value.isoformat()}'{separator}"
        if value is None:
            new_value = f"'null'{separator}"

        return new_value

    @classmethod
    def __get_where_conditions(cls, where: Union[Dict[str, Any], str],
                               operators: Optional[List[str]] = None):

        if isinstance(where, str):
            return where

        if isinstance(where, dict):
            _where = ''

            for index, (field, value) in enumerate(where.items()):
                separator = ' and '
                _where += f"{field} = "

                if operators is not None:
                    if index < len(operators):
                        separator = f' {operators[index]} '

                if index == len(where.values()) - 1:
                    separator = ' '

                _where += cls.__get_value_formated(value, separator)
            return _where

    @property
    def model(self) -> Type[_T]:

        if self.__model is None:
            raise NotImplementedError(
                "You should implement the model property in the subclass")

        return self.__model

    @model.setter
    def model(self, value: Type[_T]):
        self.__model = value

    def __get_connection(self) -> Connection:
        try:
            return self.__engine.connect()
        except OperationalError as e:
            # TODO: luego tendre que lanzar mi propia excepción custom
            raise Exception(
                f"Error de conexión a la base de datos: {e}") from e

    def __execute(self, statement: str):
        try:

            result = self.__connection.execute(text(statement))
            self.__connection.commit()

            return result

        except Exception as ex:
            self.__connection.rollback()
            print('Error => ', ex)

    def fields(self, fields: str) -> 'RepositoryBase[_T]':
        self.__fields = fields

        return self

    def create(self, model: Type[_T], /) -> _T:
        model_dict: dict = model.model_dump()

        _columns = ', '.join(model_dict.keys())
        _values = ''
        field_values = model_dict.values()

        for index, value in enumerate(field_values):
            coma = ', '

            if index == len(field_values) - 1:
                coma = ' '

            _values += self.__get_value_formated(value, coma)

        _sql = f"insert into {model.__tablename__} ({_columns}) values ({_values});"

        try:

            self.__connection.execute(text(_sql))
            self.__connection.commit()

        except Exception as ex:
            self.__connection.rollback()
            print('Error => ', ex)
        finally:
            self.__connection.close()

        return model

    def get_all(self, modelo: Optional[Type[_T]] = None) -> Optional[List[_T]]:

        if modelo is not None:
            self.model = modelo

        if self.model is None:
            raise Exception('Property model not implemented')

        _sql = f"select * from {self.model.__tablename__}"

        generic_models: List[Type[_T]] = []
        models_from_db = pd.read_sql_query(_sql, self.__connection)

        list_model = models_from_db.to_dict('records')

        for model in list_model:
            inherited_model = self.model(**model)
            generic_models.append(inherited_model)

        return generic_models

    def get_one(self, where: Union[Dict[str, Any], str],
                operators: Optional[List[str]] = None) -> 'RepositoryBase[_T]':

        if self.model is None:
            # TODO: luego tendre que lanzar mi propia excepción custom
            raise Exception('Property model not implemented')

        # if isinstance(conditions, str):
        #     _where = conditions
        #
        # if isinstance(conditions, dict):
        #
        #     for index, (field, value) in enumerate(conditions.items()):
        #         separator = ' and '
        #         _where += f"{field} = "
        #
        #         if operators is not None:
        #             if index < len(operators):
        #                 separator = f' {operators[index]} '
        #
        #         if index == len(conditions.values()) - 1:
        #             separator = ' '
        #
        #         _where += self.get_value_formated(value, separator)

        _where = self.__get_where_conditions(where, operators)

        _sql = f"select {self.__fields} from {self.model.__tablename__} where {_where};"

        self.__query = _sql

        return self

    def update(self, set_fields: Union[Dict[str, Any], str], where: Union[Dict[str, Any], str],
               operators: Optional[List[str]] = None) -> bool:
        _set = ''
        _where = ''

        if self.model is None:
            # TODO: luego tendre que lanzar mi propia excepción custom
            raise Exception('Property model not implemented')

        if isinstance(set_fields, str):
            _set = set_fields

        if isinstance(set_fields, dict):
            for index, (field, value) in enumerate(set_fields.items()):
                _set += f"{field} = "
                separator = ', '

                if index == (len(set_fields.values()) - 1):
                    separator = ' '

                _set += self.__get_value_formated(value, separator)

        # if isinstance(where, dict):
        #     for index, (field, value) in enumerate(where.items()):
        #         separator = ' and '
        #         _where += f"{field} = "
        #
        #         if operators is not None:
        #             if index < len(operators):
        #                 separator = f' {operators[index]} '
        #
        #         if index == len(where.values()) - 1:
        #             separator = ' '
        #
        #         _where += self.get_value_formated(value, separator)

        _where = self.__get_where_conditions(where, operators)

        _sql = f"update {self.model.__tablename__} set {_set} where {_where};"

        self.__query = _sql

        result = self.__execute(self.__query)

        return bool(result.rowcount)

    def delete(self, where: Union[Dict[str, Any], str], operators: Optional[List[str]] = None) -> bool:

        _where = ''

        # if isinstance(where, str):
        #     _where = where
        #
        # if isinstance(where, dict):
        #     for index, (field, value) in enumerate(where.items()):
        #         separator = ' and '
        #         _where += f"{field} = "
        #
        #         if operators is not None:
        #             if index < len(operators):
        #                 separator = f' {operators[index]} '
        #
        #         if index == len(where.values()) - 1:
        #             separator = ' '
        #
        #         _where += self.get_value_formated(value, separator)

        _where = self.__get_where_conditions(where, operators)

        _sql = f"delete from {self.model.__tablename__} where {_where}"

        self.__query = _sql

        result = self.__execute(self.__query)

        return bool(result.rowcount)

    def to_model(self) -> Optional[_T]:
        if self.__query != "":
            model_founded = pd.read_sql_query(self.__query, self.__connection)

            if model_founded.empty:
                return None

            model = model_founded.to_dict('records')[0]

            return self.model(**model)
        return None

    def to_dict(self) -> Optional[Dict[str, Any]]:
        if self.__query != "":
            model_founded = pd.read_sql_query(self.__query, self.__connection)

            if model_founded.empty:
                return None

            model = model_founded.to_dict('records')[0]

            return model
        return None


class Repository(RepositoryBase[_T], Generic[_T]):

    def __init__(self, model: Type[_T], /, **kwargs) -> None:
        super().__init__(**kwargs)
        self._model = model

    @property
    def model(self) -> Type[_T]:
        return self._model
