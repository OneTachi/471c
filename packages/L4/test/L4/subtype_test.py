import pytest
from L4 import subtype
from L4 import syntax as L4


def test_subtype_coerce_record_equivalent():
    expected = L4.Record(fields={"x": L4.Int(), "y": L4.Boolean()})
    actual = L4.Record(fields={"x": L4.Int(), "y": L4.Boolean()})

    result = subtype.coerce(actual, expected)

    assert result == expected


def test_subtype_coerce_record_reorders_fields():
    expected = L4.Record(fields={"x": L4.Int(), "y": L4.Boolean()})
    actual = L4.Record(fields={"y": L4.Boolean(), "x": L4.Int()})

    result = subtype.coerce(actual, expected)

    assert result == expected


def test_subtype_coerce_record_missing_field_raises():
    expected = L4.Record(fields={"z": L4.Int()})
    actual = L4.Record(fields={"x": L4.Int(), "y": L4.Boolean()})

    with pytest.raises(ValueError):
        subtype.coerce(actual, expected)


def test_subtype_coerce_tuple_truncates():
    expected = L4.Tuple(values=[L4.Symbol(), L4.Int()])
    actual = L4.Tuple(values=[L4.Symbol(), L4.Int(), L4.Boolean()])

    result = subtype.coerce(actual, expected)

    assert result == expected


def test_subtype_coerce_tuple_too_short_raises():
    expected = L4.Tuple(values=[L4.Symbol(), L4.Int(), L4.Boolean()])
    actual = L4.Tuple(values=[L4.Symbol(), L4.Int()])

    with pytest.raises(ValueError):
        subtype.coerce(actual, expected)


def test_subtype_coerce_incompatible_raises():
    actual = L4.Tuple(values=[L4.Symbol(), L4.Int()])
    expected = L4.Record(fields={"x": L4.Int()})

    with pytest.raises(ValueError):
        subtype.coerce(actual, expected)


def test_equivalent_boolean():
    assert subtype.equivalent(L4.Boolean(), L4.Boolean())
    assert not subtype.equivalent(L4.Boolean(), L4.Int())


def test_equivalent_int():
    assert subtype.equivalent(L4.Int(), L4.Int())
    assert not subtype.equivalent(L4.Int(), L4.Symbol())


def test_equivalent_symbol():
    assert subtype.equivalent(L4.Symbol(), L4.Symbol())


def test_equivalent_tuple():
    left = L4.Tuple(values=[L4.Int(), L4.Boolean()])
    right = L4.Tuple(values=[L4.Int(), L4.Boolean()])

    assert subtype.equivalent(left, right)
    assert not subtype.equivalent(left, L4.Tuple(values=[L4.Int()]))
    assert not subtype.equivalent(left, L4.Tuple(values=[L4.Boolean(), L4.Boolean()]))


def test_equivalent_record():
    left = L4.Record(fields={"x": L4.Int(), "y": L4.Boolean()})
    right = L4.Record(fields={"x": L4.Int(), "y": L4.Boolean()})
    swapped = L4.Record(fields={"y": L4.Boolean(), "x": L4.Int()})

    assert subtype.equivalent(left, right)
    assert subtype.equivalent(left, swapped)
    assert not subtype.equivalent(left, L4.Record(fields={"x": L4.Boolean(), "y": L4.Boolean()}))
    assert not subtype.equivalent(left, L4.Record(fields={"x": L4.Int()}))


def test_equivalent_arrow():
    left = L4.Arrow(params=[L4.Int(), L4.Boolean()], ret=L4.Boolean())
    right = L4.Arrow(params=[L4.Int(), L4.Boolean()], ret=L4.Boolean())

    assert subtype.equivalent(left, right)
    assert not subtype.equivalent(left, L4.Arrow(params=[L4.Int()], ret=L4.Boolean()))
    assert not subtype.equivalent(left, L4.Arrow(params=[L4.Int(), L4.Boolean()], ret=L4.Boolean()))


def test_equivalent_arrow_param_types_differ():
    left = L4.Arrow(params=[L4.Int()], ret=L4.Boolean())
    right = L4.Arrow(params=[L4.Boolean()], ret=L4.Boolean())

    assert not subtype.equivalent(left, right)


def test_equivalent_record_different_keys():
    assert not subtype.equivalent(L4.Record(fields={"x": L4.Int()}), L4.Record(fields={"y": L4.Int()}))


def test_equivalent_different_types_are_not_equivalent():
    assert not subtype.equivalent(L4.Boolean(), L4.Symbol())
    assert not subtype.equivalent(L4.Tuple(values=[L4.Int()]), L4.Record(fields={"x": L4.Int()}))


def test_isSubtype_wraps_coerce():
    actual = L4.Record(fields={"x": L4.Int(), "y": L4.Boolean()})
    expected = L4.Record(fields={"x": L4.Int()})

    assert subtype.isSubtype(actual, expected)
    assert not subtype.isSubtype(L4.Tuple(values=[L4.Int()]), expected)
