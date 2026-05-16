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
    field1.append((L4.Immediate(value=3)))

    field2.append((L4.Symbol(name="a")))
    field2.append((L4.Immediate(value=2)))

    expected = L4.Tuple(values=field2)
    actual = L4.Tuple(values=field1)

    result = L4.Tuple(values=field2)

    real = subtype.coerce(actual, expected)

    assert real == result


def test_subtype_coerce_tuple_fail():
    field1: list[L4.Term] = []
    field2: list[L4.Term] = []

    field1.append((L4.Symbol(name="a")))
    field1.append((L4.Immediate(value=2)))

    field2.append((L4.Symbol(name="a")))
    field2.append((L4.Immediate(value=2)))
    field2.append((L4.Immediate(value=3)))

    expected = L4.Tuple(values=field2)
    actual = L4.Tuple(values=field1)

    with pytest.raises(ValueError):
        subtype.coerce(actual, expected)


def test_subtype_coerce_incompat():
    field1: list[L4.Term] = []
    field2: list[tuple[L4.Identifier, L4.Term]] = []

    field1.append((L4.Symbol(name="a")))
    field1.append((L4.Immediate(value=2)))

    field1.append((L4.Immediate(value=3)))

    thing1 = L4.Tuple(values=field1)
    thing2 = L4.Record(fields=field2)

    with pytest.raises(ValueError):
        subtype.coerce(thing1, thing2)


def test_equivalent_bool():
    assert subtype.equivalent(L4.Bool(value=True), L4.Bool(value=True))
    assert not subtype.equivalent(L4.Bool(value=True), L4.Bool(value=False))


def test_equivalent_symbol():
    assert subtype.equivalent(L4.Symbol(name="a"), L4.Symbol(name="a"))
    assert not subtype.equivalent(L4.Symbol(name="a"), L4.Symbol(name="b"))


def test_equivalent_immediate():
    assert subtype.equivalent(L4.Immediate(value=5), L4.Immediate(value=5))
    assert not subtype.equivalent(L4.Immediate(value=5), L4.Immediate(value=6))


def test_equivalent_tuple():
    left = L4.Tuple(values=[L4.Symbol(name="a"), L4.Immediate(value=2)])
    right = L4.Tuple(values=[L4.Symbol(name="a"), L4.Immediate(value=2)])
    assert subtype.equivalent(left, right)
    assert not subtype.equivalent(left, L4.Tuple(values=[L4.Symbol(name="a")]))


def test_equivalent_gettuplevalue():
    left = L4.GetTupleValue(term=L4.Tuple(values=[L4.Immediate(value=1)]), index=0)
    right = L4.GetTupleValue(term=L4.Tuple(values=[L4.Immediate(value=1)]), index=0)
    assert subtype.equivalent(left, right)
    assert not subtype.equivalent(left, L4.GetTupleValue(term=L4.Tuple(values=[L4.Immediate(value=2)]), index=0))


def test_equivalent_record():
    left = L4.Record(fields=[("x", L4.Immediate(value=3)), ("y", L4.Bool(value=False))])
    right = L4.Record(fields=[("x", L4.Immediate(value=3)), ("y", L4.Bool(value=False))])
    assert subtype.equivalent(left, right)
    assert not subtype.equivalent(left, L4.Record(fields=[("y", L4.Bool(value=False)), ("x", L4.Immediate(value=3))]))


def test_equivalent_getrecordvalue():
    left = L4.GetRecordValue(record=L4.Record(fields=[("x", L4.Immediate(value=7))]), key="x")
    right = L4.GetRecordValue(record=L4.Record(fields=[("x", L4.Immediate(value=7))]), key="x")
    assert subtype.equivalent(left, right)
    assert not subtype.equivalent(
        left, L4.GetRecordValue(record=L4.Record(fields=[("x", L4.Immediate(value=8))]), key="x")
    )


def test_equivalent_reference():
    assert subtype.equivalent(L4.Reference(name="x"), L4.Reference(name="x"))
    assert not subtype.equivalent(L4.Reference(name="x"), L4.Reference(name="y"))


def test_equivalent_abstract():
    left = L4.Abstract(parameters=["x"], body=L4.Symbol(name="x"))
    right = L4.Abstract(parameters=["x"], body=L4.Symbol(name="x"))
    assert subtype.equivalent(left, right)
    assert not subtype.equivalent(left, L4.Abstract(parameters=["y"], body=L4.Symbol(name="y")))

    right2 = L4.Abstract(parameters=["x, y"], body=L4.Symbol(name="y"))

    assert not subtype.equivalent(left, right2)


def test_equivalent_apply():
    left = L4.Apply(target=L4.Symbol(name="f"), arguments=[L4.Immediate(value=1)])
    right = L4.Apply(target=L4.Symbol(name="f"), arguments=[L4.Immediate(value=1)])
    assert subtype.equivalent(left, right)
    assert not subtype.equivalent(left, L4.Apply(target=L4.Symbol(name="g"), arguments=[L4.Immediate(value=1)]))

    right2 = L4.Apply(target=L4.Symbol(name="f"), arguments=[L4.Immediate(value=1), L4.Immediate(value=2)])

    assert not subtype.equivalent(left, right2)


def test_equivalent_primitive():
    left = L4.Primitive(operator="+", left=L4.Immediate(value=1), right=L4.Immediate(value=2))
    right = L4.Primitive(operator="+", left=L4.Immediate(value=1), right=L4.Immediate(value=2))
    assert subtype.equivalent(left, right)
    assert not subtype.equivalent(
        left, L4.Primitive(operator="-", left=L4.Immediate(value=1), right=L4.Immediate(value=2))
    )


def test_equivalent_branch():
    left = L4.Branch(
        operator="<",
        left=L4.Immediate(value=1),
        right=L4.Immediate(value=2),
        consequent=L4.Bool(value=True),
        otherwise=L4.Bool(value=False),
    )
    right = L4.Branch(
        operator="<",
        left=L4.Immediate(value=1),
        right=L4.Immediate(value=2),
        consequent=L4.Bool(value=True),
        otherwise=L4.Bool(value=False),
    )
    assert subtype.equivalent(left, right)
    assert not subtype.equivalent(
        left,
        L4.Branch(
            operator="==",
            left=L4.Immediate(value=1),
            right=L4.Immediate(value=2),
            consequent=L4.Bool(value=True),
            otherwise=L4.Bool(value=False),
        ),
    )


def test_equivalent_allocate():
    assert subtype.equivalent(L4.Allocate(count=1), L4.Allocate(count=1))
    assert not subtype.equivalent(L4.Allocate(count=1), L4.Allocate(count=2))


def test_equivalent_load():
    left = L4.Load(base=L4.Symbol(name="x"), index=0)
    right = L4.Load(base=L4.Symbol(name="x"), index=0)
    assert subtype.equivalent(left, right)
    assert not subtype.equivalent(left, L4.Load(base=L4.Symbol(name="y"), index=0))


def test_equivalent_store():
    left = L4.Store(base=L4.Symbol(name="x"), index=0, value=L4.Immediate(value=1))
    right = L4.Store(base=L4.Symbol(name="x"), index=0, value=L4.Immediate(value=1))
    assert subtype.equivalent(left, right)
    assert not subtype.equivalent(left, L4.Store(base=L4.Symbol(name="x"), index=1, value=L4.Immediate(value=1)))


def test_equivalent_begin():
    left = L4.Begin(effects=[L4.Immediate(value=1)], value=L4.Immediate(value=2))
    right = L4.Begin(effects=[L4.Immediate(value=1)], value=L4.Immediate(value=2))
    assert subtype.equivalent(left, right)
    assert not subtype.equivalent(left, L4.Begin(effects=[L4.Immediate(value=2)], value=L4.Immediate(value=2)))

    right2 = L4.Begin(effects=[L4.Immediate(value=1), L4.Immediate(value=2)], value=L4.Immediate(value=2))

    assert not subtype.equivalent(left, right2)


def test_equivalent_let():
    left = L4.Let(bindings=[("x", L4.Immediate(value=1))], body=L4.Symbol(name="x"))
    right = L4.Let(bindings=[("x", L4.Immediate(value=1))], body=L4.Symbol(name="x"))
    assert subtype.equivalent(left, right)
    assert not subtype.equivalent(left, L4.Let(bindings=[("x", L4.Immediate(value=2))], body=L4.Symbol(name="x")))

    right2 = L4.Let(bindings=[("x", L4.Immediate(value=1)), ("y", L4.Immediate(value=2))], body=L4.Symbol(name="x"))

    assert not subtype.equivalent(left, right2)


def test_equivalent_letrec():
    left = L4.LetRec(bindings=[("x", L4.Symbol(name="x"))], body=L4.Symbol(name="x"))
    right = L4.LetRec(bindings=[("x", L4.Symbol(name="x"))], body=L4.Symbol(name="x"))
    assert subtype.equivalent(left, right)
    assert not subtype.equivalent(left, L4.LetRec(bindings=[("x", L4.Symbol(name="y"))], body=L4.Symbol(name="x")))

    right2 = L4.LetRec(bindings=[("x", L4.Symbol(name="x")), ("y", L4.Immediate(value=2))], body=L4.Symbol(name="x"))

    assert not subtype.equivalent(left, right2)


def test_equivalent_different_term_kinds():
    assert not subtype.equivalent(L4.Bool(value=True), L4.Symbol(name="x"))
