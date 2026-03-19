from L3.syntax import Apply, Immediate, Let, Reference, Allocate, Load, Store, LetRec, Abstract, Primitive, Branch, Begin
from L3.uniqify import Context, uniqify_term
from util.sequential_name_generator import SequentialNameGenerator


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
