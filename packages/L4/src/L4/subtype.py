from collections.abc import Mapping
from functools import partial

from .syntax import (
    Abstract,
    Allocate,
    Apply,
    Begin,
    Branch,
    GetRecordValue,
    GetTupleValue,
    Identifier,
    Immediate,
    Let,
    Load,
    MakeBool,
    MakeRecord,
    MakeSymbol,
    MakeTuple,
    Primitive,
    Record,
    Reference,
    Store,
    Term,
    Tuple,
    Type,
)


def isSubtype(
    actual: Type,
    expected: Type,
) -> bool:
    try:
        sub_check(actual, expected)
        return True
    except ValueError:
        return False


def sub_check(
    actual: Type,
    expected: Type,
) -> Type:
    _check = partial(sub_check)

    # if equivalent(actual, expected):
    #    return actual

    match actual, expected:
        case Record(fields=fs1), Record(fields=fs2):
            # sorted_expected = sorted(fs2)

            components: Mapping[Identifier, Type] = {}

            for key, expected_ty in fs2.items():
                key_present = [item for item in fs1 if item[0] == key]
                if not key_present:
                    raise ValueError(f"missing field {key} in {actual}")

                components[key] = expected_ty

            return Record(fields=components)

        case Tuple(values=v1), Tuple(values=v2):
            if len(v2) > len(v1):
                raise ValueError(f"expected tuple of length {len(v2)}, but got tuple of length {len(v1)}")

            new_vals: list[Type] = []

            for i in range(len(v2)):
                new_vals.append(_check(v1[i], v2[i]))

            return Tuple(values=new_vals)

        case _:
            raise ValueError(f"can not convert from {actual} to {expected}")


# See Turbak. 12.1.2 Dimensions of Subtyping: Subset Semantics versus Coercion Semantics of Subtyping
def coerce(
    actual: Term,
    expected: Term,
) -> Term:
    _coerce = partial(coerce)

    if equivalent(actual, expected):
        return actual

    match actual, expected:
        case MakeRecord(fields=fs1), MakeRecord(fields=fs2):
            sorted_expected = sorted(fs2)

            components: list[tuple[Identifier, Term]] = []

            for key, expected_ty in sorted_expected:
                key_present = [item for item in fs1 if item[0] == key]
                if not key_present:
                    raise ValueError(f"missing field {key} in {actual}")

                components.append((key, expected_ty))

            return MakeRecord(fields=components)

        case MakeTuple(values=v1), MakeTuple(values=v2):
            if len(v2) > len(v1):
                raise ValueError(f"expected tuple of length {len(v2)}, but got tuple of length {len(v1)}")

            new_vals: list[Term] = []

            for i in range(len(v2)):
                new_vals.append(_coerce(v1[i], v2[i]))

            return MakeTuple(values=new_vals)

        case _:
            raise ValueError(f"can not convert from {actual} to {expected}")


def equivalent(
    t1: Term,
    t2: Term,
) -> bool:
    match t1, t2:
        case MakeRecord(fields=fs1), MakeRecord(fields=fs2):
            if len(fs1) != len(fs2):
                return False

            return all(k1 == k2 and equivalent(v1, v2) for (k1, v1), (k2, v2) in zip(fs1, fs2))

        case MakeTuple(values=v1), MakeTuple(values=v2):
            if len(v1) != len(v2):
                return False
            return all(equivalent(item1, item2) for item1, item2 in zip(v1, v2))

        case GetTupleValue(term=term1, index=i1), GetTupleValue(term=term2, index=i2):
            return i1 == i2 and equivalent(term1, term2)

        case GetRecordValue(record=r1, key=k1), GetRecordValue(record=r2, key=k2):
            return k1 == k2 and equivalent(r1, r2)

        case Reference(name=n1), Reference(name=n2):
            return n1 == n2

        case Abstract(parameters=p1, body=b1), Abstract(parameters=p2, body=b2):
            if len(p1) != len(p2):
                return False
            if any(name1 != name2 for name1, name2 in zip(p1, p2)):
                return False
            return equivalent(b1, b2)

        case Apply(target=target1, arguments=a1), Apply(target=target2, arguments=a2):
            if len(a1) != len(a2):
                return False
            return equivalent(target1, target2) and all(equivalent(arg1, arg2) for arg1, arg2 in zip(a1, a2))

        case Immediate(value=v1), Immediate(value=v2):
            return v1 == v2

        case Primitive(operator=o1, left=l1, right=r1), Primitive(operator=o2, left=l2, right=r2):
            return o1 == o2 and equivalent(l1, l2) and equivalent(r1, r2)

        case Branch(operator=o1, left=l1, right=r1, consequent=c1, otherwise=t1), Branch(
            operator=o2,
            left=l2,
            right=r2,
            consequent=c2,
            otherwise=t2,
        ):
            return o1 == o2 and equivalent(l1, l2) and equivalent(r1, r2) and equivalent(c1, c2) and equivalent(t1, t2)

        case Allocate(count=c1), Allocate(count=c2):
            return c1 == c2

        case Load(base=b1, index=i1), Load(base=b2, index=i2):
            return i1 == i2 and equivalent(b1, b2)

        case Store(base=b1, index=i1, value=v1), Store(base=b2, index=i2, value=v2):
            return i1 == i2 and equivalent(b1, b2) and equivalent(v1, v2)

        case Begin(effects=e1, value=v1), Begin(effects=e2, value=v2):
            if len(e1) != len(e2):
                return False
            return all(equivalent(effect1, effect2) for effect1, effect2 in zip(e1, e2)) and equivalent(v1, v2)

        case Let(bindings=b1, body=body1), Let(bindings=b2, body=body2):
            if len(b1) != len(b2):
                return False
            for (k1, v1), (k2, v2) in zip(b1, b2):
                if k1 != k2 or not equivalent(v1, v2):
                    return False
            return equivalent(body1, body2)

        case MakeBool(value=v1), MakeBool(value=v2):
            return v1 == v2

        case MakeSymbol(name=n1), MakeSymbol(name=n2):
            return n1 == n2

        case _:
            return False
