from collections.abc import Mapping
from functools import partial

from .syntax import (
    Arrow,
    Boolean,
    Identifier,
    Int,
    Overload,
    Record,
    Symbol,
    Tuple,
    Type,
)


def isSubtype(
    actual: Type,
    expected: Type,
) -> bool:
    try:
        coerce(actual, expected)
        return True
    except ValueError:
        return False


# See Turbak. 12.1.2 Dimensions of Subtyping: Subset Semantics versus Coercion Semantics of Subtyping
def coerce(
    actual: Type,
    expected: Type,
) -> Type:
    _check = partial(coerce)

    if equivalent(actual, expected):
        return expected

    match actual, expected:
        case Boolean(), Boolean():
            return expected

        case Int(), Int():
            return expected

        case Symbol(), Symbol():
            return expected

        case Arrow(params=p1, ret=r1), Arrow(params=p2, ret=r2):
            if len(p1) != len(p2):
                raise ValueError("function arity mismatch")
            for actual_param, expected_param in zip(p1, p2):
                # function parameter types are contravariant
                _check(expected_param, actual_param)
            _check(r1, r2)
            return expected

        case Record(fields=fs1), Record(fields=fs2):
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

        case Arrow(), Overload(options=o2):
            if any(isSubtype(actual, option) for option in o2):
                return actual
            raise ValueError(f"can not convert from {actual} to {expected}")

        case Overload(options=o1), Arrow():
            if all(isSubtype(option, expected) for option in o1):
                return expected
            raise ValueError(f"can not convert from {actual} to {expected}")

        case _:
            raise ValueError(f"can not convert from {actual} to {expected}")


def equivalent(
    t1: Type,
    t2: Type,
) -> bool:
    match t1, t2:
        case Record(fields=fs1), Record(fields=fs2):
            if len(fs1) != len(fs2):
                return False
            for key, ty1 in fs1.items():
                if key not in fs2:
                    return False
                ty2 = fs2[key]
                if not equivalent(ty1, ty2):
                    return False
            return True

        case Tuple(values=v1), Tuple(values=v2):
            if len(v1) != len(v2):
                return False
            return all(equivalent(item1, item2) for item1, item2 in zip(v1, v2))

        case Boolean(), Boolean():
            return True

        case Int(), Int():
            return True

        case Symbol(), Symbol():
            return True

        case Arrow(params=p1, ret=r1), Arrow(params=p2, ret=r2):
            if len(p1) != len(p2):
                return False
            if not all(equivalent(param1, param2) for param1, param2 in zip(p1, p2)):
                return False
            return equivalent(r1, r2)

        case Overload(options=o1), Overload(options=o2):
            if len(o1) != len(o2):
                return False
            return all(equivalent(opt1, opt2) for opt1, opt2 in zip(o1, o2))

        case _:
            return False
