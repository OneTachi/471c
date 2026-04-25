from L1.close import close_term, close_program, free_variables
from L1 import syntax as L1
from L0 import syntax as L0
from util.sequential_name_generator import SequentialNameGenerator

def lift(term: L1.Statement) -> None:
    return None

def test_close_program_basic():
    term = L1.Halt(value="x")
    program = L1.Program(parameters=["arg"], body=term)
    
    fresh = SequentialNameGenerator()
    actual = close_program(program, fresh)
    expected = L0.Program(
        procedures=[L0.Procedure(
            name="l0",
            parameters=["arg"],
            body=L0.Halt(value="x")
            )
        ]
    )

    assert actual == expected

def test_fv_immediate():
    assert free_variables(L1.Halt(value="y")) == {"y"}
    assert free_variables(L1.Immediate(destination="x", value=10, then=L1.Halt(value="x"))) == set()

def test_fv_primitive():
    term = L1.Primitive(destination="res", operator="+", left="a", right="b", then=L1.Halt(value="res"))
    assert free_variables(term) == {"a", "b"}

def test_fv_branch():
    term = L1.Branch(left="a", right="b", operator="<", 
                     then=L1.Halt(value="a"), 
                     otherwise=L1.Halt(value="c"))
    assert free_variables(term) == {"a", "b", "c"}

def test_fv_memory():
    term_store = L1.Store(base="arr", index=0, value="v", then=L1.Halt(value="arr"))
    assert free_variables(term_store) == {"arr", "v"}
    
    term_load = L1.Load(destination="x", base="arr", index=0, then=L1.Halt(value="x"))
    assert free_variables(term_load) == {"arr"}

def test_fv_abstract_apply():
    body = L1.Primitive(destination="tmp", operator="+", left="x", right="y", then=L1.Halt(value="tmp"))
    term = L1.Abstract(destination="f", parameters=["x"], body=body, then=L1.Halt(value="f"))
    assert free_variables(term) == {"y"}

    assert free_variables(L1.Apply(target="f", arguments=["a", "b"])) == {"f", "a", "b"}

def test_fv_copy_allocate():
    assert free_variables(L1.Copy(destination="x", source="y", then=L1.Halt(value="x"))) == {"y"}
    assert free_variables(L1.Allocate(destination="x", count=10, then=L1.Halt(value="x"))) == set()

def test_fv_apply():
    assert free_variables(L1.Apply(target="a", arguments=["b"])) == {"a", "b"}
    assert free_variables(L1.Apply(target="f", arguments=[])) == {"f"}
    assert free_variables(L1.Apply(target="f", arguments=["f", "a"])) == {"f", "a"}

def test_halt_basic():
    term = L1.Halt(value="x")
    fresh = SequentialNameGenerator()
    actual = close_term(term, lift, fresh)

    expected = L0.Halt(value="x")

    assert actual == expected

def test_store_basic():
    term = L1.Store(value="a", index=2, base="a", then=L1.Halt(value="x"))
    fresh = SequentialNameGenerator()
    actual = close_term(term, lift, fresh)

    expected = L0.Store(value="a", index=2, base="a", then=L0.Halt(value="x"))

    assert actual == expected

def test_load_basic():
    term = L1.Load(destination="f", base="a", index=2, then=L1.Halt(value="x"))
    fresh = SequentialNameGenerator()
    actual = close_term(term, lift, fresh)

    expected = L0.Load(destination="f", base="a", index=2, then=L0.Halt(value="x"))

    assert actual == expected

def test_allocate_basic():
    term = L1.Allocate(destination="f", count=2, then=L1.Halt(value="x"))
    fresh = SequentialNameGenerator()
    actual = close_term(term, lift, fresh)

    expected = L0.Allocate(destination="f", count=2, then=L0.Halt(value="x"))

    assert actual == expected

def test_branch_basic():
    term = L1.Branch(operator="==", left="a", right="a", otherwise=L1.Halt(value="x"), then=L1.Halt(value="x"))
    fresh = SequentialNameGenerator()
    actual = close_term(term, lift, fresh)

    expected = L0.Branch(operator="==", left="a", right="a", otherwise=L0.Halt(value="x"), then=L0.Halt(value="x"))

    assert actual == expected

def test_abstract_basic():
    term = L1.Abstract(
        destination="f",
        parameters=["y"],
        body=L1.Primitive(
            destination="res",
            operator="+",
            left="x",
            right="y",
            then=L1.Halt(value="res")
        ),
        then=L1.Halt(value="x")
    ) 
    fresh = SequentialNameGenerator()
    actual = close_term(term, lift, fresh)
    expected = L0.Address(
        destination="t0",
        name="proc0",
        then=L0.Allocate(
            destination="env1",
            count=1,
            then=L0.Store(
                base="env1",
                index=0,
                value="x",
                then=L0.Allocate(
                    destination="f",
                    count=2,
                    then=L0.Store(
                        base="f",
                        index=0,
                        value="t0",
                        then=L0.Store(
                            base="f",
                            index=1,
                            value="env1",
                            then=L0.Halt(value="x")
                        )
                    )
                )
            )
        )
    )

    assert actual == expected

def test_apply_basic():
    term = L1.Apply(
        target="f",
        arguments=["arg_x"]
    ) 
    
    fresh = SequentialNameGenerator()
    actual = close_term(term, lift, fresh)

    expected = L0.Load(
        destination="t0",      
        base="f",              
        index=0,
        then=L0.Load(
            destination="env0", 
            base="f",           
            index=1,
            then=L0.Call(
                target="t0",
                arguments=["arg_x", "env0"] 
            )
        )
    )

    assert actual == expected

def test_immediate_basic():
    term = L1.Immediate(destination="f", value=2, then=L1.Halt(value="x"))
    fresh = SequentialNameGenerator()
    actual = close_term(term, lift, fresh)

    expected = L0.Immediate(destination="f", value=2, then=L0.Halt(value="x"))

    assert actual == expected

def test_copy_basic():
    term = L1.Copy(destination="f", source="a", then=L1.Halt(value="x"))
    fresh = SequentialNameGenerator()
    actual = close_term(term, lift, fresh)

    expected = L0.Copy(destination="f", source="a", then=L0.Halt(value="x"))

    assert actual == expected
