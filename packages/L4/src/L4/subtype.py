from functools import partial

from .syntax import Identifier, Record, Term, Tuple


# See Turbak. 12.1.2 Dimensions of Subtyping: Subset Semantics versus Coercion Semantics of Subtyping
def coerce(
    actual: Term,
    expected: Term,
) -> Term:
    _coerce = partial(coerce)

    if equivalent(actual, expected):
        return actual

    match actual, expected:
        case Record(fields=fs1), Record(fields=fs2):
            sorted_expected = sorted(fs2)

            components: list[tuple[Identifier, Term]] = []

            for key, expected_ty in sorted_expected:
                key_present = [item for item in fs1 if item[0] == key]
                if not key_present:
                    raise ValueError(f"missing field {key} in {actual}")

                components.append((key, expected_ty))

            return Record(fields=components)

        case Tuple(values=v1), Tuple(values=v2):
            new_vals: list[Term] = []

            for val in v2:
                val_present = [item for item in v1 if equivalent(item, val)]
                if not val_present:
                    raise ValueError(f"missing field {val} in {actual}")

                new_vals.append(val)

            return Tuple(values=new_vals)

        case _:
            raise ValueError(f"can not convert from {actual} to {expected}")


def equivalent(
    t1: Term,
    t2: Term,
) -> bool:
    match t1, t2:
        case Record(fields=fs1), Record(fields=fs2):
            if len(fs1) != len(fs2):
                return False

            same = True

            for thing1 in fs1:
                for thing2 in fs2:
                    if thing1 != thing2:
                        same = False

            return same

        case Tuple(values=fs1), Tuple(values=fs2):
            if len(fs1) != len(fs2):
                return False

            same = True

            for thing1 in fs1:
                for thing2 in fs2:
                    if thing1 != thing2:
                        same = False

            return same

        case _:
            return False
