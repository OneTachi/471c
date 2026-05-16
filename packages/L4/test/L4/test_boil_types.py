import pytest
from L4.boil_types import boil_types, boil_program, infer_term, infer_program
from collections.abc import Mapping
from L4 import syntax as L4
from L3 import syntax as L3
from util.sequential_name_generator import SequentialNameGenerator 

type Context = Mapping[L4.Identifier, L4.Type]

def test_boil_program():
    program = L4.Program(
        parameters=[("a", L4.Boolean())],
        ret=L4.Int(),
        body=L4.Immediate(value=3)
    )
    symbol_table = {}

    expected = L3.Program(
        parameters=["a0"],
        body=L3.Immediate(value=3)
    )
    _, actual = boil_program(program, symbol_table)
    assert expected == actual

def test_boil_types_restofstraightforward():
    term = L4.Primitive(operator="+", left=L4.Allocate(count=2), right=L4.Branch(
        operator="==",
        left=L4.Load(base=L4.Immediate(value=4), index=1),
        right=L4.Store(base=L4.Immediate(value=4), index=1, value=L4.Immediate(value=4)),
        consequent=L4.Begin(effects=[L4.Immediate(value=1)], value=L4.Immediate(value=1)),
        otherwise=L4.Immediate(value=2)
        ))

    symbol_table = {}
    fresh = SequentialNameGenerator()
    context = {}
    
    actual = boil_types(term, symbol_table, fresh, context)
    expected = L3.Primitive(operator="+", left=L3.Allocate(count=2), right=L3.Branch(
        operator="==",
        left=L3.Load(base=L3.Immediate(value=4), index=1),
        right=L3.Store(base=L3.Immediate(value=4), index=1, value=L3.Immediate(value=4)),
        consequent=L3.Begin(effects=[L3.Immediate(value=1)], value=L3.Immediate(value=1)),
        otherwise=L3.Immediate(value=2)
        ))
    assert actual == expected

def test_boil_types_abstract():
    term = L4.Abstract(
        parameters=[("x", L4.Int()), ("y", L4.Boolean())],
        ret=L4.Int(),
        body=L4.Reference(name="x")
    )
    symbol_table = {}
    fresh = SequentialNameGenerator()
    context = {}
    
    actual = boil_types(term, symbol_table, fresh, context)
    
    expected = L3.Abstract(
        parameters=["x", "y"],
        body=L3.Reference(name="x")
    )
    assert actual == expected

def test_boil_types_letrec():
    f_type = L4.Arrow(params=[L4.Int()], ret=L4.Int())
    lambda_term = L4.Abstract(parameters=[("x", L4.Int())], ret=L4.Int(), body=L4.Reference(name="x"))
    
    term = L4.LetRec(
        bindings=[("f", f_type, lambda_term)],
        body=L4.Apply(target=L4.Reference(name="f"), arguments=[L4.Immediate(value=1)])
    )
    
    symbol_table = {}
    fresh = SequentialNameGenerator()
    context = {}
    
    actual = boil_types(term, symbol_table, fresh, context)
    
    expected = L3.LetRec(
        bindings=[
            ("f", L3.Abstract(parameters=["x"], body=L3.Reference(name="x")))
        ],
        body=L3.Apply(target=L3.Reference(name="f"), arguments=[L3.Immediate(value=1)])
    )
    assert actual == expected


# Tested with make record so im just using its values here. If this breaks, that means makerecords may also be broken
def test_boil_types_getrecordvalue():
    record_term = L4.MakeRecord(fields=[
        ("z", L4.Immediate(value=1)),
        ("a", L4.MakeBool(value=True))
    ])
    term = L4.GetRecordValue(record=record_term, key="a")
    
    symbol_table = {}
    fresh = SequentialNameGenerator()
    context = {}
    
    actual = boil_types(term, symbol_table, fresh, context)
    
    record_l3 = boil_types(record_term, symbol_table, SequentialNameGenerator(), context)
    expected = L3.Load(base=record_l3, index=0)
    assert actual == expected

    term = L4.GetRecordValue(record=record_term, key="b")
    with pytest.raises(TypeError):
        boil_types(term, symbol_table, fresh, context)

    term = L4.GetRecordValue(record=L4.Immediate(value=4), key="a")
    with pytest.raises(TypeError):
        boil_types(term, symbol_table, fresh, context)
    

def test_boil_types_makerecord():
    term = L4.MakeRecord(fields=[
        ("z", L4.Immediate(value=2)),
        ("a", L4.MakeBool(value=True))
    ])
    symbol_table = {}
    fresh = SequentialNameGenerator()
    context = {}
    
    expected_name = "record0"
    actual = boil_types(term, symbol_table, fresh, context)
    
    expected = L3.Let(
        bindings=[(expected_name, L3.Allocate(count=2))],
        body=L3.Begin(
            effects=[
                L3.Store(base=L3.Reference(name=expected_name), index=0, value=L3.Immediate(value=1)),
                L3.Store(base=L3.Reference(name=expected_name), index=1, value=L3.Immediate(value=2))
            ],
            value=L3.Reference(name=expected_name)
        )
    )
    assert actual == expected

def test_boil_types_let():
    # (let ((x 5)) x)
    term = L4.Let(
        bindings=[("x", L4.Immediate(value=5))],
        body=L4.Reference(name="x")
    )
    symbol_table = {}
    fresh = SequentialNameGenerator()
    context = {}
    
    actual = boil_types(term, symbol_table, fresh, context)
    
    expected = L3.Let(
        bindings=[("x", L3.Immediate(value=5))],
        body=L3.Reference(name="x")
    )
    assert actual == expected


def test_boil_types_gettuplevalue():
    term = L4.GetTupleValue(index=0, term=L4.MakeBool(value=False))
    symbol_table = {}
    fresh = SequentialNameGenerator()
    context: Context = {}
    assert boil_types(term, symbol_table, fresh, context) == L3.Load(base=L3.Immediate(value=0), index=0)


def test_boil_types_maketuple():
    term = L4.MakeTuple(values=[L4.MakeBool(value=False)])
    symbol_table = {}
    fresh = SequentialNameGenerator()
    context: Context = {}
    expected_name = "tuple0"
    expected = L3.Let(
        bindings=[(expected_name, L3.Allocate(count=1))],
        body=L3.Begin(
            effects=[
                L3.Store(
                    base=L3.Reference(name=expected_name), 
                    index=0, 
                    value=L3.Immediate(value=0)
                )
            ],
            value=L3.Reference(name=expected_name)
        )
    )

    assert boil_types(term, symbol_table, fresh, context) == expected

def test_boil_types_makesymbol():
    term = L4.MakeSymbol(name="a")
    symbol_table = {}
    fresh = SequentialNameGenerator()
    context: Context = {}
    assert boil_types(term, symbol_table, fresh, context) == L3.Immediate(value=0)

def test_boil_types_if():
    term = L4.If(condition=L4.MakeBool(value=False), consequent=L4.MakeBool(value=False), otherwise=L4.MakeBool(value=False))
    symbol_table = {}
    fresh = SequentialNameGenerator()
    context: Context = {}
    assert boil_types(term, symbol_table, fresh, context) == L3.Branch(
            operator="==",
            left=L3.Immediate(value=0),
            right=L3.Immediate(value=1),
            consequent=L3.Immediate(value=0),
            otherwise=L3.Immediate(value=0)
            )

def test_boil_types_makebool():
    term = L4.MakeBool(value=False)
    symbol_table = {}
    fresh = SequentialNameGenerator()
    context: Context = {}

    assert boil_types(term, symbol_table, fresh, context) == L3.Immediate(value=0)
    term = L4.MakeBool(value=True)
    assert boil_types(term, symbol_table, fresh, context) == L3.Immediate(value=1)

def test_infer_program():
    program = L4.Program(
        parameters=[("a", L4.Boolean())],
        ret=L4.Int(),
        body=L4.Immediate(value=3)
    )
    assert infer_program(program) == L4.Int()
 
    program = L4.Program(
        parameters=[("a", L4.Boolean())],
        ret=L4.Boolean(),
        body=L4.Immediate(value=3)
    )
    with pytest.raises(TypeError):
        infer_program(program)


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
    term = L4.Branch(
        operator="==",
        left=L4.Immediate(value=1),
        right=L4.Immediate(value=1),
        consequent=L4.MakeRecord(fields=[
            ("a", L4.Immediate(value=10))
        ]),
        otherwise=L4.MakeRecord(fields=[
            ("a", L4.Immediate(value=20)),
            ("b", L4.Immediate(value=30))
        ])
    )
    assert infer_term(term, context) == L4.Record(fields={"a": L4.Int()})

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
    apply = L4.Apply(target=targ, arguments=[L4.MakeSymbol(name="hi")])
    with pytest.raises(TypeError):
        infer_term(apply, context)
    
    apply = L4.Apply(target=term, arguments=[])
    with pytest.raises(TypeError):
        infer_term(apply, context)
    
    apply = L4.Apply(target=term, arguments=[L4.MakeSymbol(name="hi")])
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
    
    term = L4.Abstract(
        parameters=[("x", L4.Int())],
        ret=L4.Boolean(),
        body=L4.Reference(name="x")
    )

    with pytest.raises(TypeError):
        infer_term(term, context)


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
    assert actual == expected

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
