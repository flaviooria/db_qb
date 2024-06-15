from typing import List

from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine
from typing_extensions import Type

from raw_dbmodel.settings import config

engine: Engine = create_engine(config.uri, echo=False)


def create_tables(models: List[Type]):
    tables: list[Type[SQLModel]] = []
    for _cls in models:
        if isinstance(_cls, type):
            try:
                if issubclass(_cls, SQLModel) and _cls is not SQLModel and hasattr(_cls, '__table__'):
                    tables.append(_cls)
                else:
                    print(f"{_cls.__name__} class is not a table")
            except TypeError as te:
                print(te)

    if len(tables) > 0:
        print_tables = [f"{cls.__name__} class has been added as table name: {cls.__tablename__}" for cls in tables]
        print(*print_tables, sep='\n')
        SQLModel.metadata.create_all(bind=engine, tables=[cls.__table__ for cls in tables if hasattr(cls, '__table__')])
    else:
        print('Could not create the tables, check that the imported classes are correct.')


__all__ = ["engine", "create_tables"]


def __dir__() -> list[str]:
    return sorted(list(__all__))
