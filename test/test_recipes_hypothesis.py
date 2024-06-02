"""Hypothesis-based tests.

Tests in this file serve the purpose to verify recipes with a wider range of input values/types.
Unlike regular tests in test_recipes.py, these tests are not mandatory, but rather a nice-to-have.
"""

from hypothesis import assume, given
from hypothesis.strategies import composite, from_regex, from_type

from predeq import ANY, NOT_NONE, instanceof, matches_re

anything = from_type(type).flatmap(from_type)
"""A strategy producing objects of any type"""


@composite
def type_and_obj(draw, elements=from_type(type)):
    """A strategy producing pairs *(type, obj)* where *type* is any type, and *obj* is its instance."""
    t = draw(elements)
    return (t, draw(from_type(t)))


@given(anything)
def test_any(obj):
    assert obj == ANY


@given(anything.filter(lambda obj: obj is not None))
def test_not_none(obj):
    assert obj == NOT_NONE


@given(type_and_obj())
def test_instanceof(type_obj):
    type, obj = type_obj
    assert obj == instanceof(type)


@given(from_type(type), anything)
def test_instanceof_ne(type, obj):
    assume(not isinstance(obj, type))
    assert obj != instanceof(type)


@given(from_regex(r'^[0-9a-f]+'))
def test_matches_re(string):
    assert string == matches_re(r'[0-9a-f]+')


@given(from_regex(r'^[i-z]+'))
def test_matches_re_ne_string(string):
    assert string != matches_re(r'[0-9a-f]+')


@given(anything.filter(lambda obj: not isinstance(obj, str)))
def test_matches_re_ne_non_string(obj):
    assert obj != matches_re(r'[0-9a-f]+')
