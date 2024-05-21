import pytest

from predeq import ANY, NOT_NONE, exception, instanceof, matches_re


@pytest.mark.parametrize('value, expected_repr', [
    (ANY, '<ANY>'),
    (NOT_NONE, '<NOT_NONE>'),
    (exception(IndexError(42)), 'exception(IndexError(42))'),

    # for types, instanceof shows type.__name__ rather than repr(type)
    (instanceof(str), 'instanceof(str)'),
    (instanceof(int, float), 'instanceof(int, float)'),

    # it is a mistake to pass non-type (e.g. `compile` is a function), show actual repr to make it easier to catch
    # this is not checked by `instanceof`, but will raise on comparison when `isinstance` is called
    (instanceof(compile), 'instanceof(<built-in function compile>)'),

    (matches_re('\\d+'), r"matches_re('\\d+')"),
])
def test_repr(value, expected_repr):
    assert repr(value) == expected_repr
