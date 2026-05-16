from collections.abc import Mapping, Sequence
from typing import Annotated, Literal

from pydantic import BaseModel, Field

type Identifier = Annotated[str, Field(min_length=1)]
type Nat = Annotated[int, Field(ge=0)]


# Write if too that will go into branch, remember if its just a variable i gotta make that branch/manufacture
# otherwise no point in boolean
class Overload(BaseModel, frozen=True):
    tag: Literal["overload"] = "overload"
    options: Sequence[Arrow]


type Type = Annotated[
    Boolean | Int | Tuple | Record | Symbol | Arrow | Overload,
    Field(discriminator="tag"),
]


## Type Declarations
class Boolean(BaseModel, frozen=True):
    tag: Literal["boolean"] = "boolean"


class Int(BaseModel, frozen=True):
    tag: Literal["int"] = "int"


class Tuple(BaseModel, frozen=True):
    tag: Literal["tuple"] = "tuple"
    values: Sequence[Type]


class Record(BaseModel, frozen=True):
    tag: Literal["record"] = "record"
    fields: Mapping[Identifier, Type]


class Symbol(BaseModel, frozen=True):
    tag: Literal["symbol"] = "symbol"


class Arrow(BaseModel, frozen=True):
    tag: Literal["arrow"] = "arrow"
    params: Sequence[Type]
    ret: Type


##


class Program(BaseModel, frozen=True):
    tag: Literal["l4"] = "l4"
    parameters: Sequence[tuple[Identifier, Type]]
    ret: Type
    body: Term


type Term = Annotated[
    If
    | MakeBool
    | MakeSymbol
    | MakeTuple
    | GetTupleValue
    | MakeRecord
    | GetRecordValue
    | Let
    | Reference
    | Abstract
    | Apply
    | Immediate
    | Primitive
    | Branch
    | Allocate
    | Load
    | Store
    | Begin
    | LetRec,
    Field(discriminator="tag"),
]


class If(BaseModel, frozen=True):
    tag: Literal["if"] = "if"
    condition: Term
    consequent: Term
    otherwise: Term


class MakeBool(BaseModel, frozen=True):
    tag: Literal["bool"] = "bool"
    value: bool


class MakeTuple(BaseModel, frozen=True):
    tag: Literal["tuple"] = "tuple"
    values: Sequence[Term]


class MakeSymbol(BaseModel, frozen=True):
    tag: Literal["symbol"] = "symbol"
    name: Identifier


class GetTupleValue(BaseModel, frozen=True):
    tag: Literal["gettuplevalue"] = "gettuplevalue"
    term: Term
    index: Nat


class MakeRecord(BaseModel, frozen=True):
    tag: Literal["record"] = "record"
    fields: Sequence[tuple[Identifier, Term]]


class GetRecordValue(BaseModel, frozen=True):
    tag: Literal["getrecordvalue"] = "getrecordvalue"
    record: Term
    key: Identifier


class Let(BaseModel, frozen=True):
    tag: Literal["let"] = "let"
    bindings: Sequence[tuple[Identifier, Term]]
    body: Term


class LetRec(BaseModel, frozen=True):
    tag: Literal["letrec"] = "letrec"
    bindings: Sequence[tuple[Identifier, Type, Term]]
    body: Term


class Reference(BaseModel, frozen=True):
    tag: Literal["reference"] = "reference"
    name: Identifier


class Abstract(BaseModel, frozen=True):
    tag: Literal["abstract"] = "abstract"
    parameters: Sequence[tuple[Identifier, Type]]
    body: Term
    ret: Type


class Apply(BaseModel, frozen=True):
    tag: Literal["apply"] = "apply"
    target: Term
    arguments: Sequence[Term]


class Immediate(BaseModel, frozen=True):
    tag: Literal["immediate"] = "immediate"
    value: int


class Primitive(BaseModel, frozen=True):
    tag: Literal["primitive"] = "primitive"
    operator: Literal["+", "-", "*"]
    left: Term
    right: Term


class Branch(BaseModel, frozen=True):
    tag: Literal["branch"] = "branch"
    operator: Literal["<", "=="]
    left: Term
    right: Term
    consequent: Term
    otherwise: Term


class Allocate(BaseModel, frozen=True):
    tag: Literal["allocate"] = "allocate"
    count: Nat


class Load(BaseModel, frozen=True):
    tag: Literal["load"] = "load"
    base: Term
    index: Nat


class Store(BaseModel, frozen=True):
    tag: Literal["store"] = "store"
    base: Term
    index: Nat
    value: Term


class Begin(BaseModel, frozen=True):
    tag: Literal["begin"] = "begin"
    effects: Sequence[Term]
    value: Term
