from L2.optimize import optimize_program
from L2.dead_code_elimination import (
    dead_code_elimination,
    get_free_variables,
)
from L2.constant_propagation import constant_propagation_term
from L2.constant_folding import constant_folding_term
from L2.syntax import (
    Abstract,
    Allocate,
    Apply,
    Begin,
    Branch,
    Immediate,
    Let,
    Load,
    Primitive,
    Reference,
    Store,
    Program,
)
rom collections.abc import Mapping

type ContextProp = Mapping[Identifier, Immediate]
type ContextFolding = Mapping[Identifier, Term]

def test_dead_branch_first():
    # (if (== 4 4) 3 1)
    term = Branch(
        operator="==", 
        left=Immediate(value=4), 
        right=Immediate(value=4), 
        consequent=Immediate(value=3), 
        otherwise=Immediate(value=1)
    )
    
    # The optimizer should return the live branch (consequent)
    expected = Immediate(value=3)
    
    actual = dead_code_elimination(term)
    
    assert actual == expected

def test_free_branch():
    term = Branch(operator="==", left=Immediate(value=4), right=Immediate(value=4), consequent=Immediate(value=3), otherwise=Immediate(value=1))
    result = set()

    assert get_free_variables(term) == result



def test_free_prim():
    term = Primitive(operator="+", left=Immediate(value=4), right=Immediate(value=4))
    result = set()

    assert get_free_variables(term) == result

def test_free_let_with_actual_free_var():
    # (let ((hi x)) y) -> Free variables are {"x", "y"}
    term = Let(
        bindings=[("hi", Reference(name="x"))], 
        body=Reference(name="y")
    )
    
    # The result is a set of strings
    expected = {"x", "y"}
    
    assert get_free_variables(term) == expected

def test_free_immed():
    term = Immediate(value=3)
    result = set()
    assert get_free_variables(term) == result


def test_folding_sub_goof():
    term = Primitive(operator="-",  left=Reference(name="1"), right=Reference(name="1"))
    result = Primitive(operator="-", left=Reference(name="1"), right=Reference(name="1"))
    context : ContextFolding = {}
    assert constant_folding_term(term, context) == result

def test_folding_mult_goof():
    term = Primitive(operator="*",  left=Reference(name="1"), right=Reference(name="1"))
    result = Primitive(operator="*", left=Reference(name="1"), right=Reference(name="1"))
    context : ContextFolding = {}
    assert constant_folding_term(term, context) == result


def test_folding_mult_swap():
    term = Primitive(operator="*",  left=Reference(name="1"), right=Immediate(value=5))
    result = Primitive(operator="*", left=Immediate(value=5), right=Reference(name="1"))
    context : ContextFolding = {}
    assert constant_folding_term(term, context) == result

def test_folding_mult_ones():
    term = Primitive(operator="*", left=Immediate(value=1), right=Immediate(value=2))
    result = Immediate(value=2)
    context : ContextFolding = {}
    assert constant_folding_term(term, context) == result
    
    term = Primitive(operator="*", left=Immediate(value=2), right=Immediate(value=1))
    result = Immediate(value=2)
    context : ContextFolding = {}
    assert constant_folding_term(term, context) == result

def test_folding_left_zero():
    term = Primitive(operator="*", left=Immediate(value=0), right=Immediate(value=2))
    result = Immediate(value=0)
    context : ContextFolding = {}
    assert constant_folding_term(term, context) == result

def test_folding_mult_norm():
    term = Primitive(operator="*", left=Immediate(value=2), right=Immediate(value=2))
    result = Immediate(value=4)
    context : ContextFolding = {}
    assert constant_folding_term(term, context) == result

def test_sub_normal():
    term = Primitive(operator="-", left=Immediate(value=2), right=Immediate(value=1))
    result = Immediate(value=1)
    context : ContextFolding = {}
    assert constant_folding_term(term, context) == result

def test_folding_sub_same():
    term = Primitive(operator="-", left=Immediate(value=1), right=Immediate(value=1))
    result = Immediate(value=0)
    context : ContextFolding = {}
    assert constant_folding_term(term, context) == result

def test_folding_last_case():
    term = Reference(name="x")
    result = Reference(name="x")
    context : ContextFolding = {}
    assert constant_folding_term(term, context) == result

def test_folding_ret_0():
    term = Primitive(operator="+", left=Immediate(value=0), right=Reference(name="x"))
    result = Reference(name="x")
    context : ContextFolding = {}

    assert constant_folding_term(term, context) == result

    term = Primitive(operator="+", left=Reference(name="x"), right=Immediate(value=0))
    assert constant_folding_term(term, context) == result

def test_propagation_begin():
    term = Begin(effects=[Immediate(value=3)], value=Immediate(value=1))
    result = Begin(effects=[Immediate(value=3)], value=Immediate(value=1))
    context : ContextProp = {}

    assert constant_propagation_term(term, context) == result



def test_propagation_shadowing_deletion():
    outer_context = {
        "x": Immediate(value=10)
    }

    term = Let(
        bindings=[
            ("x", Reference(name="y"))
        ],
        body=Reference(name="x")
    )

    result = constant_propagation_term(term, outer_context)

    assert isinstance(result, Let)
    
    assert result.bindings[0][1] == Reference(name="y")
    
    assert result.body == Reference(name="x")
    assert not isinstance(result.body, Immediate)

def test_deep_integration():
    program = Program(
        parameters=["p"],
        body=Let(
            bindings=[("x", Immediate(value=10))],
            body=Begin(
                effects=[
                    Branch(
                        operator="==",
                        left=Reference(name="x"),
                        right=Immediate(value=10),
                        consequent=Store(
                            base=Reference(name="p"), 
                            index=0, 
                            value=Immediate(value=1)
                        ),
                        otherwise=Immediate(value=0)
                    )
                ],
                value=Reference(name="x")
            )
        )
    )
    
    actual = optimize_program(program)
    
    assert isinstance(actual.body, Begin)
    assert isinstance(actual.body.effects[0], Store)
    assert actual.body.value == Immediate(value=10)

def test_dce_branch_equality_true():
    program = Program(
        parameters=[],
        body=Branch(
            operator="==",
            left=Immediate(value=5),
            right=Immediate(value=5),
            consequent=Immediate(value=1),
            otherwise=Reference(name="unreachable")
        )
    )
    # Should result in just Immediate(1). 'unreachable' is never seen.
    assert optimize_program(program).body == Immediate(value=1)

def test_dce_branch_less_than_false():
    program = Program(
        parameters=[],
        body=Branch(
            operator="<",
            left=Immediate(value=10),
            right=Immediate(value=5),
            consequent=Reference(name="unreachable"),
            otherwise=Immediate(value=0)
        )
    )
    # Should result in just Immediate(0).
    assert optimize_program(program).body == Immediate(value=0)

def test_purity_begin_recursive():
    # Unused Let with pure Begin body -> Deleted
    p1 = Program(
        parameters=[],
        body=Let(
            bindings=[("unused", Begin(effects=[Immediate(value=1)], value=Immediate(value=2)))],
            body=Immediate(value=0)
        )
    )
    assert optimize_program(p1).body == Immediate(value=0)

    p2 = Program(
        parameters=["p"],
        body=Let(
            bindings=[
                (
                    "unused", 
                    Begin(
                        effects=[
                            Store(
                                base=Reference(name="p"), 
                                index=0, 
                                value=Immediate(value=1)
                            )
                        ], 
                        value=Immediate(value=2)
                    )
                )
            ],
            body=Immediate(value=0)
        )
    )
    actual_body = optimize_program(p2).body
    assert isinstance(actual_body, Let)
    binding_names = [b[0] for b in actual_body.bindings]
    assert "unused" in binding_names


def test_optimize_program():
    program = Program(
        parameters=[],
        body=Primitive(
            operator="+",
            left=Immediate(value=1),
            right=Immediate(value=1),
        ),
    )

    expected = Program(
        parameters=[],
        body=Immediate(value=2),
    )

    actual = optimize_program(program)

    assert actual == expected

def test_optimize_arithmetic():
    program = Program(
        parameters=["x"],
        body=Primitive(
            operator="+",
            left=Primitive(operator="+", left=Reference(name="x"), right=Immediate(value=5)),
            right=Immediate(value=10)
        )
    )
    expected_body = Primitive(operator="+", left=Immediate(value=15), right=Reference(name="x"))
    assert optimize_program(program).body == expected_body

def test_arithmetic_identities():
    program = Program(
        parameters=["x"],
        body=Begin(
            effects=[
                Primitive(operator="*", left=Reference(name="x"), right=Immediate(value=0)),
                Primitive(operator="*", left=Immediate(value=1), right=Reference(name="x")),
                Primitive(operator="-", left=Reference(name="x"), right=Reference(name="x")),
            ],
            value=Primitive(operator="-", left=Reference(name="x"), right=Immediate(value=0))
        )
    )
    assert optimize_program(program).body == Reference(name="x")

def test_branch_folding_true():
    program = Program(
        parameters=[],
        body=Branch(
            operator="==",
            left=Immediate(value=10),
            right=Immediate(value=10),
            consequent=Immediate(value=1),
            otherwise=Immediate(value=0)
        )
    )
    assert optimize_program(program).body == Immediate(value=1)

def test_branch_folding_false():
    program = Program(
        parameters=[],
        body=Branch(
            operator="<",
            left=Immediate(value=10),
            right=Immediate(value=5),
            consequent=Immediate(value=1),
            otherwise=Immediate(value=0)
        )
    )
    assert optimize_program(program).body == Immediate(value=0)

def test_propagation_and_shadowing():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[("x", Immediate(value=100))],
            body=Abstract(
                parameters=["x"],
                body=Reference(name="x")
            )
        )
    )
    actual = optimize_program(program)
    assert actual.body == Abstract(parameters=["x"], body=Reference(name="x"))

def test_nested_propagation():
    program = Program(
        parameters=[],
        body=Let(
            bindings=[
                ("x", Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=1))),
                ("y", Reference(name="x"))
            ],
            body=Reference(name="y")
        )
    )
    assert optimize_program(program).body == Immediate(value=2)

def test_dce_impure_preservation():
    program = Program(
        parameters=["ptr"],
        body=Let(
            bindings=[
                ("unused_pure", Primitive(operator="+", left=Immediate(value=1), right=Immediate(value=2))),
                ("unused_impure", Allocate(count=10)),
                ("used", Load(base=Reference(name="ptr"), index=0))
            ],
            body=Reference(name="used")
        )
    )
    actual_body = optimize_program(program).body
    assert isinstance(actual_body, Let)
    binding_names = [b[0] for b in actual_body.bindings]
    assert "unused_pure" not in binding_names
    assert "unused_impure" in binding_names

def test_complex_structures():
    program = Program(
        parameters=["f", "p"],
        body=Begin(
            effects=[
                Store(base=Reference(name="p"), index=1, value=Immediate(value=99)),
                Apply(target=Reference(name="f"), arguments=[Immediate(value=1), Reference(name="p")])
            ],
            value=Load(base=Reference(name="p"), index=1)
        )
    )
    actual = optimize_program(program)
    assert actual == program

def test_dead_branch_recursion():
    program = Program(
        parameters=[],
        body=Branch(
            operator="==",
            left=Immediate(value=1),
            right=Immediate(value=1),
            consequent=Primitive(operator="+", left=Immediate(value=10), right=Immediate(value=10)),
            otherwise=Reference(name="dead_path")
        )
    )
    assert optimize_program(program).body == Immediate(value=20)

def test_free_vars_complex_scoping():
    program = Program(
        parameters=["y", "z", "f"],
        body=Let(
            bindings=[("x", Reference(name="y"))],
            body=Apply(
                target=Reference(name="f"),
                arguments=[Reference(name="x"), Reference(name="z")]
            )
        )
    )
    assert optimize_program(program) == program

def test_free_vars_branch_and_begin():
    program = Program(
        parameters=["a", "b", "c", "d", "e"],
        body=Begin(
            effects=[
                Branch(
                    operator="==",
                    left=Reference(name="a"),
                    right=Reference(name="b"),
                    consequent=Reference(name="c"),
                    otherwise=Reference(name="d")
                )
            ],
            value=Reference(name="e")
        )
    )
    # No constants to fold, so it should return unchanged.
    assert optimize_program(program) == program

def test_free_vars_store_and_immediate():
    program = Program(
        parameters=["p", "v"],
        body=Begin(
            effects=[Store(base=Reference(name="p"), index=0, value=Reference(name="v"))],
            value=Immediate(value=42)
        )
    )
    assert optimize_program(program) == program
