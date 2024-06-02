import re

from ._predeq import predeq

__all__ = (
    'ANY',
    'NOT_NONE',
    'exception',
    'instanceof',
    'matches_re',
)

# Assign to __doc__ of module attributes below for nicer help(),
# and for sphinx to find the documentation of these imported in __init__.
# See https://github.com/sphinx-doc/sphinx/issues/6495


ANY = predeq(lambda _: True, repr='<ANY>')
ANY.__doc__ = \
    """
    An object which compares equal to any object.
    Semantically equivalent to :external:py:data:`unittest.mock.ANY`, but implemented with :func:`predeq`.
    """

NOT_NONE = predeq(lambda obj: obj is not None, repr='<NOT_NONE>')
NOT_NONE.__doc__ = \
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

    The equality is determined by :func:`isinstance`.

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
        repr=f'{instanceof.__name__}({", ".join(map(_repr_class, classes))})'
    )


def _repr_class(klass):
    return klass.__name__ if isinstance(klass, type) else repr(klass)


def matches_re(regex: 'str | re.Pattern') -> predeq:
    """Create an object which compares equal to strings matching the regular expression pattern.

    Return True if zero or more characters at the beginning of the tested string
    match the regular expression (:func:`re.match` behavior).

        >>> 'abc123' == matches_re(r'[a-z]+')
        True

    The behavior of :func:`re.fullmatch` can be enabled by using a dollar sign, which matches end of string.

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
