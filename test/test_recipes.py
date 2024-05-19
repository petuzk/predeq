from predeq import ANY, NOT_NONE, exception, instanceof, matches_re


def test_any():
    assert {} == ANY
    assert None == ANY


def test_not_none():
    assert {} == NOT_NONE
    assert None != NOT_NONE


def test_exception():
    msg = 'fridge does not contain food'
    exc = LookupError(msg)

    assert exc == exception(exc)
    assert KeyError(msg) == exception(exc)

    assert ValueError() != exception(exc)
    assert ValueError(msg) != exception(exc)


def test_instanceof():
    assert {} == instanceof(dict)
    assert 123 == instanceof(int)
    assert False == instanceof(int)

    assert 'abc' != instanceof(int)


def test_matches_re():
    pred = matches_re(r'\d{3}$')
    assert '123' == pred
    assert '1234' != pred

    assert None != pred
    assert 12.34 != pred
