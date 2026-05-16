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


def get_free_variables(term: Term) -> set[Identifier]:
    match term:
        case Reference(name=name):
            return {name}

        case Let(bindings=bindings, body=body):
            variables = get_free_variables(body)
            for name, value in bindings:
                variables.discard(name)
                variables |= get_free_variables(value)
            return variables

        case Abstract(parameters=parameters, body=body):
            return get_free_variables(body) - set(parameters)

        case Apply(target=target, arguments=arguments):
            variables = get_free_variables(target)
            for arg in arguments:
                variables |= get_free_variables(arg)
            return variables

        case Primitive(operator=_operator, left=left, right=right):
            variables = get_free_variables(left)
            variables |= get_free_variables(right)
            return variables

        case Branch(operator=_operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            return (
                get_free_variables(left)
                | get_free_variables(right)
                | get_free_variables(consequent)
                | get_free_variables(otherwise)
            )

        case Begin(effects=effects, value=value):
            variables = get_free_variables(value)
            for effect in effects:
                variables |= get_free_variables(effect)
            return variables

        case Load(base=base, index=_index):
            return get_free_variables(base)

        case Store(base=base, index=_index, value=value):
            return get_free_variables(base) | get_free_variables(value)

        case Allocate(count=_count):
            return set()

        case Immediate(value=_value):  # pragma: no branch
            # Case is expliticly written
            return set()


def is_pure(term: Term) -> bool:
    match term:
        case Immediate() | Reference() | Abstract():
            return True
        case Primitive(left=left, right=right):
            return is_pure(left) and is_pure(right)
        case Begin(effects=effects, value=value):
            return all(is_pure(effect) for effect in effects) and is_pure(value)
        case _:
            return False


def dead_code_elimination(term: Term) -> Term:
    recur = partial(dead_code_elimination)
    match term:
        case Branch(
            operator=operator,
            left=Immediate(value=i1),
            right=Immediate(value=i2),
            consequent=consequent,
            otherwise=otherwise,
        ):
            res = (i1 < i2) if operator == "<" else (i1 == i2)
            return recur(consequent if res else otherwise)

        case Let(bindings=bindings, body=body):
            new_body = recur(body)
            free_vars = get_free_variables(new_body)

            new_bindings = []
            for name, value in reversed(bindings):
                folded = recur(value)
                if name not in free_vars and is_pure(folded):
                    continue
                new_bindings.append((name, folded))
                free_vars.discard(name)
                free_vars |= get_free_variables(folded)

            if not new_bindings:
                return new_body
            return Let(bindings=list(reversed(new_bindings)), body=new_body)

        case Abstract(parameters=parameters, body=body):
            return Abstract(parameters=parameters, body=recur(body))

        case Apply(target=target, arguments=arguments):
            return Apply(target=recur(target), arguments=[recur(argument) for argument in arguments])

        case Primitive(operator=operator, left=left, right=right):
            return Primitive(operator=operator, left=recur(left), right=recur(right))

        case Branch(operator=operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            return Branch(
                operator=operator,
                left=recur(left),
                right=recur(right),
                consequent=recur(consequent),
                otherwise=recur(otherwise),
            )

        case Begin(effects=effects, value=value):
            new_effects = [recur(effect) for effect in effects]
            new_value = recur(value)

            optimized_effects = [effect for effect in new_effects if not is_pure(effect)]

            if not optimized_effects:
                return new_value
            return Begin(effects=optimized_effects, value=new_value)

        case Store(base=base, index=index, value=value):
            return Store(base=recur(base), index=index, value=recur(value))

        case Load(base=base, index=index):
            return Load(base=recur(base), index=index)

        case _:
            return term


def dead_code_elimination_program(
    program: Program,
) -> Program:
    return Program(parameters=program.parameters, body=dead_code_elimination(program.body))
