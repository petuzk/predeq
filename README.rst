======
predeq
======

PredEq is a utility for testing objects using an equivalence predicate. It facilitates writing declarative-style
tests for complex requirements, and for cases where the default ``__eq__`` is inapplicable or missing.

At its core, ``predeq(predicate)`` is an object which tests equal to ``X`` if ``predicate(X)`` returns True.

.. code-block:: python

    from predeq import predeq, instanceof


    def test_tuple_of_2_ints():
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

Since PredEq is primarily designed for tests, it also tries to be helpful when they fail.
If lambda is used as a predicate, ``predeq`` attempts to locate its source code and show it in pytest output::

    >   assert value == (
          predeq(lambda x: isinstance(x, int)),  # provide your own predicate
          instanceof(str),                       # or use one of the recipes
       )
    E   AssertionError: assert (123.0, 'abc') == (<predeq to m...stanceof(str))
    E
    E     At index 0 diff: 123.0 != <predeq to meet lambda x: isinstance(x, int)>
    E     Use -v to get more diff


Each built-in recipe also provides a readable representation, which typically looks like the corresponding code::

    >   assert value == (
          predeq(lambda x: isinstance(x, int)),  # provide your own predicate
          instanceof(str),                       # or use one of the recipes
       )
    E   AssertionError: assert (123, b'abc') == (<predeq to m...stanceof(str))
    E
    E     At index 1 diff: b'abc' != instanceof(str)
    E     Use -v to get more diff
