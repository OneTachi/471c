from collections.abc import Callable, Mapping
from functools import partial

from L4 import syntax as L4


# See Turbak. 12.1.2 Dimensions of Subtyping: Subset Semantics versus Coercion Semantics of Subtyping
def coerce(
    actual: L4.Type,
    expected: L4.Type,
    term: L4.Term,
    fresh: Callable[[str], str],
) -> L4.Term:
    _coerce = partial(coerce, fresh=fresh)

    if equivalent(actual, expected):
        return term

    match actual, expected:
        case L4.Record(fields=fs1), L4.Record(fields=fs2):
            # expected fields define projection order
            sorted_expected = sorted(fs2.items())

            components: list[L4.Term] = []

            for key, expected_ty in sorted_expected:
                if key not in fs1:
                    raise ValueError(f"missing field {key} in {actual}")

                actual_ty = fs1[key]

                # project from source term
                index = sorted(fs1.keys()).index(key)

                projected = T0.Project(
                    target=term,
                    index=index,
                )

                components.append(_coerce(actual_ty, expected_ty, projected))

            return L4.Join(components=components)

        case _:
            raise ValueError(f"can not convert from {actual} to {expected}")


def equivalent(
    t1: L4.Type,
    t2: L4.Type,
) -> bool:
    match t1, t2:
        case L4.Arrow(domain=d1, codomain=c1), T1.Arrow(domain=d2, codomain=c2):
            return (
                equivalent(d1, d2)  # domain
                and equivalent(c1, c2)  # codomain
            )

        case L4.Trivial(), L4.Trivial():
            return True

        case L4.Record(fields=fs1), L4.Record(fields=fs2):
            return (
                fs1.keys() == fs2.keys()  #
                and all(equivalent(fs1[k], fs2[k]) for k in fs1.keys())  #
            )

        case _:
            return False


def elaborate_type(
    type: T1.Type,
) -> T0.Type:
    _type = partial(elaborate_type)

    match type:
        case T1.Arrow(domain=domain, codomain=codomain):
            return T0.Arrow(
                domain=_type(domain),
                codomain=_type(codomain),
            )

        case T1.Int():
            return T0.Int()

        case T1.Trivial():
            return T0.Trivial()

        case T1.Record(fields=fields):
            return T0.Product(components=[_type(type) for _key, type in sorted(fields.items())])


def check_term(
    term: T1.Term,
    expected: T1.Type,
    gamma: Mapping[T1.Identifier, T1.Type],
    fresh: Callable[[str], str],
) -> T0.Term:
    _type = partial(elaborate_type)
    _check = partial(check_term, gamma=gamma, fresh=fresh)
    _infer = partial(infer_term, gamma=gamma, fresh=fresh)

    match term:
        case T1.Abstraction(parameter=parameter, body=body):
            match expected:
                case T1.Arrow(domain=domain, codomain=codomain):
                    body = _check(body, codomain, gamma={**gamma, parameter: domain})
                    return T0.Abstraction(
                        parameter=parameter,
                        domain=_type(domain),
                        body=body,
                    )

                case expected:  # pragma: no branch
                    raise ValueError(f"expected {term} to be {T1.Arrow} not {expected}")

        case T1.Branch(operator=operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            match operator:
                case "<" | "==":
                    left = _check(left, T1.Int())
                    right = _check(right, T1.Int())
                    consequent = _check(consequent, expected)
                    otherwise = _check(otherwise, expected)
                    return T0.Branch(
                        operator=operator,
                        left=left,
                        right=right,
                        motive=_type(expected),
                        consequent=consequent,
                        otherwise=otherwise,
                    )

        case term:
            actual, elaborated = _infer(term)

            if not equivalent(actual, expected):
                raise ValueError(f"expected {term} to be {expected} not {actual}")

            return elaborated


def infer_term(
    term: T1.Term,
    gamma: Mapping[T1.Identifier, T1.Type],
    fresh: Callable[[str], str],
) -> tuple[T1.Type, T0.Term]:
    _check = partial(check_term, gamma=gamma, fresh=fresh)
    _infer = partial(infer_term, gamma=gamma, fresh=fresh)

    match term:
        case T1.Ascription(annotation=annotation, target=target):
            target = _check(target, annotation)
            return annotation, target

        case T1.Reference(name=name):
            match gamma.get(name):
                case None:
                    raise ValueError(f"unknown variable: {name}")

                case type:
                    return (
                        type,
                        T0.Reference(name=name),
                    )

        case T1.Abstraction():
            raise ValueError(f"can not infer type of {term}")

        case T1.Application(target=target, argument=argument):
            match _infer(target):
                case T1.Arrow(domain=domain, codomain=codomain), target:
                    return (
                        codomain,
                        T0.Application(
                            target=target,
                            argument=_check(argument, domain),
                        ),
                    )

                case target_type:
                    raise ValueError(f"expected {target} to be {T1.Arrow} not {target_type}")

        case T1.Immediate(value=value):
            return (
                T1.Int(),
                T0.Immediate(value=value),
            )

        case T1.Primitive(operator=operator, left=left, right=right):
            match operator:
                case "+" | "-" | "*":
                    left = _check(left, T1.Int())
                    right = _check(right, T1.Int())
                    return (
                        T1.Int(),
                        T0.Primitive(
                            operator=operator,
                            left=left,
                            right=right,
                        ),
                    )

        case T1.Branch():
            raise ValueError(f"can not infer type of {term}")

        case T1.Sole():
            return (
                T1.Trivial(),
                T0.Sole(),
            )

        case T1.Construct(fields=fields):
            results = {key: _infer(value) for key, value in fields.items()}
            types = {key: type for key, (type, _value) in results.items()}
            values = {key: value for key, (_type, value) in results.items()}

            return (
                T1.Record(fields=types),
                T0.Join(components=[value for _key, value in sorted(values.items())]),
            )

        case T1.Select(target=target, key=key):
            match _infer(target):
                case T1.Record(fields=fields), target:
                    match fields.get(key):
                        case None:
                            raise ValueError(f"unknown key {key} in {fields}")

                        case type:
                            return (
                                type,
                                T0.Project(
                                    target=target,
                                    index=sorted(fields.keys()).index(key),
                                ),
                            )

                case target_type, _:
                    raise ValueError(f"expected {target} to be {T1.Record} not {target_type}")
