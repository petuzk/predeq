"""Tests provided in README and documentation home page."""

import pytest

from predeq import instanceof, predeq


def test_tuple_of_int_and_str():
    """Test that value is a tuple of an int and a string."""

    value = (123, 'abc')

    # without predeq
    assert isinstance(value, tuple) and len(value) == 2
    assert isinstance(value[0], int)
    assert isinstance(value[1], str)

    # with predeq
    assert value == (
        predeq(lambda x: isinstance(x, int)),  # provide your own predicate
        instanceof(str),                       # or use one of the recipes
    )


# use --runxfail to get output for docs

@pytest.mark.xfail
def test_tuple_of_int_and_str_issue_1():
    value = (123.0, 'abc')

    assert value == (
        predeq(lambda x: isinstance(x, int)),
        instanceof(str),
    )


@pytest.mark.xfail
def test_tuple_of_int_and_str_issue_2():
    value = (123, b'abc')

    assert value == (
        predeq(lambda x: isinstance(x, int)),
        instanceof(str),
    )
