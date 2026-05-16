import pytest
from L4.boil_types import boil_types, boil_program, infer_term, infer_program
from collections.abc import Mapping
from L4 import syntax as L4


type Context = Mapping[L4.Identifier, L4.Type]

def test_infer_term_makebool():
    term = L4.MakeBool(value=False)
    context : Context = {}
    expected = L4.Boolean()
    actual = infer_term(term, context)

    assert actual == expected


