import ast
import importlib
import os.path
import pathlib
import types
from typing import List

from sqlalchemy import Engine, inspect
from sqlmodel import SQLModel, create_engine
from typing_extensions import Type

from raw_dbmodel.settings import config

engine: Engine = create_engine(config.uri, echo=False)


def __is_package(module: types.ModuleType):
    if module.__file__ is not None:
        return True

    return False


def init_db(module: types.ModuleType):
    try:
        inspector = inspect(engine)

        if len(inspector.get_table_names()) == 0:
            return

        if not __is_package(module):
            raise ModuleNotFoundError(
                f'{module.__name__} not is a valid module or package, not found __init__ file')

        init_file = module.__file__

        if os.path.exists(init_file) and list(pathlib.Path(init_file).parts)[-1] == '__init__.py':
            with open(init_file, 'r') as file:
                # la convierte en un árbol de sintaxis abstracta (AST)
                # El ast.parse convierte un cadena de código y lo convierte en
                # una representación estructurada de codigo fuente
                tree = ast.parse(file.read(), filename=init_file)

                # ass.dump, sirve para pintar el código parseado de manera bonita y legible
                # print(ast.dump(tree, indent=4))

                # ast.walk siver para recorrer todos los nodos del arbol, desde el nodo padre hasta las hijas.
                import_statements = [node for node in ast.walk(
                    tree) if isinstance(node, (ast.Import, ast.ImportFrom))]

                if len(import_statements) == 0:
                    raise Exception(
                        'the init file does not containt any class imports')

                for node_ast in import_statements:

                    if isinstance(node_ast, ast.Import):
                        module_name = node_ast.names[0].name
                    elif isinstance(node_ast, ast.ImportFrom):
                        module_name = node_ast.module

                    # El import_module sirve para importar modulos dinamicamente,
                    # es útil cuando el nombre del modulo en tiempo de ejecución se desconoce
                    imported_module = importlib.import_module(module_name)

                    for c in dir(imported_module):
                        mc = getattr(imported_module, c)

                        if isinstance(mc, type):
                            try:
                                if not issubclass(mc, SQLModel) and mc is not SQLModel:
                                    raise Exception(
                                        f'{imported_module.__name__} module is not subclass of SQLModel')
                            except TypeError as te:
                                # Handle cases where _class is not a class type, skip non-classes
                                print('entra aqui', te)

        # Add classes form module
        for name in dir(module):
            _class = getattr(module, name)
            if isinstance(_class, type):
                try:
                    if issubclass(_class, SQLModel) and _class is not SQLModel and hasattr(_class, '__table__'):
                        # Convert the dictionary to a new immutable dictionary
                        updated_tables = dict(SQLModel.metadata.tables)
                        updated_tables[_class.__tablename__] = _class.__table__
                        SQLModel.metadata.tables = types.MappingProxyType(
                            updated_tables)
                        print(
                            f"{_class.__name__} class has been added as table {_class.__tablename__}")
                except TypeError as te:
                    # Handle cases where _class is not a class type, skip non-classes
                    print(te)

        # Crea todas las tablas registradas
        SQLModel.metadata.create_all(engine)
    except Exception as ex:
        print('El error viene de aquí => ', ex)


def creat_tables(classes: List[Type]):
    tables: list[Type[SQLModel]] = []
    for _cls in classes:
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


__all__ = ["init_db", "engine", "creat_tables"]


def __dir__() -> list[str]:
    return sorted(list(__all__))
