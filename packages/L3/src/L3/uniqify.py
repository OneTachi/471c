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
        # Creates bindings that must be uniquified, and represented in a new context!
        case Let(bindings=bindings, body=body):
            unique_bindings = []
            for name, value in bindings:
                # Get unique name and iterator on term!
                unique_name = fresh(name)
                unique_value = _term(value)
                unique_bindings.append((unique_name, unique_value))
            
            updated_context = dict(context)
            for (orig_name, _), (new_name, _) in zip(bindings, unique_bindings):
                # Just like in the tests.
                # Grab from context to __get the binding name__ in which we retrieve the value
                updated_context[orig_name] = new_name
            
            new_body = uniqify_term(body, updated_context, fresh) 

            return Let(bindings=unique_bindings, body=new_body)

        # LetRec is similar to Let, but each binding should have the new context + prev binding        
        case LetRec(bindings=bindings, body=body):
            unique_bindings = []
            updated_context = dict(context)
            tmp_names = []
            
            # Establish new bindings through the context!
            for name, _ in bindings:
                new_name = fresh(name)
                tmp_names.append(new_name)
                updated_context[name] = new_name

            # Let new context pass through the bindings
            for unique_name, (_, binding) in zip(tmp_names, bindings):
                unique_value = uniqify_term(binding, updated_context, fresh)
                unique_bindings.append((unique_name, unique_value))

            new_body = uniqify_term(body, updated_context, fresh)
            return LetRec(bindings=unique_bindings, body=new_body)

        
        # If a name exists in the context, bind it to that unique variable
        case Reference(name=name):
            real_name = context[name]
            return Reference(name=real_name)
        
        # Basically Let/LetRec
        case Abstract(parameters=parameters, body=body):
            unique_parameters = []
            updated_context = dict(context)
            
            # No bindings! So no updating a corresponding binding.
            for parameter in parameters:
                unique_parameter = fresh(parameter)
                unique_parameters.append(unique_parameter)
                updated_context[parameter] = updated_parameter

            new_body = uniqify_term(body, updated_context, fresh)
            return Abstract(parameters=unique_parameters, body=new_body)

        
        # Same case as Begin
        case Apply(target=target, arguments=arguments):
            unique_arguments = []
            for argument in arguments:
                unique_arguments.append(_term(argument))
            return Apply(target=_term(target), arguments=unique_arguments)

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

        # Go over each effect and value to find bindings
        case Begin(effects=effects, value=value):  # pragma: no branch
            unique_effects = []
            for effect in effects:
                unique_effects.append(_term(effect))
            return Begin(effects=unique_effects, value=_term(value))


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
