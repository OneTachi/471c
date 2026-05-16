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


def test_applicable_accepts_subtype_arguments():
    arrow = L4.Arrow(params=[L4.Record(fields={"x": L4.Int()})], ret=L4.Boolean())
    assert overload.applicable(arrow, [L4.Record(fields={"x": L4.Int(), "y": L4.Boolean()})])


def test_applicable_rejects_wrong_arity():
    arrow = L4.Arrow(params=[L4.Int(), L4.Int()], ret=L4.Int())
    assert not overload.applicable(arrow, [L4.Int()])


def test_choose_overload_returns_first_equivalent_candidate():
    candidate1 = L4.Arrow(params=[L4.Int()], ret=L4.Boolean())
    candidate2 = L4.Arrow(params=[L4.Int()], ret=L4.Boolean())
    chosen = overload.choose_overload([candidate1, candidate2], [L4.Int()])

    assert chosen == candidate1


def test_choose_overload_no_match_raises():
    candidates = [
        L4.Arrow(params=[L4.Int()], ret=L4.Boolean()),
        L4.Arrow(params=[L4.Record(fields={"x": L4.Int()})], ret=L4.Boolean()),
    ]

    with pytest.raises(ValueError):
        overload.choose_overload(candidates, [L4.Boolean()])


def test_choose_overload_ambiguous_raises_for_distinct_return_types():
    candidates = [
        L4.Arrow(params=[L4.Int()], ret=L4.Boolean()),
        L4.Arrow(params=[L4.Int()], ret=L4.Int()),
    ]

    with pytest.raises(ValueError):
        overload.choose_overload(candidates, [L4.Int()])


def test_resolve_overload_with_overload_target():
    overload_type = L4.Overload(
        options=[
            L4.Arrow(params=[L4.Int()], ret=L4.Boolean()),
            L4.Arrow(params=[L4.Record(fields={"x": L4.Int(), "y": L4.Boolean()})], ret=L4.Boolean()),
        ]
    )

    resolved = overload.resolve_overload(overload_type, [L4.Record(fields={"x": L4.Int(), "y": L4.Boolean()})])

    assert resolved.ret == L4.Boolean()
    assert resolved.params == [L4.Record(fields={"x": L4.Int(), "y": L4.Boolean()})]


def test_resolve_overload_non_callable_raises():
    with pytest.raises(TypeError):
        overload.resolve_overload(L4.Int(), [L4.Int()])


def test_is_strictly_more_specific():
    left = L4.Arrow(params=[L4.Record(fields={"x": L4.Int(), "y": L4.Boolean()}), L4.Boolean()], ret=L4.Boolean())
    right = L4.Arrow(params=[L4.Record(fields={"x": L4.Int()})], ret=L4.Boolean())

    assert not overload.is_strictly_more_specific(right, left)


def test_resolve_overload_no_applicable_raises():
    overload_type = L4.Arrow(
        params=[L4.Record(fields={"x": L4.Int(), "y": L4.Boolean()}), L4.Boolean()], ret=L4.Boolean()
    )

    with pytest.raises(ValueError):
        overload.resolve_overload(overload_type, [L4.Boolean()])
