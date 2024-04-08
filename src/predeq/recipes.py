import re

from ._predeq import predeq


NOT_NONE = predeq(lambda obj: obj is not None, repr='<NOT_NONE>')


def exception(exc: BaseException) -> predeq:
    return predeq(
        lambda obj: isinstance(obj, type(exc)) and obj.args == exc.args,
        repr=f'{exception.__name__}({exc!r})',
    )


def matches_re(regex) -> predeq:
    pattern = re.compile(regex)
    return predeq(
        lambda obj: isinstance(obj, str) and pattern.match(obj) is not None,
        repr=f'{matches_re.__name__}({pattern.pattern!r})',
    )
