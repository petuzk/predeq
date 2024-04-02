"""
Hint: `PYTEST _DONT _REWRITE` in docstring (spelled with no spaces) disables assertion rewrite,
and causes co_positions to be correct and inspect.getsource() returning less context
"""

import pytest

from predeq import predeq


# Test source code finder with both "short" and "long" path (see _ENABLE_ONE_NODE_SHORT_PATH).
# The goal is to test "production" version ("short" path), but also test bytecode comparison
# more thoroughly by having more testcases running into it ("long" path).
pytestmark = pytest.mark.parametrize('enable_one_node_short_path', (True, False), indirect=True, ids=('short', 'long'))


@pytest.fixture(autouse=True)
def enable_one_node_short_path(monkeypatch, request):
    monkeypatch.setattr('predeq._predeq._ENABLE_ONE_NODE_SHORT_PATH', request.param)


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


class Callable:
    def __call__(self, obj):
        return not obj


def test_custom_callable():
    assert repr(predeq(Callable())) == '<def __call__(self, obj):\n        return not obj>'
