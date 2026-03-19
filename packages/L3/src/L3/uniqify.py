from collections.abc import Callable, Mapping
from functools import partial

from util.sequential_name_generator import SequentialNameGenerator

from .syntax import (
    Abstract,
    Allocate,
    Apply,
    Begin,
    Branch,
    Immediate,
    Let,
    LetRec,
    Load,
    Primitive,
    Program,
    Reference,
    Store,
    Term,
)

type Context = Mapping[str, str]


def uniqify_term(
    term: Term,
    context: Context,
    fresh: Callable[[str], str],
) -> Term:
    _term = partial(uniqify_term, context=context, fresh=fresh)

    match term:
        case Let(bindings=bindings, body=body):
            pass

        case LetRec(bindings=bindings, body=body):
            pass

        case Reference(name=name):
            pass            

        case Abstract(parameters=parameters, body=body):
            pass

        case Apply(target=target, arguments=arguments):
            pass

        # No bindings, just return as is
        case Immediate(value=value):
            return Immediate(value=value)

        # Recur on the unknown terms as they may have bindings.
        case Primitive(operator=operator, left=left, right=right):
            return Primitive(operator=operator, left=_term(left), right=_term(right))

        # These are all terms that we don't know whether has a binding or not. So just recur on them
        case Branch(operator=operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            return Branch(
                operator=operator,
                left=_term(left),
                right=_term(right),
                consequent=_term(consequent),
                otherwise=_term(otherwise)
            )
        
        # count is a natural number, no bindings
        case Allocate(count=count):
            return Allocate(count=count)

        # index is also just a nat, but base is an unknown term. Just recur on it
        case Load(base=base, index=index):
            return Load(base=_term(base), index=index)
        
        # This does store a value, but doesn't return the binding directly or anything
        case Store(base=base, index=index, value=value):
            return Store(base=_term(base), index=index, value=_term(value))

        case Begin(effects=effects, value=value):  # pragma: no branch
            pass


def uniqify_program(
    program: Program,
) -> tuple[Callable[[str], str], Program]:
    fresh = SequentialNameGenerator()

    _term = partial(uniqify_term, fresh=fresh)

    match program:
        case Program(parameters=parameters, body=body):  # pragma: no branch
            local = {parameter: fresh(parameter) for parameter in parameters}
            return (
                fresh,
                Program(
                    parameters=[local[parameter] for parameter in parameters],
                    body=_term(body, local),
                ),
            )
