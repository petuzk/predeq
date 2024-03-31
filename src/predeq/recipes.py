import re

from ._predeq import predeq


NOT_NONE = predeq(lambda obj: obj is not None)


def exception(exc: BaseException) -> predeq:
    return predeq(lambda obj: isinstance(obj, type(exc)) and obj.args == exc.args)


def matches_re(regex) -> predeq:
    pattern = re.compile(regex)
    return predeq(lambda obj: isinstance(obj, str) and pattern.match(obj) is not None)
