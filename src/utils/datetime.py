import time
from pathlib import Path
from typing import Union


def seconds_since_creation(path: Union[str, Path]) -> float:
    """
    Return the number of seconds elapsed since the file at 'path' was created.

    Parameters:
    -----------
    path : str | Path
        The filesystem path to the file.

    Returns:
    --------
    float
        Seconds elapsed since file creation.

    Raises:
    -------
    FileNotFoundError
        If the file does not exist.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"No such file: {file_path!s}")

    created_ts = file_path.stat().st_ctime

    now_ts = time.time()

    return now_ts - created_ts
