from abc import ABC, abstractmethod
from typing import Generic

from raw_dbmodel._types import _T


class RepositoryAbstract(ABC):
    @property
    @abstractmethod
    def model(self) -> Generic[_T]:
        pass
