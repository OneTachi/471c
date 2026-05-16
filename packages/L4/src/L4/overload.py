from collections.abc import Sequence

from .subtype import equivalent, isSubtype
from .syntax import Arrow, Overload, Type


def applicable(arrow: Arrow, arg_types: Sequence[Type]) -> bool:
    if len(arrow.params) != len(arg_types):
        return False
    return all(isSubtype(actual, expected) for actual, expected in zip(arg_types, arrow.params))


def is_strictly_more_specific(left: Arrow, right: Arrow) -> bool:
    if len(left.params) != len(right.params):
        return False

    if not all(isSubtype(left_param, right_param) for left_param, right_param in zip(left.params, right.params)):
        return False

    return any(not isSubtype(right_param, left_param) for left_param, right_param in zip(left.params, right.params))


def choose_overload(candidates: Sequence[Arrow], arg_types: Sequence[Type]) -> Arrow:
    applicable_candidates = [candidate for candidate in candidates if applicable(candidate, arg_types)]
    if not applicable_candidates:
        raise ValueError(f"No overload matches {arg_types}")

    best_candidates = [
        candidate
        for candidate in applicable_candidates
        if not any(
            candidate is not other and is_strictly_more_specific(other, candidate) for other in applicable_candidates
        )
    ]

    if not best_candidates:
        raise ValueError(f"No best overload found for {arg_types}")

    first = best_candidates[0]
    if all(equivalent(first, candidate) for candidate in best_candidates):
        return first

    raise ValueError(f"Ambiguous overload resolution for {arg_types}")


def resolve_overload(target: Type, arg_types: Sequence[Type]) -> Arrow:
    match target:
        case Arrow():
            if not applicable(target, arg_types):
                raise ValueError(f"Function type {target} is not applicable to {arg_types}")
            return target

        case Overload(options=options):
            return choose_overload(options, arg_types)

        case _:
            raise TypeError(f"Target {target} is not callable")
