import pytest
from L3.check import Context, check_program, check_term
from L3.check import Context, check_term
from L3.syntax import (
    Reference,
    Abstract, 
    Allocate,
    Apply,
    Begin,
    Branch, 
    Immediate, 
    Let,
    LetRec,
    Load,
    Primitive,
    Program,
    Reference,
    Store,
)

def test_check_reference_bound():
    term = Reference(name="x")

    context: Context = {
        "x": None,
    }

    check_term(term, context)


def test_check_reference_free():
    term = Reference(name="x")

    context: Context = {}

    with pytest.raises(ValueError):
        check_term(term, context)

def test_check_term_let():
    term = Let(
            bindings= [
                ("x", Immediate(value=0)),
                ("y", Immediate(value=1))
            ],
            body=Reference(name="x"),
    )
    
    # Remember that context in this case is the context for this term. Aka any arguments already stated before this term
    # In other words, declared variables before this variable
    context = Context = {
        "y" : None,
    }

    check_term(term, context)

def test_check_let_not_bound():
    term = Let(
        bindings = [
            ("x", Immediate(value=0)),
            ("y", Reference(name="x"))
        ],
        body=Reference(name="y")
    )

    context = Context = {}
    with pytest.raises(ValueError):
        check_term(term, context)

def test_check_let_duped():
    term = Let(
        bindings = [
            ("x", Immediate(value=0)),
            ("x", Immediate(value=1))
        ],
        body=Reference(name="x")
    )

    context = Context = {
        "x" : None,
    }

    with pytest.raises(ValueError):
        check_term(term, context)

def test_check_letrec_duped():
    term = LetRec(
        bindings = [
            ("x", Immediate(value=0)),
            ("x", Immediate(value=1))
        ],
        body=Reference(name="x")
    )

    context = Context = {}

    with pytest.raises(ValueError):
        check_term(term, context)

def test_check_letrec_binding_exists():
    term = LetRec(
        bindings = [
            ("x", Immediate(value=0)),
            ("y", Reference(name="x"))
        ],
        body=Reference(name="y")
    )

    context = Context = {}
    check_term(term, context)

def test_check_abstract_duped():
    term = Abstract(
        parameters = [
            "x", 
            "x"
        ],
        body=Immediate(value=0)
    )

    context : Context = {}
    with pytest.raises(ValueError):
        check_term(term, context)

def test_check_abstract_bound():
    term = Abstract(
        parameters = [
            "x", 
            "y"
        ],
        body=Immediate(value=0)
    )

    context : Context = {}
    check_term(term, context)

def test_check_apply_args_invalid():
    term = Apply(
        target = Reference(name="x"),
        arguments = [
            Immediate(value=0),
            Reference(name="y")
        ],
    )

    context : Context = {
        "x" : None,
    }
    with pytest.raises(ValueError):
        check_term(term, context)

def test_check_apply_bound():
    term = Apply(
        target = Reference(name="x"),
        arguments = [
            Immediate(value=0),
        ]
    )

    context : Context = {
        "x" : None,
    }
    check_term(term, context)

def test_check_apply_target_invalid():
    term = Apply(
        target = Reference(name="x"),
        arguments = [
            Immediate(value=0),
        ],
    )

    context : Context = {}
    with pytest.raises(ValueError):
        check_term(term, context)

def test_check_immediate_pass():
    term = Immediate(
        value=0    
    )

    context : Context = {}
    check_term(term, context)

def test_check_primitive_pass():
    term = Primitive(
        operator="+",
        left=Immediate(value=0),
        right=Immediate(value=1)
    )

    context : Context = {}
    check_term(term, context)

def test_check_primitive_left_fail():
    term = Primitive(
        operator="+",
        left=Reference(name="x"),
        right=Immediate(value=1)
    )

    context : Context = {}
    with pytest.raises(ValueError):
        check_term(term, context)

def test_check_branch_pass():
    term = Branch(
        left=Immediate(value=0),
        right=Immediate(value=1),
        consequent=Immediate(value=2),
        otherwise=Immediate(value=3)
    )

    context : Context = {
        "z" : None
    }
    check_term(term, context)

def test_check_branch_one_invalid():
    term = Branch(
        left=Reference(name="z"),
        right=Reference(name="x"),
        consequent=Immediate(value=2),
        otherwise=Immediate(value=3)
    )

    context : Context = {
        "z" : None
    }
    with pytest.raises(ValueError):
        check_term(term, context)

def test_check_allocate_pass():
    term = Allocate(
        count=1,
    )

    context : Context = {
        "z" : None
    }
    check_term(term, context)

def test_check_load_pass_z():
    term = Load(
        base=Reference(name="z"),
        index=1,
    )

    context : Context = {
        "z" : None
    }
    check_term(term, context)

def test_check_store_value_invalid():
    term = Store(
        base=Reference(name="z"),
        value=Reference(name="c"),
        index=1,
    )

    context : Context = {
        "z" : None
    }
    with pytest.raises(ValueError):
        check_term(term, context)


