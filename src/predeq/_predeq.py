import ast
from functools import partial
from inspect import getsource, isfunction
from itertools import chain


class predeq:
    def __init__(self, predicate) -> None:
        self.pred = predicate
        self.source = _get_pred_body(predicate)

    def __repr__(self) -> str:
        return '<' + self.source + '>'

    def __eq__(self, other):
        return self.pred(other)


_DUMMY_POSITION = {'lineno': 1, 'col_offset': 0}


def _get_pred_body(predicate) -> 'str | None':
    if not isfunction(predicate) and hasattr(predicate, '__call__'):
        predicate = predicate.__call__

    try:
        full_source = getsource(predicate).strip()
    except OSError:
        return None

    # Problem: the source code returned by inspect.get_source() often has unwanted additional context, such as:
    #   - the statement where lambda is defined (e.g. "x = lambda: None" or "print(getsource(lambda: None))")
    #   - in pytest environment, because of assertion rewrite, source offsets are not entirely correct,
    #     and might include the whole assert statement or even the whole test function.
    # Solution: parse the AST of whatever `getsource()` returns, and find the function or lambda node
    # which compiles to the same bytecode as original predicate. If there is only one function or lambda,
    # we can assume it is the one we need (to avoid unnecessary compilation).

    looking_for_lambda = islambda(predicate)
    nodes = filter_instance(ast.Lambda if looking_for_lambda else ast.FunctionDef, ast.walk(ast.parse(full_source)))

    if (first := next(nodes, None)) is None:
        # no func/lambda node found in AST, should not happen
        return None

    if (second := next(nodes, None)) is None:
        # there is only `first` node, return its source segment
        return ast.get_source_segment(full_source, first)

    # there is more than one, prepend first and second to the iterator and compare by bytecode
    freevars = predicate.__code__.co_freevars
    compile_node = _compile_simple if not freevars else partial(_compile_with_freevars, freevars)
    for node in chain((first, second), nodes):
        code = compile_node(ast.Expr(node, **_DUMMY_POSITION) if looking_for_lambda else node)
        if code.co_code == predicate.__code__.co_code:
            return ast.get_source_segment(full_source, node)

    return None


def _compile_node_in_module(node):
    return compile(ast.Module([node], []), '<dummy>', 'exec')


def _compile_simple(node):
    return _compile_node_in_module(node).co_consts[-2]  # co_consts = (<code object from node>, None)


_NO_ARGS = ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[])
_OUTER_FUN = partial(ast.FunctionDef, name='@outer_scope@', args=_NO_ARGS, decorator_list=[])


def _compile_with_freevars(freevars, node):
    """Compile `node` in the function scope with `freevars` defined."""

    # When `node` is compiled in module scope, names other than its arguments are loaded from global scope
    # using LOAD_GLOBAL instruction. However, sometimes the predicate has variables captured from outer scope,
    # which will be loaded by LOAD_DEREF. This causes a difference in the bytecode of the recompiled node.

    # If a predicate's code has non-empty `co_freevars` (names of variables captured from outer scope),
    # the node is compiled in the scope of a dummy function which has those freevars defined.
    # The compiler then produces LOAD_DEREF instructions, and the bytecode is equal to original predicate's one.

    return _compile_node_in_module(_OUTER_FUN(**_DUMMY_POSITION, body=[
        ast.Assign(
            [ast.Name(freevar, ctx=ast.Store(), **_DUMMY_POSITION) for freevar in freevars],
            ast.Constant(None, **_DUMMY_POSITION), **_DUMMY_POSITION),
        node,
    ])).co_consts[-2].co_consts[-1]


def islambda(obj):
    # apparently there is no more reliable method than checking __name__
    return isfunction(obj) and obj.__name__ == '<lambda>'


def filter_instance(class_or_tuple, iterable):
    return (obj for obj in iterable if isinstance(obj, class_or_tuple))
