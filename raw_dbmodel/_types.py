from typing import Literal, Any, Dict, TypeVar, Union, Optional, List

from sqlmodel import SQLModel
from typing_extensions import Annotated

_T = TypeVar(name='_T', bound=SQLModel)
TypeMode = Annotated[str, Literal['sql', 'as_pd']]
DictOrStr = Union[Dict[str, Any], str]
ListStrOrNone = Optional[List[str]]
