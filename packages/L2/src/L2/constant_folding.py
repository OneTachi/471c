
# As of right now, only needs to do branch and primitive folding! 
def constant_folding_term(term: Term, context: Context) -> Term:
    recur = partial(constant_folding_term, context=context)

    match term:
        case Branch(operator=_operator, left=left, right=right, consequent=consequent, otherwise=otherwise):
            pass
        case Primitive(operator=_operator, left=left, right=right):
            match operator: 
                case "+":
                    match recur(left), recur(right):
                        case Immediate(value=i1), Immediate(value=i2):
                            return Immediate(value=i1+i2)

                        case Immediate(value=0), right:
                            return right

                        case left, Immediate(value=0):
                            return left
                        # We are trying to keep all Immediates to the left as our processing rules
                        case [
                            Primitive(operator="+", left=Immediate(value=i1), right=right), 
                            Primitive(operator="+", left=Immediate(value=i2), right=right)
                        ]:
                            return (Primitive( 
                                operator="+",
                                left=Immediate(value=i1 + i2),
                                right=Primitive(
                                    operator="+",
                                    left=left,
                                    right=right,
                                ),
                            ))
                        
                        case left, Immediate() as right:
                            return Primitive(operator="+", left=right, right=left)

                case "-":
                case "*":


