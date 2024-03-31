# predeq

PredEq is a utility library for testing objects using an equivalence predicate.
At its core, the `predeq(predicate)` is an object which tests equal to `X` if `predicate(X)` returns True.

```py
def test_my_api_returns_error():
    response = get_reponse(...)
    assert response == {
        'result': 'error',
        'message': predeq(lambda msg: isinstance(msg, str)),
    }
```
