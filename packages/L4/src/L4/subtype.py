from functools import partial

from .syntax import Identifier, Record, Term


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
            sorted_actual = sorted(fs1)

            components: list[tuple[Identifier, Term]] = []

            for key, expected_ty in sorted_expected:
                key_present = [item for item in fs1 if item[0] == key]
                if not key_present:
                    raise ValueError(f"missing field {key} in {actual}")

                components.append((key, expected_ty))

            return Record(fields=components)

        case _:
            raise ValueError(f"can not convert from {actual} to {expected}")


def equivalent(
    t1: Term,
    t2: Term,
) -> bool:
    match t1, t2:
        case _:
            return False
