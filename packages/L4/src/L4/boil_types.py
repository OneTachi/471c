from collections.abc import Mapping
from functools import partial
from util.sequential_name_generator import SequentialNameGenerator
from L3 import syntax as L3

from . import syntax as L4

type Context = Mapping[L4.Identifier, None]

def boil_types(
    term: L4.Term,
    symbol_table: Mapping[L4.Identifer, int],
    fresh: Callable[[str], str],
) -> L3.Term:
    recur = partial(boil_types, fresh=fresh, symbol_table=symbol_table)
    match term: 
        # Boils down into 1 or 0 for truth
        case Bool(value=value):
            if value == True:
                return L3.Immediate(value=1)
            else:
                return L3.Immediate(value=0)

        # Boils down into basic integer determined by symbol table 
        case Symbol(name=name):
            if name in symbol_table:
                return Immediate(value=symbol_table[name])
            else:
                symbol_table[name] = len(table) + 1
                return Immediate(value=symbol_table[name])

        
        # Store all values in memory and make sure reference to is properly set
        case Tuple(values=values):
            lowered_values = [recur(v) for v in values]

            new_name = fresh("tuple")
            
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
        
        # Similar to Tuple, but sort alphabetically as there is no given order
        case Record(fields=fields):
            identifiers = [item[0] for item in fields]
            identifiers.sort() # alphabetical
            
            lowered_fields = [tuple(item[0], recur(item[1])) for item in fields] 
            
            ptr = fresh("record")
            seq = [
                L3.Store(
                    base=L3.Reference(name=ptr),
                    index=i,
                    value=lowered_fields[identifiers[i]]
                )
                for i in enumerate(identifiers)
            ]
            
            return L3.Let(
                bindings=[(ptr, L3.Allocate(count=len(identifiers)))],
                body=L3.Begin(
                    effects=seq,
                    value=L3.Reference(name=ptr)
                )
            )
        
        case GetRecordValue(record=record, key=key): #TODO
            #get_record_type(record)
            #coerce(record)
            return L3.Load(base=record, index=index)

        ## STANDARD ONES

        case Let(bindings=bindings, body=body):
            return L3.Let(bindings=[(name, recur(val)) for name, val in bindings], body=recur(body))

        case LetRec(bindings=bindings, body=body):
            return L3.LetRec(bindings=[(name, recur(val)) for name, val in bindings], body=recur(body))

        case Reference(name=name):
            return L3.Reference(name=name)

        case Abstract(parameters=parameters, body=body):
            return L3.Abstract(parameters=parameters, body=recur(body))

        case Apply(target=target, arguments=arguments):
            return L3.Apply(target=recur(target), arguments=[recur(arg) for arg in arguments])

        case Immediate(value=value):
            return L3.Immediate(value=value)

        case Primitive(operator=operator, left=left, right=right):
            return L3.Primitive(operator=operator, left=recur(left), right=recur(right))

        case Branch(operator=operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            return L3.Branch(operator=operator, left=recur(left), right=recur(right), consequent=recur(consequent), otherwise=recur(otherwise))
    
        case Allocate(count=count):
            return L3.Allocate(count=count)

        case Load(base=base, index=index):
            return L3.Load(base=recur(base), index=index)

        case Store(base=base, index=index, value=value):
            return L3.Store(base=recur(base), index=index, value=recur(value))

        case Begin(effects=effects, value=value):
            return L3.Begin(value=recur(value), effects=[recur(e) for e in effects])
            
