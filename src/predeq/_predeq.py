import ast
import dis
import re
import sys
from collections import deque
from functools import cached_property, partial
from inspect import getsourcelines, iscode, isfunction
from itertools import accumulate, chain


class predeq:
    """predeq(predicate) -> predeq object

    Return an object which compares equal to any object X for which predicate(X) returns True.

        >>> even = predeq(lambda x: x % 2 == 0)
        >>> 2 == even
        True
        >>> 5 == even
        False

    No exceptions are handled by predeq.
    It is the user's choice whether the comparison might raise.

        >>> None == even
        Traceback (most recent call last):
            ...
        TypeError: unsupported operand type(s) for %: 'NoneType' and 'int'

    """

    def __init__(self, predicate, repr: 'str | None' = None) -> None:
        self.pred = predicate
        self.repr = repr

    @cached_property
    def _default_repr(self):
        predicate = (
            # show source for lambdas, but __name__ for functions (function body might be too long)
            (_get_lambda_repr(self.pred) if islambda(self.pred) else getattr(self.pred, '__name__', None))
            # if not available, fallback to repr
            or repr(self.pred)
        )
        return f'<predeq to meet {predicate}>'

    def __repr__(self) -> str:
        if self.repr is not None:
            return self.repr
        return self._default_repr

    def __eq__(self, other):
        return self.pred(other)


def _get_lambda_repr(lambda_func) -> 'str | None':
    try:
        lines, lnum = getsourcelines(lambda_func)
    except OSError:
        return None

    # Problem: the source code returned by inspect.getsourcelines() has unwanted additional context, such as:
    #   1. The statement where lambda is defined (e.g. "x = lambda: None" or "print(getsource(lambda: None))")
    #   2. Lambdas that are defined in assertions rewritten by pytest have source offsets
    #      cover the whole assert statement (which could also contain other lambda definitions)
    #
    # There are two solutions for this problem, each adressing it only partially:
    #   1. Use __code__.co_positions
    #      Pros: solves problem #1
    #      Cons: available in Python 3.11+ only, does not work with rewritten assertions where offsets are incorrect
    #   2. Parse the found source into AST, and find the lambda node corresponding to the searched lambda
    #      by compiling the node and comparing bytecode
    #      Pros: solves problem #2, and #1 given that the source is a valid Python code
    #      Cons: the source might not be a valid code if lambda is a part of multiline expression
    #
    # In case no solution is able to precisely locate the lambda definition, return None.

    source = (
        (_get_lambda_source_co_positions(lines, lnum, lambda_func) if sys.version_info >= (3, 11) else None)
        or _get_lambda_source_ast(''.join(lines), lambda_func)
    )
    if not source:
        return None
    if (newline_pos := source.find('\n')) >= 0:
        # multiline lambda is rather rarely used, but the \n in the middle makes repr ugly
        source = source[:newline_pos] + '...'
    return source


_LAMBDA_PATTERN = re.compile(br'(?<!\w)(lambda)\W', re.ASCII)


def _get_lambda_source_co_positions(lines, lnum, lambda_func) -> 'str | None':
    # according to python data model, "column information is 0-indexed utf-8 byte offsets", so work on encoded source
    lines = list(map(str.encode, lines))

    # prepare the `source` and `offsets` of line starts in it
    source = b''.join(lines)
    offsets = dict(enumerate(accumulate(map(len, lines[:-1]), initial=0), start=lnum))

    # find lambda body span (code after a colon) from instructions' positions
    body_start_offsets, body_end_offsets = zip(*(
        (offsets[pos.lineno] + pos.col_offset, offsets[pos.end_lineno] + pos.end_col_offset)
        for instr in dis.get_instructions(lambda_func)
        # some instructions have zeroed both col_offset and end_col_offset, those are filtered out
        if (pos := instr.positions).col_offset or pos.end_col_offset
    ))

    # now find the lambda keyword closest to the body
    matches = deque(_LAMBDA_PATTERN.finditer(source[:min(body_start_offsets)]), maxlen=1)
    try:
        lambda_match = matches[-1]
    except IndexError:
        # deque is empty because no matches was found
        return None

    return source[lambda_match.start():max(body_end_offsets)].decode()


_DUMMY_POSITION = {'lineno': 1, 'col_offset': 0}
_ENABLE_ONE_NODE_SHORT_PATH = True  # see _get_lambda_source_ast() below


def _get_lambda_source_ast(source, lambda_func) -> 'str | None':
    source = source.lstrip()  # remove leading whitespace so that it's not interpreted as indent

    try:
        tree = ast.parse(source)
    except SyntaxError:
        # the context available in `source` is not a valid code on its own
        return None

    nodes = filter_instance(ast.Lambda, ast.walk(tree))

    # _ENABLE_ONE_NODE_SHORT_PATH enables "short path": if there is only one function node in AST of the source
    # returned by `getsource()`, it is assumed that this is the function we are looking source code for.
    # It is enabled by default, but omitted in tests to verify this assumption and bytecode comparison code.
    if _ENABLE_ONE_NODE_SHORT_PATH:
        if (first := next(nodes, None)) is None:
            # no func/lambda node found in AST, should not happen
            return None

        if (second := next(nodes, None)) is None:
            # there is only `first` node, return its source segment
            return ast.get_source_segment(source, first)

        # there is more than one, restore the iterator and compare by bytecode
        nodes = chain((first, second), nodes)

    compile_node = _get_node_compiler(lambda_func.__code__)
    for node in nodes:
        # lambda node has to be wrapped into Expr to be compiled, see `echo lambda:0 | python -m ast`
        code = compile_node(ast.Expr(node, **_DUMMY_POSITION))
        if code.co_code == lambda_func.__code__.co_code:
            return ast.get_source_segment(source, node)

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
