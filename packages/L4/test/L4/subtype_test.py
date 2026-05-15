from L4 import subtype
from L4 import syntax as L4


def test_subtype_coerce():
    field1: list[tuple[L4.Identifier, L4.Term]] = []
    field2: list[tuple[L4.Identifier, L4.Term]] = []

    field1.append(("x", L4.Immediate(value=2)))
    field2.append(("x", L4.Immediate(value=2)))

    expected = L4.Record(fields=field1)
    actual = L4.Record(fields=field2)

    result = L4.Record(fields=field1)

    real = subtype.coerce(actual, expected)

    assert real == result
