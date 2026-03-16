from .syntax import Program
from .constant_propagation import constant_propagation_program
from .constant_folding import constant_folding_program
from .dead_code_elimination import dead_code_elimination_program


def optimize_program(
    program: Program,
) -> Program:
    # Create loop to continue optimizing as long as there was a change that occured
    while True:
        # Run constant propogation loop
        altered_program = constant_propagation_program(program)
        # Run constant folding loop
        altered_program = constant_folding_program(altered_program)
        # Run dead code elimination loop
        altered_program = dead_code_elimination_program(altered_program)

        if altered_program == program:
            break
        program = altered_program

    return program
