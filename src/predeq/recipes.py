import re

from ._predeq import predeq

__all__ = (
    'ANY',
    'NOT_NONE',
    'exception',
    'instanceof',
    'matches_re',
)


ANY = predeq(lambda _: True, repr='<ANY>')
"""An object which compares equal to any object. Equivalent to `unittest.mock.ANY`, but implemented with `predeq`."""

NOT_NONE = predeq(lambda obj: obj is not None, repr='<NOT_NONE>')
"""An object which compares equal to any object except None."""


def exception(exc: BaseException) -> predeq:
    """Create an object which compares equal to an exception of the same class (or its subclass) with the same args.

        >>> ValueError('invalid literal') == exception(ValueError('invalid literal'))
        True
        >>> KeyError('key') == exception(LookupError('key'))
        True

    """
    return predeq(
        lambda obj: isinstance(obj, type(exc)) and obj.args == exc.args,
        repr=f'{exception.__name__}({exc!r})',
    )


def instanceof(*classes) -> predeq:
    """Create an object which compares equal to an instance of the given class(es) or its subclass(es).

    This is a wrapper for `isinstance` checks, so it behaves exactly like `isinstance` does.

        >>> 2 == instanceof(int)
        True
        >>> 'abc' == instanceof(int, str)
        True
        >>> KeyError('key') == instanceof(LookupError)
        True
        >>> None == instanceof(str)
        False

    """
    return predeq(
        lambda obj: isinstance(obj, classes),
        repr=f'{instanceof.__name__}{classes}'
    )


def matches_re(regex) -> predeq:
    """Create an object which compares equal to strings matching the regular expression pattern.

    Return True if zero or more characters at the beginning of the tested string
    match the regular expression (re.match behavior).

        >>> 'abc123' == matches_re(r'[a-z]+')
        True

    The behavior of re.fullmatch can be enabled by using a dollar sign, which matches end of string.

        >>> 'abc123' == matches_re(r'[a-z]+$')
        False
        >>> 'abcdef' == matches_re(r'[a-z]+$')
        True

    Compiled patterns are accepted as well, which can be used to set flags.

        >>> import re
        >>> 'AbC' == matches_re(re.compile(r'[a-z]+'))
        False
        >>> 'AbC' == matches_re(re.compile(r'[a-z]+', re.IGNORECASE))
        True

    If the tested object is not a string, return False.

        >>> 123 == matches_re(r'[a-z]+')
        False

    """
    pattern = re.compile(regex)
    return predeq(
        lambda obj: isinstance(obj, str) and pattern.match(obj) is not None,
        repr=f'{matches_re.__name__}({pattern.pattern!r})',
    )
