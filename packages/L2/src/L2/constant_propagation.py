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

type Context = Mapping[Identifier, Immediate]

def constant_propagation_program(program: Program) -> Program:
    return Program(
        parameters=program.parameters,
        body=constant_propagation_term(program.body, {})
    )

# Basically, see if you can propogate anything by constantly looking at each term like in previous assignments
def constant_propagation_term(term: Term, context: Context) -> Term:
    recur = partial(constant_propagation_term, context=context)
    match term:
        case Reference(name=name):
            return context.get(name, term)
        
        case Let(bindings=bindings, body=body):
            inner_context = dict(context)
            new_bindings = []
            for name, value in bindings:
                propagated_val = constant_propagation_term(value, inner_context)
                new_bindings.append((name, propagated_val))

                if isinstance(propagated_val, Immediate):
                    inner_context[name] = propagated_val
                elif name in inner_context:
                    del inner_context[name]

            return Let(
                bindings=new_bindings,
                body=constant_propagation_term(body, inner_context)
            )

        case Abstract(parameters=parameters, body=body):
            inner_context = {k: v for k, v in context.items() if k not in parameters}
            return Abstract(
                parameters=parameters,
                body=constant_propagation_term(body, inner_context)
            )

        case Apply(target=target, arguments=arguments):
            new_args = []
            for argument in arguments:
                new_args.append(recur(argument))

            return Apply(
                target=recur(target),
                arguments=new_args
            )

        case Immediate(value=value):
            return Immediate(value=value)

        case Primitive(operator=operator, left=left, right=right):
            return Primitive(
                operator=operator, 
                left=recur(left), 
                right=recur(right)
            )

        case Branch(operator=operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            return Branch(
                operator=operator, 
                left=recur(left), 
                right=recur(right),
                consequent=recur(consequent),
                otherwise=recur(otherwise)
            )

        case Allocate(count=count):
            return Allocate(
                count=count
            )

        case Load(base=base, index=index):
            return Load(
                base=recur(base),
                index=index
            )

        case Store(base=base, index=index, value=value):
            return Store(
                base=recur(base),
                index=index,
                value=recur(value)
            )

        case Begin(effects=effects, value=value): 
            new_effects = []
            for effect in effects:
                new_effects.append(recur(effect))

            return Begin(
                effects=new_effects,
                value=recur(value)
            )
