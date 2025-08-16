"""Warning and error routines.

© Reuben Thomas <rrt@sc3d.org> 2023.

Released under the Apache Software Licence, v2.0.
"""

import sys
from collections.abc import Callable
from typing import NoReturn, TextIO
from warnings import warn


# Error messages
def simple_warning(prog: str) -> Callable[..., None]:
    """Make a simply-formatted `warnings.warn` routine.

    This is suitable for console warnings for a program invoked from the
    terminal.

    Args:
        prog (str): the program's name

    Returns:
        Callable[..., None]: the warning function
    """

    def _warning(
        message: Warning | str,
        category: type[Warning],
        filename: str,
        lineno: int,
        file: TextIO | None = sys.stderr,
        line: str | None = None,
    ) -> None:
        print(f"{prog}: {message}", file=file or sys.stderr)

    return _warning


def die(msg: str, code: int | None = 1) -> NoReturn:
    """Print a fatal error message and exit.

    Args:
        msg (str): the error message
        code (int | None, optional): . Defaults to 1.
    """
    warn(msg)
    sys.exit(code)
