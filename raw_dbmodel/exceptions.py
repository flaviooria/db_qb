from raw_dbmodel._types import DictOrStr

__all__ = (
    "ModeOperatorError", "ParameterTypeError", "DictOrStrType", "ListStrOrNoneType"
)


def __dir__() -> list[str]:
    return sorted(list(__all__))


DictOrStrType = 12
ListStrOrNoneType = 2


class ModeOperatorError(Exception):
    """
    Exception raised when mode to execute raw sql is incorrect
    """

    def __init__(self, msg: str):
        super().__init__(msg)


class ParameterTypeError(TypeError):
    """
    Exception raised when a parameter is not valida type
    """

    def __init__(self, code: int, msg: str = None):
        self.code = code
        self.msg = "The parameter is not a valid instance or type of:"

        if code == DictOrStrType:
            self.msg += f" {DictOrStr.__class__.__name__}"

        if code == ListStrOrNoneType:
            self.msg += f" {ListStrOrNoneType.__class__.__name__}"

        if msg is not None:
            self.msg = msg

        super().__init__(self.msg)
