from collections.abc import Mapping
from functools import partial

from L3 import syntax as L3

from . import syntax as L4

type Context = Mapping[L4.Identifier, None]

def get_symbol_table(term: L4.Term) -> Mapping[L4.Identifer, int]:
    # TODO
    pass

def boil_types(
    term: L4.Term,
    context: Context,
    symbol_table: Mapping[L4.Identifer, int], # TODO must write this out in another function somewhere...
    naming: blah,
) -> L3.Term:
    recur = partial(eliminate_letrec_term, context=context)
    match term: 
        # Boils down into 1 or 0 for truth
        case Bool(value=value):
            if value == True:
                return L3.Immediate(value=1)
            else:
                return L3.Immediate(value=0)

        # Boils down into basic integer determined by symbol table 
        case Symbol(name=name):
            symbol_value = symbol_table[name] 
            return Immediate(value=symbol_value)
        
        # Store all values in memory and make sure reference to is properly set
        case Tuple(values=values):
            lowered_values = [recur(v) for v in values]

            new_name = #BLAH
            
            seq = [
                L3.Store(
                    base=L3.Reference(name=new_name),
                    index=0,
                    value=lowered_values[0]
                ),
                L3.Store(
                    base=L3.Reference(name=new_name),
                    index=1,
                    value=lowered_values[1]
                )
            ]

            return L3.Let(
                bindings=[(ptr_name, L3.Allocate(count=len(elements)))],
                body=L3.Begin(
                    effects=seq,
                    value=L3.Reference(name=new_name)
                )
            )
        
        # Grab the reference and specific term
        case GetTupleValue(index=index, term=term):
            return L3.Load(recur(term), index=index)
            
        case Record(fields=fields):
            pass
