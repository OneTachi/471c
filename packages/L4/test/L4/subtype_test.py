import pytest
from L4 import subtype
from L4 import syntax as L4


def test_subtype_coerce_record_equivalent():
    field1: list[tuple[L4.Identifier, L4.Term]] = []
    field2: list[tuple[L4.Identifier, L4.Term]] = []

    field1.append(("x", L4.Immediate(value=2)))
    field2.append(("x", L4.Immediate(value=2)))

    expected = L4.Record(fields=field1)
    actual = L4.Record(fields=field2)

    result = L4.Record(fields=field1)

    real = subtype.coerce(actual, expected)

    assert real == result


def test_subtype_coerce_record_nonequivalent():
    field1: list[tuple[L4.Identifier, L4.Term]] = []
    field2: list[tuple[L4.Identifier, L4.Term]] = []

    field1.append(("x", L4.Immediate(value=3)))
    field1.append(("y", L4.Immediate(value=2)))

    field2.append(("y", L4.Immediate(value=2)))
    field2.append(("x", L4.Immediate(value=3)))

    expected = L4.Record(fields=field1)
    actual = L4.Record(fields=field2)

    result = L4.Record(fields=field1)

    real = subtype.coerce(actual, expected)

    assert real == result


def test_subtype_coerce_record():
    field1: list[tuple[L4.Identifier, L4.Term]] = []
    field2: list[tuple[L4.Identifier, L4.Term]] = []

    field1.append(("x", L4.Immediate(value=2)))

    field2.append(("y", L4.Immediate(value=2)))
    field2.append(("x", L4.Immediate(value=3)))

    expected = L4.Record(fields=field1)
    actual = L4.Record(fields=field2)

    result = L4.Record(fields=field1)

    real = subtype.coerce(actual, expected)

    assert real == result


def test_subtype_coerce_record_missing_field():
    field1: list[tuple[L4.Identifier, L4.Term]] = []
    field2: list[tuple[L4.Identifier, L4.Term]] = []

    field1.append(("z", L4.Immediate(value=2)))

    field2.append(("y", L4.Immediate(value=2)))
    field2.append(("x", L4.Immediate(value=3)))

    expected = L4.Record(fields=field1)
    actual = L4.Record(fields=field2)

    with pytest.raises(ValueError):
        subtype.coerce(actual, expected)


def test_subtype_coerce_tuple():
    field1: list[L4.Term] = []
    field2: list[L4.Term] = []

    field1.append((L4.Symbol(name="a")))
    field1.append((L4.Immediate(value=2)))

    field2.append((L4.Symbol(name="a")))
    field2.append((L4.Immediate(value=2)))

    expected = L4.Tuple(values=field1)
    actual = L4.Tuple(values=field2)

    result = L4.Tuple(values=field1)

    real = subtype.coerce(actual, expected)

    assert real == result
