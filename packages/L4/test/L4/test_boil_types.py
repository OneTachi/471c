import pytest
from L4.boil_types import boil_types, boil_program, infer_term, infer_program
from collections.abc import Mapping
from L4 import syntax as L4


type Context = Mapping[L4.Identifier, L4.Type]

def test_infer_program():
    program = L4.Program(
        parameters=[("a", L4.Boolean())],
        ret=L4.Int(),
        body=L4.Immediate(value=3)
    )
    context: Context = {}
    assert infer_program(program) == L4.Int()


def test_infer_term_store():
    term = L4.Store(base=L4.Immediate(value=2), index=1, value=L4.Immediate(value=3))
    context: Context = {}
    assert infer_term(term, context) == L4.Int()
    term = L4.Store(base=L4.MakeBool(value=False), index=1, value=L4.Immediate(value=3))
    with pytest.raises(TypeError):
        infer_term(term, context)
    term = L4.Store(value=L4.MakeBool(value=False), index=1, base=L4.Immediate(value=3))
    with pytest.raises(TypeError):
        infer_term(term, context)


def test_infer_term_load():
    term = L4.Load(base=L4.Immediate(value=2), index=1)
    context: Context = {}
    assert infer_term(term, context) == L4.Int()
    term = L4.Load(base=L4.MakeBool(value=False), index=1)
    with pytest.raises(TypeError):
        infer_term(term, context)

def test_infer_term_allocate():
    term = L4.Allocate(count=2)
    context: Context = {}
    assert infer_term(term, context) == L4.Int()

def test_infer_term_branch():
    term = L4.Branch(operator="==", left=L4.Immediate(value=1), right=L4.MakeBool(value=False), consequent=L4.MakeBool(value=False), otherwise=L4.MakeBool(value=False))
    context: Context = {}
    
    with pytest.raises(TypeError):
        infer_term(term, context)
    
    term = L4.Branch(operator="==", right=L4.Immediate(value=1), left=L4.MakeBool(value=False), consequent=L4.MakeBool(value=False), otherwise=L4.MakeBool(value=False))
    with pytest.raises(TypeError):
        infer_term(term, context)
    
    term = L4.Branch(operator="==", right=L4.Immediate(value=1), left=L4.Immediate(value=1), consequent=L4.MakeBool(value=False), otherwise=L4.MakeBool(value=False))
    assert infer_term(term, context) == L4.Boolean()
    
    term = L4.Branch(operator="==", right=L4.Immediate(value=1), left=L4.Immediate(value=1), consequent=L4.MakeBool(value=False), otherwise=L4.Immediate(value=1))
    with pytest.raises(TypeError):
        infer_term(term, context)

def test_infer_term_begin():
    term = L4.Begin(effects=[L4.Immediate(value=2)], value=L4.Immediate(value=0))
    context: Context = {}
    assert infer_term(term, context) == L4.Int()
    
def test_infer_term_letrec():
    f_type = L4.Arrow(params=[L4.Int()], ret=L4.Int())
    f_body = L4.Abstract(
        parameters=[("x", L4.Int())],
        ret=L4.Int(),
        body=L4.Apply(target=L4.Reference(name="f"), arguments=[L4.Reference(name="x")])
    )
    
    term = L4.LetRec(
        bindings=[("f", f_type, f_body)],
        body=L4.Apply(target=L4.Reference(name="f"), arguments=[L4.Immediate(value=1)])
    )
    context: Context = {}
    assert infer_term(term, context) == L4.Int()

    term = L4.LetRec(
        bindings=[("f", L4.Int(), L4.MakeBool(value=True))],
        body=L4.Immediate(value=1)
    )
    with pytest.raises(TypeError):
        infer_term(term, context)

def test_infer_term_apply():
    term = L4.Abstract(
        parameters=[("x", L4.Int())],
        ret=L4.Int(),
        body=L4.Reference(name="x")
    )
    apply = L4.Apply(target=term, arguments=[L4.Immediate(value=10)])
    context: Context = {}
    assert infer_term(apply, context) == L4.Int()
    
    targ = L4.Immediate(value=10)
    apply = L4.Apply(target=targ, arguments=[L4.MakeBool(value=False)])
    with pytest.raises(TypeError):
        infer_term(apply, context)
    
    apply = L4.Apply(target=term, arguments=[])
    with pytest.raises(TypeError):
        infer_term(apply, context)

def test_infer_term_abstract():
    term = L4.Abstract(
        parameters=[("x", L4.Int())],
        ret=L4.Int(),
        body=L4.Reference(name="x")
    )
    context: Context = {}
    expected = L4.Arrow(params=[L4.Int()], ret=L4.Int())
    assert infer_term(term, context) == expected

def test_infer_term_if():
    term = L4.If(
        condition=L4.MakeBool(value=True),
        consequent=L4.Immediate(value=1),
        otherwise=L4.Immediate(value=0)
    )
    context: Context = {}
    actual = infer_term(term, context)
    expected = L4.Int()
    assert actual == expected

    term = L4.If(
        condition=L4.Immediate(value=2),
        consequent=L4.Immediate(value=1),
        otherwise=L4.Immediate(value=0)
    )
    with pytest.raises(TypeError):
        infer_term(term, context)

    term = L4.If(
        condition=L4.MakeBool(value=True),
        consequent=L4.Immediate(value=1),
        otherwise=L4.MakeBool(value=False)
    )
    with pytest.raises(TypeError):
        infer_term(term, context)
    

def test_infer_term_let():
    term = L4.Let(
        bindings=[("x", L4.Immediate(value=5))],
        body=L4.Reference(name="x")
    )
    context: Context = {}

    expected = L4.Int()
    actual = infer_term(term, context)
    assert actual == expected

def test_infer_term_getrecord():
    rec_term = L4.MakeRecord(fields=[("a", L4.Immediate(value=2)), ("b", L4.MakeBool(value=True))])
    context : Context = {"hi": L4.Int()}

    term = L4.GetRecordValue(record=rec_term, key="b")
    assert infer_term(term, context) == L4.Boolean()

    term = L4.GetRecordValue(record=rec_term, key="c")
    with pytest.raises(TypeError):
        infer_term(term, context)

    not_rec = L4.Immediate(value=2)
    term = L4.GetRecordValue(record=not_rec, key="c")
    with pytest.raises(TypeError):
        infer_term(term, context)

def test_infer_term_gettuple():
    term = L4.GetTupleValue(term=L4.MakeTuple(values=[L4.Immediate(value=2)]), index=0)
    context : Context = {"hi": L4.Int()}

    expected = L4.Int()
    actual = infer_term(term, context)

    term = L4.GetTupleValue(term=L4.Immediate(value=2), index=0)
    with pytest.raises(TypeError):
        infer_term(term, context)
    
    term = L4.GetTupleValue(term=L4.MakeTuple(values=[L4.Immediate(value=2)]), index=1)
    with pytest.raises(TypeError):
        infer_term(term, context)

def test_infer_term_reference():
    term = L4.Reference(name="hi")
    context : Context = {"hi": L4.Int()}

    expected = L4.Int()
    actual = infer_term(term, context)
    
    term = L4.Reference(name="i")
    with pytest.raises(TypeError):
        infer_term(term, context)

    assert actual == expected

def test_infer_term_maketuple():
    term = L4.MakeTuple(values=[L4.Immediate(value=2)])
    context : Context = {}

    expected = L4.Tuple(values=[L4.Int()])
    actual = infer_term(term, context)

    assert actual == expected

def test_infer_term_makerecord():
    term = L4.MakeRecord(fields=[("a", L4.Immediate(value=2))])
    context : Context = {}

    expected = L4.Record(fields={"a": L4.Int()})
    actual = infer_term(term, context)

    assert actual == expected

def test_infer_term_makesymbol():
    term = L4.MakeSymbol(name="hi")
    context : Context = {}

    expected = L4.Symbol()
    actual = infer_term(term, context)

    assert actual == expected


def test_infer_term_makebool():
    term = L4.MakeBool(value=False)
    context : Context = {}
    expected = L4.Boolean()
    actual = infer_term(term, context)

    assert actual == expected

def test_infer_term_immediate():
    term = L4.Immediate(value=2)
    context : Context = {}

    expected = L4.Int()
    actual = infer_term(term, context)

    assert actual == expected

def test_infer_term_primitive():
    term = L4.Primitive(operator="-", left=L4.Immediate(value=2), right=L4.Immediate(value=2))
    context : Context = {}

    expected = L4.Int()
    actual = infer_term(term, context)

    assert actual == expected
    
    term = L4.Primitive(operator="-", left=L4.MakeBool(value=False), right=L4.Immediate(value=2))
    
    with pytest.raises(TypeError):
        infer_term(term, context)

    term = L4.Primitive(operator="-", right=L4.MakeBool(value=False), left=L4.Immediate(value=2))
    with pytest.raises(TypeError):
        infer_term(term, context)
