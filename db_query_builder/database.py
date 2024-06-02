import ast
import importlib
import os.path
import pathlib
import types

from sqlalchemy import Engine, inspect
from sqlmodel import SQLModel, create_engine

from db_query_builder.settings import config

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


__all__ = ["init_db", "engine"]


def __dir__() -> list[str]:
    return sorted(list(__all__))
