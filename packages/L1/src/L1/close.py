from L1 import syntax as L1
from L0 import syntax as L0
from collections.abc import Callable
from functools import partial

def free_variables(term: L1.Statement):
    match term:
        case L1.Immediate(destination=destination, value=_value, then=then):
            return free_variables(then) - {destination}
        case L1.Primitive(destination=destination, operator=_operator, left=left, right=right, then=then):
            return {left, right} | (free_variables(then) - {destination})
        case L1.Branch(left=left, right=right, then=then, otherwise=otherwise, operator=_o):
            return {left, right} | free_variables(otherwise) | free_variables(then)
        case L1.Allocate(destination=destination, count=_count, then=then):
            return free_variables(then) - {destination}
        case L1.Store(base=base, index=_i, value=value, then=then):
            return {base, value} | free_variables(then)
        case L1.Load(destination=d, base=b, index=_i, then=t):
            return {b} | (free_variables(t) - {d})
        case L1.Halt(value=v):
            return {v}
        case L1.Copy(destination=d, source=s, then=t):
            return {s} | (free_variables(t) - {d})
        case L1.Abstract(destination=d, parameters=p, body=b, then=t):
            body_set = free_variables(b) - set(p)
            return body_set | (free_variables(t) - {d})
        case L1.Apply(target=t, arguments=a): # pragma: no branch
            # This is tested, but shows up yellow for some reason.
            return {t} | set(a)


def close_term(statement: L1.Statement, lift: Callable[[any], None], fresh: Callable[[str], str]):
    recur = partial(close_term, lift=lift, fresh=fresh)

    match statement:
        case L1.Abstract(destination=destination, parameters=parameters, body=body, then=then):
            name = fresh("proc")
            env_p = fresh("env")

            fvs = list(free_variables(body) - set(parameters))

            result = recur(body)

            for i, fv in enumerate(fvs):
                result = L0.Load(destination=fv, base=env_p, index=i, then=result)

            lift(L0.Procedure(name=name, parameters=[*parameters, env_p], body=result))

            env = fresh("env") # The chunk of memory for storing environment variables
            code = fresh("t")
            
            # Recursively returns store and finally just the last continuation
            def recur_store_vars(index: int, final_continuation: L0.Statement):
                if index >= len(fvs):
                    return final_continuation
                # Note that base indicates the start of memory and index is where we store it in it!
                return L0.Store(base=env, index=index, value=fvs[index], then=recur_store_vars(index+1, final_continuation))
            
            code_alloc = L0.Allocate(
              destination=destination,
              count=2,
              then=L0.Store(
                base=destination,
                index=0,
                value=code,
                then=L0.Store(
                  base=destination,
                  index=1,
                  # Putting env here which is also a chunk of memory, think of env[0] = X, env[1] = Y, so we have to write this o    ut consecutively.... we looping
                  value=env,
                  then=recur(then), # Rest of program, but make sure if it's alloc/apply, it's handled
                  )
                )
             )

            # Allocate memory for environment vars & then store all variables recursively
            env_alloc = L0.Allocate(
                destination=env,
                count=len(fvs),
                then=recur_store_vars(0, code_alloc)
            ) 
            
            # Return the new location of the memory with it's name, then allocate our variables!
            return L0.Address(destination=code, name=name, then=env_alloc)
            
        case L1.Apply(target=target, arguments=arguments):
            env = fresh("env") # The chunk of memory for storing environment variables
            code = fresh("t") # The code 

            return L0.Load(
                destination=code,
                base=target,
                index=0,
                then=L0.Load(
                    destination=env,
                    base=target,
                    index=1,
                    then=L0.Call(
                        target=code,
                        arguments=[*arguments, env]
                    )
                )
            )
        case L1.Immediate(destination=d, value=v, then=t):
            return L0.Immediate(destination=d, value=v, then=recur(t))

        case L1.Copy(destination=d, source=s, then=t):
            return L0.Copy(destination=d, source=s, then=recur(t))

        case L1.Primitive(destination=d, operator=o, left=l, right=r, then=t):
            return L0.Primitive(destination=d, operator=o, left=l, right=r, then=recur(t))

        case L1.Branch(operator=o, left=l, right=r, then=t, otherwise=oth):
            return L0.Branch(operator=o, left=l, right=r, then=recur(t), otherwise=recur(oth))

        case L1.Allocate(destination=d, count=c, then=t):
            return L0.Allocate(destination=d, count=c, then=recur(t))

        case L1.Load(destination=d, base=b, index=i, then=t):
            return L0.Load(destination=d, base=b, index=i, then=recur(t))

        case L1.Store(base=b, index=i, value=v, then=t):
            return L0.Store(base=b, index=i, value=v, then=recur(t))

        case L1.Halt(value=v): # pragma: no branch
            return L0.Halt(value=v)
            



def close_program(program, fresh):
    match program:
        case L1.Program(parameters=parameters, body=body): # pragma: no branch
            procedures = list[L0.Procedure]()
            body = close_term(body, procedures.append, fresh)
            return L0.Program(procedures=[
                *procedures,
                L0.Procedure(
                    name="l0", parameters=parameters, 
                    body=body
                )
            ])
