from predeq.recipes import NOT_NONE, exception, matches_re


def test_not_none():
    assert {} == NOT_NONE


def test_exception():
    exc = LookupError('fridge does not contain food')
    assert exc == exception(exc)


def test_matches_re():
    pred = matches_re(r'\d{3}$')
    assert '123' == pred
    assert '1234' != pred
