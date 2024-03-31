"""
Hint: `PYTEST _DONT _REWRITE` in docstring (spelled with no spaces) disables assertion rewrite,
and causes co_positions to be correct and inspect.getsource() returning less context
"""

from predeq import predeq


class Callable:
    def __call__(self, obj):
        return not obj


def test_predeq():
    assert 2 != predeq(lambda obj: obj % 3 == 0)
    assert {'a': 1, 'b': 2} == {'a': 1, 'b': predeq(lambda obj: obj % 2 == 0)}


def test_lambda_single_line():
    assert repr(predeq(lambda obj: obj % 2 == 0)) == '<lambda obj: obj % 2 == 0>'


def test_lambda_multiline():
    assert repr(predeq(
        lambda obj: obj % 2 == 0
    )) == '<lambda obj: obj % 2 == 0>'


def test_inner_func():
    def pred(obj):
        return obj is None

    assert repr(predeq(pred)) == '<def pred(obj):\n        return obj is None>'


def test_lambda_with_capture():
    captured = 123
    assert repr(predeq(lambda obj: obj + captured)) == '<lambda obj: obj + captured>'


def test_custom_callable():
    assert repr(predeq(Callable())) == '<def __call__(self, obj):\n        return not obj>'
