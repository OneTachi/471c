from L3.syntax import Apply, Immediate, Let, Reference, Allocate, Load, Store, LetRec, Abstract, Primitive, Branch, Begin, Program
from L3.uniqify import Context, uniqify_term, uniqify_program
from util.sequential_name_generator import SequentialNameGenerator

def test_uniqify_program():
    program = Program(
        parameters=["x"],
        body=Immediate(value=5)
    )
    
    fresh, actual = uniqify_program(program)
    expected = Program(
        parameters=["x0"],
        body=Immediate(value=5)
    )

    assert actual == expected

def test_uniqify_term_begin():
    term = Begin(
        effects=[Reference(name="t")],
        value=Reference(name="x")
    )

    context: Context = {"x": "z", "t": "bh"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh=fresh)

    expected = Begin(
        effects=[Reference(name="bh")],
        value=Reference(name="z")
    )

    assert actual == expected

def test_uniqify_term_branch():
    term = Branch(operator="==", left=Reference(name="x"), right=Reference(name="t"), consequent=Reference(name="t"), otherwise=Reference(name="t"))

    context: Context = {"x": "z", "t": "bh"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh=fresh)

    expected = Branch(operator="==", left=Reference(name="z"), right=Reference(name="bh"), consequent=Reference(name="bh"), otherwise=Reference(name="bh"))

    assert actual == expected

def test_uniqify_term_primitive():
    term = Primitive(operator="-", left=Reference(name="x"), right=Reference(name="t"))

    context: Context = {"x": "z", "t": "bh"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh=fresh)

    expected = Primitive(operator="-", left=Reference(name="z"), right=Reference(name="bh"))

    assert actual == expected


def test_uniqify_term_abstract():
    term = Abstract(
        parameters=["x", "y", "z"],
        body=Reference(name="x")
    )

    context: Context = {"y": "yoohoo!"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = Abstract(
        parameters=["x0", "y0", "z0"],
        body=Reference(name="x0")
    )

    assert actual == expected

def test_uniqify_term_letrec():
    term = LetRec(
        bindings=[
            ("x", Immediate(value=1)),
            ("y", Reference(name="x")),
            ("z", Reference(name="y"))
        ],
        body=Apply(
            target=Reference(name="x"),
            arguments=[
                Reference(name="y"),
            ],
        ),
    )

    context: Context = {"x": "y"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = LetRec(
        bindings=[
            ("x0", Immediate(value=1)),
            ("y0", Reference(name="x0")),
            ("z0", Reference(name="y0"))
        ],
        body=Apply(
            target=Reference(name="x0"),
            arguments=[
                Reference(name="y0"),
            ],
        ),
    )
    
    assert actual == expected

def test_uniqify_term_reference():
    term = Reference(name="x")

    context: Context = {"x": "y"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh=fresh)

    expected = Reference(name="y")

    assert actual == expected


def test_uniqify_immediate():
    term = Immediate(value=42)

    context: Context = dict[str, str]()
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = Immediate(value=42)

    assert actual == expected


def test_uniqify_term_let():
    term = Let(
        bindings=[
            ("x", Immediate(value=1)),
            ("y", Reference(name="x")),
        ],
        body=Apply(
            target=Reference(name="x"),
            arguments=[
                Reference(name="y"),
            ],
        ),
    )

    context: Context = {"x": "y"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh)

    expected = Let(
        bindings=[
            ("x0", Immediate(value=1)),
            ("y0", Reference(name="y")),
        ],
        body=Apply(
            target=Reference(name="x0"),
            arguments=[
                Reference(name="y0"),
            ],
        ),
    )

    assert actual == expected

def test_uniqify_term_allocate():
    term = Allocate(count=5)

    context: Context = {"x": "y"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh=fresh)

    expected = Allocate(count=5)

    assert actual == expected

def test_uniqify_term_load():
    term = Load(base=Reference(name="x"), index=5)

    context: Context = {"x": "z"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh=fresh)

    expected = Load(base=Reference(name="z"), index=5)

    assert actual == expected

def test_uniqify_term_store():
    term = Store(base=Reference(name="x"), index=5, value=Reference(name="t"))

    context: Context = {"x": "z", "t": "bh"}
    fresh = SequentialNameGenerator()
    actual = uniqify_term(term, context, fresh=fresh)

    expected = Store(base=Reference(name="z"), index=5, value=Reference(name="bh"))

    assert actual == expected

