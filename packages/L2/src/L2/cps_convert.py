from collections.abc import Callable, Sequence
from functools import partial

from L1 import syntax as L1

from L2 import syntax as L2

# Need to name all intermediate results and make control flow explicit
def cps_convert_term(
    term: L2.Term,
    k: Callable[[L1.Identifier], L1.Statement], # A function(name of L1 computation so far) => give us rest of computation
    fresh: Callable[[str], str],
) -> L1.Statement:
    _term = partial(cps_convert_term, fresh=fresh)
    _terms = partial(cps_convert_terms, fresh=fresh)

    match term:
        # Involves copy
        case L2.Let(bindings=_bindings, body=_body):
            result = _term(body, k)

            for name, value in reversed(bindings):
                 result = _term(value, lambda value: L1.Copy(destination=name, source=value, then=result))

            return result
        
        # Name has been given a value so give k the name so we can return the next steps
        case L2.Reference(name=name):
            return k(name)

        case L2.Abstract(parameters=_parameters, body=_body):
            tmp = fresh("t")
            c = fresh("c")
            return L1.Abstract(
                destination=tmp,
                parameters=[*parameters, c],
                body=_term(body, lambda body: L1.Apply(target=c, arguments=[body])),
                then=k(tmp)
            )
        
        # This doesn't have a then. So we need to support it in another way, we need to make an abstraction since we need an identifier
        case L2.Apply(target=_target, arguments=_arguments):
            c = fresh("t")
            tmp = fresh("t")
            return L1.Abstract(
                destination=k,
                parameters=[tmp],
                body=k(tmp), 
                then= _term(
                    target=target,
                    lambda target: _terms(
                        target=target,
                        arguments=[*arguments, c],
                    ),
                )
            )

        case L2.Immediate(value=value):
            # Temporary name (not given like in reference!)
            tmp = fresh("t")
            return L1.Immediate(
                destination=tmp, # Our new temp destination
                value=value,
                then=k(tmp) # Rest of computation
            )
        
        # Control flow for primitive is to execute the left first and then the right
        case L2.Primitive(operator=operator, left=left, right=right): # Note we have terms now. So recur them!
            tmp = fresh("t")
            # We nest left and right (called left and right for the lambda funcs) because we don't have the final result yet
            return _term(
                left,
                k=lambda left: _term(
                    right,
                    k=lambda right: L1.Primitive(
                        destination=tmp, # necc for then
                        operator=operator,
                        left=left,
                        right=right,
                        then=k(tmp) # Remember that our tmp name was established above, we simply ask for what happens next
                        # k is our black box (for now) that just tells us what happens next with a variable as input
                    )
                )
            )

        case L2.Branch(operator=_operator, left=_left, right=_right, consequent=_consequent, otherwise=_otherwise):
            t = fresh("t")
            j = fresh("j")

            return L1.Abstract(
                destination=j,
                parameters=[t],
                body=k(t),
                then=_term(
                    left,
                    lambda left: _term(
                        right,
                        lambda right: L1.Branch(
                            operator=operator,
                            left=left,
                            right=right,
                            then=_term(consequent, lambda consequent: L1.Apply(
                                target=j,
                                arguments=[consequent]
                            )),
                            otherwise=_term(otherwise, lambda otherwise: L1.Apply(
                                target=j,
                                arguments=[otherwise]
                            )
                        )
                    )
                )
            )
        
        # Similar to Reference
        case L2.Allocate(count=_count):
            tmp = fresh("t")
            return L1.Allocate(
                destination=tmp,
                count=count,
                then=k(tmp)
            )

        # Similar to Primitive
        case L2.Load(base=base, index=index):
            tmp = fresh("t")
            return _term(
                base, 
                k=lambda base: L1.Load( 
                    # base turns into whatever value the stuff below evaluates to
                    destination=tmp,
                    base=base,
                    index=index,
                    then=k(tmp)
                ),
            )
        
        # Evaluates to a constant value=0, but we could have code that relies on this evaluation.  
        case L2.Store(base=base, index=index, value=value):
            tmp = fresh("t")
            # Store is really two operations where is stores and gives you a pointer to the 0
            # But it doesn't actually give you the 0 yet so that's why we have an immediate
            return _term(
                base,
                k=lambda base: _term(
                    value,
                    k=lambda value: L1.Store(
                        base=base,
                        index=index,
                        value=value,
                        then=L1.Immediate(
                            destination=tmp,
                            value=0,
                            then=k(tmp)
                        ),
                    )
                )
            )

        case L2.Begin(effects=effects, value=value):  # pragma: no branch
            # Make sure that effects stay in order.
            # L1 Begin doesn't exist. Since our control flow has now been accomplished as value is determined!
            return _terms(effects, k=lambda effects: _term(value, lambda value: k(value))) # just return our explicit name


def cps_convert_terms(
    terms: Sequence[L2.Term],
    k: Callable[[Sequence[L1.Identifier]], L1.Statement],
    fresh: Callable[[str], str],
) -> L1.Statement:
    _term = partial(cps_convert_term, fresh=fresh)
    _terms = partial(cps_convert_terms, fresh=fresh)

    match terms:
        case []:
            return k([])

        case [first, *rest]:
            return _term(first, lambda first: _terms(rest, lambda rest: k([first, *rest])))

        case _:  # pragma: no cover
            raise ValueError(terms)


def cps_convert_program(
    program: L2.Program,
    fresh: Callable[[str], str],
) -> L1.Program:
    _term = partial(cps_convert_term, fresh=fresh)

    match program:
        case L2.Program(parameters=parameters, body=body):  # pragma: no branch
            return L1.Program(
                parameters=parameters,
                body=_term(body, lambda value: L1.Halt(value=value)), # get name of the answer and do rest of computation
            )
