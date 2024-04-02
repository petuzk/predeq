import ast
from functools import cached_property, partial
from inspect import getsource, iscode, isfunction
from itertools import chain


class predeq:
    def __init__(self, predicate) -> None:
        self.pred = predicate

    @cached_property
    def _cached_repr(self):
        predicate = (
            # show source for lambdas, but __name__ for functions (function body might be too long)
            (_get_callable_source(self.pred) if islambda(self.pred) else getattr(self.pred, '__name__', None))
            # if not available, fallback to repr
            or repr(self.pred)
        )
        return f'<predeq to meet {predicate}>'

    def __repr__(self) -> str:
        return self._cached_repr

    def __eq__(self, other):
        return self.pred(other)


_DUMMY_POSITION = {'lineno': 1, 'col_offset': 0}
_ENABLE_ONE_NODE_SHORT_PATH = True  # see _get_pred_body() below


def _get_callable_source(clbl) -> 'str | None':
    if not isfunction(clbl) and hasattr(clbl, '__call__'):
        clbl = clbl.__call__

    try:
        full_source = getsource(clbl).strip()
    except OSError:
        return None

    # Problem: the source code returned by inspect.get_source() often has unwanted additional context, such as:
    #   - the statement where lambda is defined (e.g. "x = lambda: None" or "print(getsource(lambda: None))")
    #   - in pytest environment, because of assertion rewrite, source offsets are not entirely correct,
    #     and might include the whole assert statement or even the whole test function.
    # Solution: parse the AST of whatever `getsource()` returns, and find the function or lambda node
    # which compiles to the same bytecode as original callable.

    looking_for_lambda = islambda(clbl)
    nodes = filter_instance(ast.Lambda if looking_for_lambda else ast.FunctionDef, ast.walk(ast.parse(full_source)))

    # _ENABLE_ONE_NODE_SHORT_PATH enables "short path": if there is only one function node in AST of the source
    # returned by `getsource()`, it is assumed that this is the function we are looking source code for.
    # It is enabled by default, but omitted in tests to verify this assumption and bytecode comparison code.
    if _ENABLE_ONE_NODE_SHORT_PATH:
        if (first := next(nodes, None)) is None:
            # no func/lambda node found in AST, should not happen
            return None

        if (second := next(nodes, None)) is None:
            # there is only `first` node, return its source segment
            return ast.get_source_segment(full_source, first)

        # there is more than one, prepend first and second to the iterator and compare by bytecode
        nodes = chain((first, second), nodes)

    compile_node = _get_node_compiler(clbl.__code__)
    for node in nodes:
        # lambda node has to be wrapped into Expr to be compiled, see `echo lambda:0 | python -m ast`
        code = compile_node(ast.Expr(node, **_DUMMY_POSITION) if looking_for_lambda else node)
        if code.co_code == clbl.__code__.co_code:
            return ast.get_source_segment(full_source, node)

    return None


def _get_node_compiler(code):
    # When `node` is compiled in module scope, names other than its arguments are loaded from global scope
    # using LOAD_GLOBAL instruction. However, sometimes the function has variables captured from outer scope,
    # which should be loaded by LOAD_DEREF. This causes a difference in the bytecode of the recompiled node.

    # If a function's code has non-empty `co_freevars` (names of variables captured from outer scope),
    # the node is compiled in the scope of an artificial function which has those freevars defined.
    # The compiler then produces LOAD_DEREF instructions, and the bytecode is equal to original function's one.
    # Otherwise, module scope compiler is used because it does not do unnecessary work.

    freevars = code.co_freevars
    return _compile_node if not freevars else partial(_compile_node_with_freevars, freevars)


def _find_code(iterable, *default):
    return next(filter(iscode, iterable), *default)


def _compile_node(node):
    # get node's code object from module's co_consts
    return _find_code(compile(ast.Module([node], []), '<dummy>', 'exec').co_consts)


_NO_ARGS = ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[])


def _compile_node_with_freevars(freevars, node):
    """Compile `node` in the function scope with `freevars` defined."""

    # get inner node's code object from outer node's co_consts
    return _find_code(_compile_node(ast.FunctionDef(
        **_DUMMY_POSITION,
        name='@outer_scope@',  # use a syntactically invalid name to avoid any potential name clashes
        args=_NO_ARGS,
        decorator_list=[],
        body=[
            ast.Assign(
                [ast.Name(freevar, ctx=ast.Store(), **_DUMMY_POSITION) for freevar in freevars],
                ast.Constant(None, **_DUMMY_POSITION),
                **_DUMMY_POSITION
            ),
            node,
        ],
    )).co_consts)


def islambda(obj):
    # apparently there is no more reliable method than checking __name__
    return isfunction(obj) and obj.__name__ == '<lambda>'


def filter_instance(class_or_tuple, iterable):
    return (obj for obj in iterable if isinstance(obj, class_or_tuple))
