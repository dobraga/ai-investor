from typing import Any, Optional


def convert_none_str_to_none(value: Any) -> Any:
    """
    Convert a string literal 'None' to actual None, otherwise return the value.
    """
    if isinstance(value, str) and value.lower() == "none" or value == "":
        return None
    return value


def convert_str_to_number(value: Optional[Any]) -> Optional[float]:
    """
    Convert numeric strings to float, or None if value is None or cannot be parsed.
    """
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
