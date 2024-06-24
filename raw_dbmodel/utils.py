from typing import Any


def is_dict_or_str(_type: Any):
    return isinstance(_type, dict) or isinstance(_type, str)


def is_list_str_or_none(_type: Any):
    return (isinstance(_type, list) and all(isinstance(value, str) for value in _type)) or _type is None
