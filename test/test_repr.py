"""
Hint: `PYTEST _DONT _REWRITE` in docstring (spelled with no spaces) disables assertion rewrite,
and causes co_positions to be correct and inspect.getsource() returning less context
"""

import sys

import pytest

from predeq import predeq


# Test source code finder with both "short" and "long" path (see _ENABLE_ONE_NODE_SHORT_PATH).
# The goal is to test "production" version ("short" path), but also test bytecode comparison
# more thoroughly by having more testcases running into it ("long" path).
pytestmark = pytest.mark.parametrize('enable_one_node_short_path', (True, False), indirect=True, ids=('short', 'long'))

# not mark.skip to ensure that the testcase indeed fails on pre-3.11
requires_3_11 = pytest.mark.xfail(sys.version_info <= (3, 11), reason='requires python3.11 or higher')


@pytest.fixture(autouse=True)
def enable_one_node_short_path(monkeypatch, request):
    monkeypatch.setattr('predeq._predeq._ENABLE_ONE_NODE_SHORT_PATH', request.param)


def test_lambda_single_line():
    assert repr(predeq(lambda obj: obj % 2 == 0)) == '<predeq to meet lambda obj: obj % 2 == 0>'


def test_lambda_multiline():
    assert repr(predeq(
        lambda obj: obj % 2 == 0
    )) == '<predeq to meet lambda obj: obj % 2 == 0>'


def test_inner_func():
    def is_none(obj):
        return obj is None

    assert repr(predeq(is_none)) == '<predeq to meet is_none>'


def test_lambda_with_capture():
    # captured variables are retrieved using different instruction, so bytecode will differ
    # this test ensures that this is taken into account when recompiling source AST
    captured = 123
    assert repr(predeq(lambda obj: obj + captured)) == '<predeq to meet lambda obj: obj + captured>'


def test_callable_instance():
    class Negator:
        def __call__(self, obj):
            return not obj

        def __repr__(self) -> str:
            return f'{type(self).__name__}()'

    assert repr(predeq(Negator())) == '<predeq to meet Negator()>'


def test_lambda_with_default_param():
    assert repr(predeq(lambda obj, isinst=isinstance: isinst(obj, str))) == (
        '<predeq to meet lambda obj, isinst=isinstance: isinst(obj, str)>'
    )

    assert repr(predeq(lambda obj, *, isinst=isinstance: isinst(obj, str))) == (
        '<predeq to meet lambda obj, *, isinst=isinstance: isinst(obj, str)>'
    )

    assert repr(predeq(lambda obj, /, isinst=isinstance: isinst(obj, str))) == (
        '<predeq to meet lambda obj, /, isinst=isinstance: isinst(obj, str)>'
    )


@requires_3_11
def test_lambda_in_dict():
    dummy_dict = {
        'result': 'error',
        'message': predeq(lambda msg: isinstance(msg, str)),
    }
    assert repr(dummy_dict['message']) == '<predeq to meet lambda msg: isinstance(msg, str)>'


@requires_3_11
def test_multiline_lambda_in_dict():
    dummy_dict = {
        'result': 'error',
        'message': predeq(lambda msg: isinstance(
            msg, str)),
    }
    assert repr(dummy_dict['message']) == '<predeq to meet lambda msg: isinstance(\n            msg, str)>'


@requires_3_11
def test_multiline_lambda_in_dict_utf8():
    dummy_dict = {
        'result': 'error',
        'message': predeq(lambda wiadomość: isinstance(wiadomość, str)),
    }
    assert repr(dummy_dict['message']) == '<predeq to meet lambda wiadomość: isinstance(wiadomość, str)>'
