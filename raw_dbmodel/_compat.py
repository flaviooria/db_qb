from datetime import datetime
from functools import wraps
from typing import (Callable, Type, Optional, Union, Any, List, Dict)

import pandas as pd
import sqlalchemy.sql
from pandas import DataFrame
from sqlalchemy import Connection, CursorResult, text
from sqlmodel import inspect
from typing_extensions import Generic

from raw_dbmodel._abstracts import RepositoryAbstract
from raw_dbmodel._types import _T, TypeMode, DictOrStr, ListStrOrNone
from raw_dbmodel.database import engine as engine
from raw_dbmodel.exceptions import ModeOperatorError, ParameterTypeError, DictOrStrType, ListStrOrNoneType
from raw_dbmodel.utils import is_dict_or_str, is_list_str_or_none


class DotDict(dict):
    """
    class to map the data in dictionary and access it through the dot
    """

    def __getattr__(self, key):

        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'Object has no attribute '{key}'")

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(f"'Object has no attribute '{key}'")


class RepositoryBase(Generic[_T], RepositoryAbstract):

    def __init__(self) -> None:

        try:
            if engine is None:
                raise Exception('Engine not could None')

            self.__engine = engine
        except Exception:
            raise

        self.__model: Optional[Type[_T]] = None
        self.__fields = "*"
        self.__query = ""

    @staticmethod
    def transaction(func: Callable[..., Union[DataFrame, CursorResult[Any]]]):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            with engine.begin() as connection:
                return func(self, connection, *args, **kwargs)

        return wrapper

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
            new_value = f"{sqlalchemy.sql.null()}{separator}"

        return new_value

    @classmethod
    def __get_where_conditions(cls, where: DictOrStr,
                               operators: ListStrOrNone = None):

        if not is_dict_or_str(where):
            raise ParameterTypeError(DictOrStrType)

        if not is_list_str_or_none(operators):
            raise ParameterTypeError(ListStrOrNoneType)

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

    @transaction
    def __execute(self, connection: Optional[Connection], /, statement: Union[str, Type[_T]],
                  parameters: Optional[Union[List[Type[_T]], Dict[str, Any]]] = None, *,
                  mode: TypeMode = 'sql') -> \
            DataFrame | CursorResult[Any]:
        try:

            if mode != 'sql' and mode != 'as_pd':
                raise ModeOperatorError(
                    'Mode not is \'sql\' or \'as_pd\'')

            if mode == 'as_pd':
                return pd.read_sql_query(text(statement), connection)

            if parameters is not None:
                return connection.execute(statement, parameters)

            return connection.execute(text(statement))

        except Exception:
            raise

    def fields(self, fields: str) -> 'RepositoryBase[_T]':
        self.__fields = fields

        return self

    def insert(self, model: Type[_T], *, have_autoincrement_default: bool = True) -> _T:
        model_dict: dict = model.model_dump()

        if not have_autoincrement_default:
            table = inspect(self.model).tables[0]
            columns_key = [column.name for column in table.primary_key.columns]

            for field_key in columns_key:
                for key in model_dict.keys():
                    if field_key == key:
                        model_dict.pop(field_key)
                        break

        _columns = ', '.join(model_dict.keys())
        _values = ''
        field_values = model_dict.values()

        for index, value in enumerate(field_values):
            separator = ', '

            if index == len(field_values) - 1:
                separator = ' '

            _values += self.__get_value_formated(value, separator)

        _sql = f"insert into {model.__tablename__} ({_columns}) values ({_values});"

        try:
            self.__execute(_sql)
            return model
        except ModeOperatorError:
            raise
        except Exception:
            raise

    def insert_all(self, *, models: List[Type[_T]], have_autoincrement_default: bool = True) -> bool:
        try:

            models = [{**data.model_dump()} for data in models]
            _sql = self.model.__table__.insert()

            if not have_autoincrement_default:
                table = inspect(self.model).tables[0]
                columns_key = [
                    column.name for column in table.primary_key.columns]

                for field_key in columns_key:
                    for model in models:
                        if field_key in model.keys():
                            model.pop(field_key)
                            continue

                _columns = ', '.join(models[0].keys())
                _values = ', '.join(f":{key}" for key in models[0].keys())

                _sql = f"insert into {self.model.__tablename__} ({_columns}) values ({_values})"

            result = self.__execute(_sql, models)

            return bool(result.rowcount)
        except Exception:
            raise

    def get_data(self) -> 'RepositoryBase[_T]':
        self.__query = f"select {self.__fields} from {self.model.__tablename__}"

        return self

    def get_all(self, model: Optional[Type[_T]] = None) -> Optional[List[_T]]:

        if model is not None:
            self.model = model

        if self.model is None:
            raise Exception('Property model not implemented')

        _sql = f"select * from {self.model.__tablename__}"

        generic_models: List[Type[_T]] = []
        models_from_db = self.__execute(_sql, mode='as_pd')

        list_model = models_from_db.to_dict('records')

        for model in list_model:
            inherited_model = self.model(**model)
            generic_models.append(inherited_model)

        return generic_models

    def get_one(self, where: DictOrStr,
                operators: ListStrOrNone = None) -> 'RepositoryBase[_T]':

        if not is_dict_or_str(where):
            raise ParameterTypeError(DictOrStrType)

        if not is_list_str_or_none(operators):
            raise ParameterTypeError(ListStrOrNoneType)

        if self.model is None:
            raise NotImplementedError('Property model not implemented')

        _where = self.__get_where_conditions(where, operators)

        _sql = f"select {self.__fields} from {self.model.__tablename__} where {_where};"

        self.__query = _sql

        return self

    def update(self, set_fields: DictOrStr, where: DictOrStr,
               operators: ListStrOrNone = None) -> bool:

        if not is_dict_or_str(set_fields):
            raise ParameterTypeError(DictOrStrType)

        if not is_dict_or_str(where):
            raise ParameterTypeError(DictOrStrType)

        if not is_list_str_or_none(operators):
            raise ParameterTypeError(ListStrOrNoneType)

        _set = ''
        _where = ''

        if self.model is None:
            raise NotImplementedError('Property model not implemented')

        if isinstance(set_fields, str):
            _set = set_fields

        if isinstance(set_fields, dict):
            for index, (field, value) in enumerate(set_fields.items()):
                _set += f"{field} = "
                separator = ', '

                if index == (len(set_fields.values()) - 1):
                    separator = ' '

                _set += self.__get_value_formated(value, separator)

        _where = self.__get_where_conditions(where, operators)

        _sql = f"update {self.model.__tablename__} set {_set} where {_where};"

        result = self.__execute(_sql)

        return bool(result.rowcount)

    def delete(self, where: DictOrStr, operators: ListStrOrNone = None) -> bool:

        if not is_dict_or_str(where):
            raise ParameterTypeError(DictOrStrType)

        if not is_list_str_or_none(operators):
            raise ParameterTypeError(ListStrOrNoneType)

        _where = ''

        _where = self.__get_where_conditions(where, operators)

        _sql = f"delete from {self.model.__tablename__} where {_where}"

        result = self.__execute(_sql)

        return bool(result.rowcount)

    def as_model(self) -> Optional[_T]:
        if self.__query != "":
            model_found = self.__execute(self.__query, mode='as_pd')

            if model_found.empty:
                return None

            model = model_found.to_dict('records')[0]

            return self.model(**model)
        return None

    def as_dict(self) -> Optional[DotDict]:
        if self.__query != "":
            model_found = self.__execute(self.__query, mode='as_pd')

            if model_found.empty:
                return None

            model = model_found.to_dict('records')[0]

            return DotDict(model)
        return None

    def as_df(self) -> Optional[DataFrame]:
        if self.__query != "":
            model_found = self.__execute(self.__query, mode='as_pd')

            if model_found.empty:
                return None

            return model_found

        return None
