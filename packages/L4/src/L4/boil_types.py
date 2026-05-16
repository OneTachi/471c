from collections.abc import Callable, Mapping
from functools import partial

from L3 import syntax as L3
from util.sequential_name_generator import SequentialNameGenerator

from . import syntax as L4
from .subtype import isSubtype

type Context = Mapping[L4.Identifier, None]


# Pass to verify program's type safety
def infer_program(program: L4.Program) -> L4.Type:
    context = {name: t for name, t in program.parameters}

    body_type = infer_term(program.body, context)

    if body_type != program.ret:
        raise TypeError(f"Program body returns {body_type}. Expected {program.ret}")

    return program.ret


# Pass that assigns types to everything
def infer_term(term: L4.Term, context: Mapping[L4.Identifier, L4.Type]) -> L4.Type:
    match term:
        case L4.Immediate():
            return L4.Int()

        case L4.Primitive(left=left, right=right):
            lef = infer_term(left, context)
            rig = infer_term(right, context)
            if not isinstance(lef, L4.Int):
                raise TypeError("Left side of primitive is not Int")
            if not isinstance(rig, L4.Int):
                raise TypeError("Right side of primitive is not Int")

            return L4.Int()

        case L4.MakeBool():
            return L4.Boolean()

        case L4.MakeSymbol():
            return L4.Symbol()

        case L4.MakeRecord(fields=fields):
            types = {identifier: infer_term(value, context) for identifier, value in fields}
            return L4.Record(fields=types)

        case L4.MakeTuple(values=values):
            types = [infer_term(value, context) for value in values]
            return L4.Tuple(values=types)

        # Does variable exist in the context or not basically
        case L4.Reference(name=name):
            if name not in context:
                raise TypeError(f"Undefined variable: {name}")
            return context[name]

        case L4.GetTupleValue(term=tm, index=index):
            t = infer_term(tm, context)
            if not isinstance(t, L4.Tuple):
                raise TypeError("Not a tuple or nonexistent.")
            if index >= len(t.values):
                raise TypeError("Index is too large!")

            return t.values[index]

        case L4.GetRecordValue(record=rd, key=key):
            rig = infer_term(rd, context)

            if not isinstance(rig, L4.Record):
                raise TypeError("Not a record or nonexistent.")

            if key not in rig.fields:
                raise TypeError("Key doesn't exist in record.")

            return rig.fields[key]

        case L4.Let(bindings=bindings, body=body):
            new_context = dict(context)

            # Ensure our context has types
            for name, t in bindings:
                new_context[name] = infer_term(t, new_context)

            return infer_term(body, new_context)

        case L4.If(condition=condition, consequent=consequent, otherwise=otherwise):
            condType = infer_term(condition, context)
            if not isinstance(condType, L4.Boolean):
                raise TypeError("Condition for If must be a boolean")

            c1 = infer_term(consequent, context)
            c2 = infer_term(otherwise, context)

            if c1 == c2:
                return c1
            else:
                raise TypeError("Comparisons are uncomparable in if statement")

        case L4.Abstract(parameters=parameters, ret=ret, body=body):
            new_context = dict(context)
            # Get parameters types for Arrow
            params = []
            for name, t in parameters:
                new_context[name] = t
                params.append(t)

            # Check if body matches return type
            inferred_body = infer_term(body, new_context)

            isSubtype(inferred_body, ret)

            return L4.Arrow(parameters=params, ret=ret)

        case L4.Apply(target=target, arguments=arguments):
            t = infer_term(target, context)
            if not isinstance(t, L4.Arrow):
                raise TypeError("Target is not a function")

            if len(t.parameters) != len(arguments):
                raise TypeError("Argument length mismatch")

            for i, arg in enumerate(arguments):
                a = infer_term(arg, context)

                isSubtype(a, t.parameters[i])

            return t.ret

        case L4.LetRec(bindings=bindings, body=body):
            new_context = dict(context)

            for name, binding_type, _ in bindings:
                new_context[name] = binding_type

            for name, binding_type, value in bindings:
                inferred = infer_term(value, new_context)

                isSubtype(inferred, binding_type)

                return infer_term(body, new_context)

        case L4.Begin(effects=effects, value=value):
            # check validity of types
            for effect in effects:
                infer_term(effect)

            return infer_term(value, context)

        case L4.Branch(left=left, right=right, consequent=consequent, otherwise=otherwise):
            if not isinstance(infer_term(left, context), L4.Int):
                raise TypeError("Left side of comparison is not Int")
            if not isinstance(infer_term(right, context), L4.Int):
                raise TypeError("Right side of comparison is not Int")

            c = infer_term(consequent, context)
            o = infer_term(otherwise, context)

            if isSubtype(c, o):
                return c

            raise TypeError("Branch consequent and otherwise do not match types")

        case L4.Allocate():
            return L4.Int()

        case L4.Load(base=base, index=index):
            if not isinstance(infer_term(base, context), L4.Int):
                raise TypeError("Base of Load must be an Int (address)")

            return L4.Int()

        case L4.Store(base=base, index=index, value=value):
            if not isinstance(infer_term(base, context), L4.Int):
                raise TypeError("Base of Load must be an Int (address)")
            if not isinstance(infer_term(index, context), L4.Int):
                raise TypeError("Index of Load must be an Int (address)")

            v = infer_term(value, context)
            if not isinstance(v, L4.Int):
                raise TypeError("Value of Load must be an Int")

            return L4.Int()


def boil_program(
    program: L4.Program,
    symbol_table: Mapping[L4.Identifier, int],
) -> tuple[SequentialNameGenerator, L3.Program]:
    fresh = SequentialNameGenerator()
    _term = partial(boil_types, fresh=fresh)
    # Use freshness for lowering
    renamed_params = {name: fresh(name) for name, _ in program.parameters}
    lowered_params = [renamed_params[name] for name, _ in program.parameters]
    lowered_context = {renamed_params[name]: t for name, t in program.parameters}

    lowered_body = boil_types(term=program.body, symbol_table=symbol_table, fresh=fresh, context=lowered_context)

    return (fresh, L3.Program(parameters=lowered_params, body=lowered_body))


def boil_types(
    term: L4.Term,
    symbol_table: Mapping[L4.Identifier, int],
    fresh: Callable[[str], str],
    context: Mapping[L4.Identifier, L4.Type],
) -> L3.Term:
    recur = partial(boil_types, fresh=fresh, symbol_table=symbol_table, context=context)
    match term:
        # Boils down into 1 or 0 for truth
        case L4.MakeBool(value=value):
            if value:
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
                otherwise=recur(otherwise),
            )

        # Boils down into basic integer determined by symbol table
        case L4.MakeSymbol(name=name):
            if name not in symbol_table:
                symbol_table[name] = len(symbol_table)
            return L3.Immediate(value=symbol_table[name])

        # Store all values in memory and make sure reference to is properly set
        case L4.MakeTuple(values=values):
            lowered_values = [recur(v) for v in values]

            new_name = fresh("tuple")

            seq = [
                L3.Store(base=L3.Reference(name=new_name), index=i, value=val) for i, val in enumerate(lowered_values)
            ]

            return L3.Let(
                bindings=[(new_name, L3.Allocate(count=len(values)))],
                body=L3.Begin(effects=seq, value=L3.Reference(name=new_name)),
            )

        # Grab the reference and specific term
        case L4.GetTupleValue(index=index, term=term):
            return L3.Load(recur(term), index=index)

        # Similar to Tuple, but sort alphabetically as there is no given order
        case L4.MakeRecord(fields=fields):
            identifiers = [name for name, value in fields]
            identifiers = sorted(identifiers)  # alphabetical

            lowered_fields = [tuple(name, recur(value)) for name, value in fields]

            ptr = fresh("record")
            seq = [
                L3.Store(base=L3.Reference(name=ptr), index=i, value=lowered_fields[identifiers[i]])
                for i in enumerate(identifiers)
            ]

            return L3.Let(
                bindings=[(ptr, L3.Allocate(count=len(identifiers)))],
                body=L3.Begin(effects=seq, value=L3.Reference(name=ptr)),
            )

        case L4.GetRecordValue(record=record, key=key):
            record_type = infer_term(record, context)
            if not isinstance(record_type, L4.Record):
                raise TypeError("Term is not type Record")

            sorted_keys = sorted(record_type.fields.keys())
            try:
                index = sorted_keys.index(key)
            except ValueError:
                raise TypeError(f"{key} not found in record {record}")

            return L3.Load(base=recur(record), index=index)

        case L4.Let(bindings=bindings, body=body):
            ctx = dict(context)
            lowered_bindings = []
            for name, value in bindings:
                # Pass type checker
                ctx[name] = infer_term(value, ctx)
                lowered_bindings.append((name, recur(value, ctx)))
            return L3.Let(bindings=lowered_bindings, body=recur(body, ctx))

        case L4.LetRec(bindings=bindings, body=body):
            ctx = dict(context)
            for name, t, _ in bindings:
                ctx[name] = t

            lowered_bindings = [(name, recur(value, ctx)) for name, _, value in bindings]
            return L3.LetRec(bindings=lowered_bindings, body=recur(body, ctx))

        case L4.Abstract(parameters=parameters, body=body):
            ctx = dict(context)
            lowered_params = []
            for name, t in parameters:
                ctx[name] = t
                lowered_params.append(name)

            return L3.Abstract(parameters=lowered_params, body=recur(body, ctx))

        ## STANDARD ONES
        case L4.Reference(name=name):
            return L3.Reference(name=name)

        case L4.Apply(target=target, arguments=arguments):
            return L3.Apply(target=recur(target), arguments=[recur(arg) for arg in arguments])

        case L4.Immediate(value=value):
            return L3.Immediate(value=value)

        case L4.Primitive(operator=operator, left=left, right=right):
            return L3.Primitive(operator=operator, left=recur(left), right=recur(right))

        case L4.Branch(operator=operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            return L3.Branch(
                operator=operator,
                left=recur(left),
                right=recur(right),
                consequent=recur(consequent),
                otherwise=recur(otherwise),
            )

        case L4.Allocate(count=count):
            return L3.Allocate(count=count)

        case L4.Load(base=base, index=index):
            return L3.Load(base=recur(base), index=index)

        case L4.Store(base=base, index=index, value=value):
            return L3.Store(base=recur(base), index=index, value=recur(value))

        case L4.Begin(effects=effects, value=value):
            return L3.Begin(value=recur(value), effects=[recur(e) for e in effects])
