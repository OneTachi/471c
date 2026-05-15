from collections.abc import Mapping
from functools import partial
from util.sequential_name_generator import SequentialNameGenerator
from L3 import syntax as L3

from . import syntax as L4

type Context = Mapping[L4.Identifier, None]

# Pass that assigns types to everything
def infer_term(
    term: L4.Term,
    context: Mapping[L4.Identifier, L4.Type]
) -> L4.Type:
    match term:
        case Immediate():
            return Int()
        
        case Primitive(left=left, right=right):
            l = infer_term(left, context)
            r = infer_term(right, context)
            if not isinstance(l, Int):
                raise TypeError("Left side of primitive is not Int")
            if not isinstance(r, Int):
                raise TypeError("Right side of primitive is not Int")

            return Int()

        case MakeBool():
            return Boolean()

        case MakeSymbol():
            return Symbol()

        case MakeRecord(fields=fields):
            types = {identifier : infer_term(value, context) for identifier, value in fields}
            return Record(fields=types)

        case MakeTuple(values=values):
            types = [infer_term(value, context) for value in values]
            return Tuple(values=types)

        # Does variable exist in the context or not basically
        case Reference(name=name):
            if name not in context:
                raise TypeError(f"Undefined variable: {name}")
            return context[name]

        case GetTupleValue(term=tm, index=index):
            t = infer_term(tm, context)
            if not isinstance(t, Tuple):
                raise TypeError("Not a tuple or nonexistent.")
            if index >= len(t.values):
                raise TypeError("Index is too large!")
            
            return t.values[index]

        case GetRecordValue(record=rd, key=key):
            r = infer_term(rd, context)

            if not isinstance(r, Record):
                raise TypeError("Not a record or nonexistent.")

            if key not in r.fields:
                raise TypeError("Key doesn't exist in record.")

            return r.fields[key]

        case Let(bindings=bindings, body=body):
            new_context = dict(context)
            
            # Ensure our context has types
            for name, t in bindings:
                new_context[name] = infer_term(t, new_context)

            return infer_term(body, new_context)

        case If(condition=condition, consequent=consequent, otherwise=otherwise):
            condType = infer_term(condition, context)
            if not isinstance(condType, Boolean):
                raise TypeError("Condition for If must be a boolean")

            c1 = infer_type(consequent, context)
            c2 = infer_type(otherwise, context)

            if c1 == c2:
                return c1
            else:
                raise TypeError("Comparisons are uncomparable in if statement")

        case Abstract(parameters=parameters, ret=ret, body=body):
            new_context = dict(context)
            # Get parameters types for Arrow
            params = []
            for name, t in parameters:
                new_context[name] = t
                params.append(t)

            # Check if body matches return type
            inferred_body = infer_term(body, new_context)
            
            # TODO change for subtype
            if inferred_body != ret:
                raise TypeError(f"Return type does not match body. Expected {ret}, got {inferred_body}")

            return Arrow(parameters=params, ret=ret)

        case Apply(target=target, arguments=arguments):
            t = infer_term(t, context)
            if not isinstance(t, Arrow):
                raise TypeError("Target is not a function")

            if len(t.parameters) != len(arguments):
                raise TypeError("Argument length mismatch")

            for i, arg in enumerate(arguments):
                a = infer_type(arg, context)
                
                # TODO SUBTYPING
                if a != t.parameters[i]:
                    raise TypeError(f"Argument {i} is type {a}. Expected {t.parameters[i]}")
                
            return t.ret

        case LetRec(bindings=bindings, body=body):
            new_context = dict(context)

            for name, binding_type, _ in bindings:
                new_context[name] = binding_type

            for name, binding_type, value in bindings:
                inferred = infer_term(value, new_context)
                #TODO Subtyping here
                if inferred != binding_type:
                    raise TypeError(f"Expected type {binding_type}. Got {inferred}")

                return infer_term(body, new_context)
        
        case Begin(effects=effects, value=value):
            # check validity of types
            for effect in effects:
                infer_term(effect)

            return infer_term(value, context)

        case Branch(left=left, right=right, consequent=consequent, otherwise=otherwise):
            if not isinstance(infer_term(left, context), Int):
                raise TypeError("Left side of comparison is not Int")
            if not isinstance(infer_term(right, context), Int):
                raise TypeError("Right side of comparison is not Int")

            c = infer_term(consequent, context)
            o = infer_term(otherwise, context)

            # TODO Subtyping
            if c == o:
                return c

            raise TypeError("Branch consequent and otherwise do not match types")

        case Allocate(count=count):
            return Int()
        
        case Load(base=base, index=index):
            if not isinstance(infer_term(base, context), Int):
                raise TypeError("Base of Load must be an Int (address)")
            
            return Int()

        case Store(base=base, index=index, value=value)
            if not isinstance(infer_term(base, context), Int):
                raise TypeError("Base of Load must be an Int (address)")
            if not isinstance(infer_term(index, context), Int):
                raise TypeError("Index of Load must be an Int (address)")

            v = infer_term(value, context)
            if not isinstance(v, Int):
                raise TypeError("Value of Load must be an Int")

            return Int()


def boil_program(
    program: L4.Program,
    symbol_table: Mapping[L4.Identifer, int],
) -> tuple[Callable[[str], str], L3.Program]:
    fresh = SequentialNameGenerator()
    _term = partial(boil_types, fresh=fresh)

    match program:
        case Program(parameters=parameters, body=body):  # pragma: no branch
            local = {parameter: fresh(parameter) for parameter in parameters}
            return (
                fresh,
                L3.Program(
                    parameters=[local[parameter] for parameter in parameters],
                    body=_term(body, local),
                ),
            )


def boil_types(
    term: L4.Term,
    symbol_table: Mapping[L4.Identifer, int],
    fresh: Callable[[str], str],
) -> L3.Term:
    recur = partial(boil_types, fresh=fresh, symbol_table=symbol_table)
    match term: 
        # Boils down into 1 or 0 for truth
        case MakeBool(value=value):
            if value == True:
                return L3.Immediate(value=1)
            else:
                return L3.Immediate(value=0)
        
        # Boil everything down into left holding all values. Since we can have just a true or false 
        case L4.If(condition=condition, consequent=consequent, otherwise=otherwise):
            return L3.Branch(
                operator="==",
                left=recur(condition),
                right=L3.Immediate(value=1),
                consequent=recur(consequent),
                otherwise=recur(otherwise)
            )

        # Boils down into basic integer determined by symbol table 
        case MakeSymbol(name=name):
            if name not in symbol_table:
                symbol_table[name] = len(table)
            return L3.Immediate(value=symbol_table[name])

        
        # Store all values in memory and make sure reference to is properly set
        case MakeTuple(values=values):
            lowered_values = [recur(v) for v in values]

            new_name = fresh("tuple")
            
            seq = [
                L3.Store(
                    base=L3.Reference(name=new_name),
                    index=i,
                    value=val
                )
                for i, val in enumerate(lowered_values)
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
        case MakeRecord(fields=fields):
            identifiers = [name for name, value in fields]
            identifiers= sorted(identifiers) # alphabetical
            
            lowered_fields = [tuple(name, recur(value)) for name, value in fields] 
            
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
            #get_record_type(record) #what type is this basically... will need for inference!
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
            
