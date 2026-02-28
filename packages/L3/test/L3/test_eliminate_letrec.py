import pytest
from L2 import syntax as L2
from L3 import syntax as L3
from L3.eliminate_letrec import Context, eliminate_letrec_program, eliminate_letrec_term

def test_check_term_letrec_inside_bound():
    term = L3.LetRec(
        bindings=[("x", L3.Immediate(value=0)), ("y", L3.Primitive(operator="-", left=L3.Reference(name="x"), right=L3.Immediate(value=1)))],
        body=L3.Reference(name="y")
    )

    context: Context = {}

    expected = L2.Let(
        bindings=[("x", L2.Allocate(count=1)), ("y", L2.Allocate(count=1))],
        body=L2.Begin(
            effects=[
                L2.Store(base=L2.Reference(name="x"), index=0, value=L2.Immediate(value=0)),
                L2.Store(base=L2.Reference(name="y"), index=0, value=L2.Primitive(operator="-", left=L2.Load(base=L2.Reference(name="x"), index=0), right=L2.Immediate(value=1)))
            ],
            value=L2.Load(base=L2.Reference(name="y"), index=0)
        )
    )
    
    actual = eliminate_letrec_term(term, context)

    assert actual == expected

def test_check_term_let():
    term = L3.Let(
        bindings=[
            ("x", L3.Immediate(value=0)),
        ],
        body=L3.Reference(name="x"),
    )

    context: Context = {}

    expected = L2.Let(
        bindings=[
            ("x", L2.Immediate(value=0)),
        ],
        body=L2.Reference(name="x"),
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected

def test_eliminate_letrec_program():
    program = L3.Program(
        parameters=[],
        body=L3.Immediate(value=0),
    )

    expected = L2.Program(
        parameters=[],
        body=L2.Immediate(value=0),
    )

    actual = eliminate_letrec_program(program)

    assert actual == expected

def test_check_term_reference_basic():
    term = L3.Reference(
        name="x",
    )

    context: Context = {}

    expected = L2.Reference(
        name="x",
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected

def test_check_term_reference_context_bound():
    term = L3.Reference(
        name="x",
    )

    context: Context = {"x" : None}

    expected = L2.Load(base=L2.Reference(name="x"), index=0)

    actual = eliminate_letrec_term(term, context)

    assert actual == expected
    

def test_check_term_abstract_basic():
    term = L3.Abstract(
        parameters=[
            "hi", "wow"
        ],
        body=L3.Reference(name="x"),
    )

    context: Context = {}

    expected = L2.Abstract(
        parameters=[
            "hi", "wow"
        ],
        body=L2.Reference(name="x"),
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected

def test_check_term_apply_basic():
    term = L3.Apply(
        target=L3.Immediate(value=0),
        arguments=[L3.Immediate(value=5)],
    )

    context: Context = {}

    expected = L2.Apply(
        target=L2.Immediate(value=0),
        arguments=[L2.Immediate(value=5)],
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected

def test_check_term_immediate_basic():
    term = L3.Immediate(
        value=10
    )

    context: Context = {}

    expected = L2.Immediate(
        value=10
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected

def test_check_term_primitive_basic():
    term = L3.Primitive(
        operator="-",
        left=L3.Immediate(value=0),
        right=L3.Immediate(value=2)
    )

    context: Context = {}

    expected = L2.Primitive(
        operator="-",
        left=L2.Immediate(value=0),
        right=L2.Immediate(value=2)
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected

def test_check_term_branch_basic():
    term = L3.Branch(
        operator="==",
        left=L3.Immediate(value=3),
        right=L3.Immediate(value=4),
        consequent=L3.Reference(name="hi"),
        otherwise=L3.Load(base=L3.Immediate(value=0), index=5),
    )

    context: Context = {}

    expected = L2.Branch(
        operator="==",
        left=L2.Immediate(value=3),
        right=L2.Immediate(value=4),
        consequent=L2.Reference(name="hi"),
        otherwise=L2.Load(base=L2.Immediate(value=0), index=5),
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected

def test_check_term_allocate_basic():
    term = L3.Allocate(
        count=5
    )

    context: Context = {}

    expected = L2.Allocate(
        count=5
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected

def test_check_term_load_basic():
    term = L3.Load(
        base=L3.Reference(name="x"),
        index=5
    )

    context: Context = {}

    expected = L2.Load(
        base=L2.Reference(name="x"),
        index=5
    )


    actual = eliminate_letrec_term(term, context)

    assert actual == expected

def test_check_term_store_basic():
    term = L3.Store(
        base=L3.Reference(name="x"),
        index=2,
        value=L3.Reference(name="y")
    )

    context: Context = {}

    expected = L2.Store(
        base=L2.Reference(name="x"),
        index=2,
        value=L2.Reference(name="y")
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected

def test_check_term_begin_basic():
    term = L3.Begin(
        effects=[L3.Reference(name="x"), L3.Reference(name="y")],
        value=L3.Immediate(value=5)
    )

    context: Context = {}

    expected = L2.Begin(
        effects=[L2.Reference(name="x"), L2.Reference(name="y")],
        value=L2.Immediate(value=5)
    )

    actual = eliminate_letrec_term(term, context)

    assert actual == expected
