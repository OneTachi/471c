from collections.abc import Mapping
from functools import partial
from .syntax import (
    Abstract,
    Allocate,
    Apply,
    Begin,
    Branch,
    Identifier,
    Immediate,
    Let,
    Load,
    Primitive,
    Reference,
    Store,
    Term,
    Program,
)

type Context = Mapping[Identifier, Term]


def constant_folding_program(program: Program) -> Program:
    return Program(parameters=program.parameters, body=constant_folding_term(program.body, {}))


# As of right now, only needs to do branch and primitive folding!
def constant_folding_term(term: Term, context: Context) -> Term:
    recur = partial(constant_folding_term, context=context)
    match term:
        case Branch(operator=operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            lf = recur(left)
            rt = recur(right)

            if isinstance(lf, Immediate) and isinstance(rt, Immediate):
                res = (lf.value < rt.value) if operator == "<" else (lf.value == rt.value)
                return recur(consequent if res else otherwise)

            return Branch(
                operator=operator, left=lf, right=rt, consequent=recur(consequent), otherwise=recur(otherwise)
            )

        case Primitive(operator=operator, left=left, right=right):
            lf = recur(left)
            rt = recur(right)
            match operator:
                case "+":
                    match lf, rt:
                        case Immediate(value=i1), Immediate(value=i2):
                            return Immediate(value=i1 + i2)

                        case Immediate(value=0), right:
                            return right

                        case left, Immediate(value=0):
                            return left

                        case Immediate(value=v1), Primitive(operator="+", left=Immediate(value=v2), right=rest):
                            return Primitive(operator="+", left=Immediate(value=v1 + v2), right=rest)

                        case _, Immediate():
                            return Primitive(operator="+", left=rt, right=lf)

                case "-":
                    # Note that - operations shouldn't change their order
                    match lf, rt:
                        case Immediate(value=i1), Immediate(value=i2):
                            return Immediate(value=i1 - i2)

                        # skip '0, right' case as above handles calculation
                        case left, Immediate(value=0):
                            return left

                        case _:
                            return term
                case "*":  # pragma: no branch
                    # All cases tested, but last prim is never jumped to because it shouldn't.
                    match lf, rt:
                        case Immediate(value=i1), Immediate(value=i2):
                            return Immediate(value=i1 * i2)

                        # Multiply by 0 case
                        case left, Immediate(value=0):
                            return Immediate(value=0)

                        case Immediate(value=1), right:
                            return right

                        case _, Immediate():  # pragma: no branch
                            # This in fact is branching here, but for some reason doesn't show up as tested?
                            return Primitive(operator="*", left=rt, right=lf)
            return Primitive(operator=operator, left=lf, right=rt)

        case Let(bindings=bindings, body=body):
            new_bindings = [(name, recur(val)) for name, val in bindings]
            return Let(bindings=new_bindings, body=recur(body))

        case Abstract(parameters=parameters, body=body):
            return Abstract(parameters=parameters, body=recur(body))

        case Apply(target=target, arguments=arguments):
            return Apply(target=recur(target), arguments=[recur(a) for a in arguments])

        case Begin(effects=effects, value=value):
            return Begin(effects=[recur(effect) for effect in effects], value=recur(value))

        case Store(base=base, index=index, value=value):
            return Store(base=recur(base), index=index, value=recur(value))

        case Load(base=base, index=index):
            return Load(base=recur(base), index=index)

        # Cases are handled and tested...
        case Immediate() | Reference() | Allocate():  # pragma: no branch
            return term
