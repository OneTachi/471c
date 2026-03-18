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
        case L2.Let(bindings=bindings, body=body):
            pass
        
        # Name has been given a value so give k the name so we can return the next steps
        case L2.Reference(name=name):
            return k(name)

        case L2.Abstract(parameters=parameters, body=body):
            pass

        case L2.Apply(target=target, arguments=arguments):
            pass

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
                        destination=tmp # necc for then
                        operator=operator,
                        left=left,
                        right=right,
                        then=k(tmp) # Remember that our tmp name was established above, we simply ask for what happens next
                        # k is our black box (for now) that just tells us what happens next with a variable as input
                    )
                )
            )

        case L2.Branch(operator=operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            pass
        
        # Similar to Reference
        case L2.Allocate(count=count):
            pass

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

        case L2.Store(base=base, index=index, value=value):
            pass

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
