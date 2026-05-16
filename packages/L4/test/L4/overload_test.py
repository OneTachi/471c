import pytest
from L4 import overload
from L4 import syntax as L4


def test_choose_overload_prefers_more_specific():
    candidates = [
        L4.Arrow(params=[L4.Record(fields={"x": L4.Int()})], ret=L4.Boolean()),
        L4.Arrow(params=[L4.Record(fields={"x": L4.Int(), "y": L4.Boolean()})], ret=L4.Boolean()),
    ]
    actual_args = [L4.Record(fields={"x": L4.Int(), "y": L4.Boolean()})]

    chosen = overload.choose_overload(candidates, actual_args)

    assert chosen == candidates[1]


def test_choose_overload_ambiguous_raises():
    candidates = [
        L4.Arrow(params=[L4.Int()], ret=L4.Boolean()),
        L4.Arrow(params=[L4.Int()], ret=L4.Int()),
    ]

    with pytest.raises(ValueError):
        overload.choose_overload(candidates, [L4.Int()])


def test_resolve_overload_with_direct_arrow():
    arrow = L4.Arrow(params=[L4.Int()], ret=L4.Boolean())
    resolved = overload.resolve_overload(arrow, [L4.Int()])

    assert resolved == arrow
