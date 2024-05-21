from predeq import predeq


def test_predeq():
    assert 2 != predeq(lambda obj: obj % 3 == 0)
    assert {'a': 1, 'b': 2} == {'a': 1, 'b': predeq(lambda obj: obj % 2 == 0)}


def test_predeq_returns_bool():
    # with predicate returning passed object, verify that the result of comparison is bool
    truthy = predeq(lambda x: x)

    assert ('' == truthy) is False
    assert ('abc' == truthy) is True
