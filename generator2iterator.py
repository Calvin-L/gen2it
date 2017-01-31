#!/usr/bin/env python3

import sys
from collections import namedtuple

# expressions
EVal = namedtuple("EVal", ["val"])
EVar = namedtuple("EVar", ["id"])
EAssign = namedtuple("EAssign", ["lval", "rval"])
ECall = namedtuple("ECall", ["f", "args"])
EEq = namedtuple("EEq", ["e1", "e2"])
ELt = namedtuple("ELt", ["e1", "e2"])
EPlus = namedtuple("EPlus", ["e1", "e2"])

# statements
SNop = namedtuple("SNop", [])
SReturn = namedtuple("SReturn", ["e"])
SExp = namedtuple("SExp", ["e"])
SSeq = namedtuple("SSeq", ["stms"])
SYield = namedtuple("SYield", ["e"])
SWhile = namedtuple("SWhile", ["cond", "body"])
SIf    = namedtuple("SIf", ["cond", "then_branch", "else_branch"])
SSwitch = namedtuple("SSwitch", ["e", "cases"])

ast = SSeq([
    SExp(EAssign(EVar("x"), EVal(0))),
    SIf(EVal(True),
        SYield(EVal(1)),
        SNop()),
    SWhile(ELt(EVar("x"), EVal(10)),
        SSeq([
            SYield(EVar("x")),
            SExp(EAssign(EVar("x"), EPlus(EVar("x"), EVal(1))))]))])

_i = 0
_yield_ids = { }
def number_yields(s):
    global _i
    if isinstance(s, SNop) or isinstance(s, SExp):
        return
    elif isinstance(s, SYield):
        _i += 1
        _yield_ids[id(s)] = _i
    elif isinstance(s, SSeq):
        for ss in s.stms:
            number_yields(ss)
    elif isinstance(s, SIf):
        number_yields(s.then_branch)
        number_yields(s.else_branch)
    elif isinstance(s, SWhile):
        number_yields(s.body)
    else:
        raise NotImplementedError(s)

# vars for the iterator
_hn   = EVar("_has_next")
_next = EVar("_next")
_state = EVar("_state")

def run_to_first_yield(s):
    if isinstance(s, SNop) or isinstance(s, SExp):
        return (s, False)
    elif isinstance(s, SYield):
        return (SSeq([
                SExp(EAssign(_hn,   EVal(True))),
                SExp(EAssign(_next, s.e)),
                SExp(EAssign(_state, EVal(_yield_ids[id(s)]))),
                SReturn(None)]),
            True)
    elif isinstance(s, SSeq):
        stms = []
        ret = False
        for i in range(len(s.stms)):
            stm, ret = run_to_first_yield(s.stms[i])
            stms.append(stm)
            if ret:
                break
        return (SSeq(stms), ret)
    elif isinstance(s, SIf):
        s1, r1 = run_to_first_yield(s.then_branch)
        s2, r2 = run_to_first_yield(s.else_branch)
        return (SIf(s.cond, s1, s2), r1 and r2)
    elif isinstance(s, SWhile):
        body, ret = run_to_first_yield(s.body)
        return (SWhile(s.cond, body), False)
    else:
        raise NotImplementedError(s)

def enumerate_conts(s):
    if isinstance(s, SNop) or isinstance(s, SExp):
        return
    elif isinstance(s, SSeq):
        for i in range(len(s.stms)):
            for (e, k) in enumerate_conts(s.stms[i]):
                yield (e, SSeq([k] + s.stms[i+1:]))
    elif isinstance(s, SYield):
        yield (_yield_ids[id(s)], SNop())
    elif isinstance(s, SWhile):
        for (e, k) in enumerate_conts(s.body):
            yield (e, SSeq([k, s]))
    elif isinstance(s, SIf):
        yield from enumerate_conts(s.then_branch)
        yield from enumerate_conts(s.else_branch)
    else:
        raise NotImplementedError(s)

def pprint(x, out, indent=""):
    if isinstance(x, SNop):
        return
    elif isinstance(x, SExp):
        out(indent)
        pprint(x.e, out)
        out("\n")
    elif isinstance(x, SSeq):
        for s in x.stms:
            pprint(s, out, indent)
    elif isinstance(x, SYield):
        out(indent)
        out("yield ")
        pprint(x.e, out)
        out("\n")
    elif isinstance(x, SReturn):
        out(indent)
        out("return")
        if x.e:
            out(" ")
            pprint(x.e, out)
        out("\n")
    elif isinstance(x, SIf):
        out(indent)
        out("if ")
        pprint(x.cond, out)
        out(":\n")
        pprint(x.then_branch, out, indent="  "+indent)
        out(indent)
        out("else:\n")
        pprint(x.else_branch, out, indent="  "+indent)
    elif isinstance(x, SSwitch):
        out(indent)
        out("switch ")
        pprint(x.e, out)
        out(":\n")
        indent += "  "
        for val, case in x.cases:
            out(indent)
            out("case ")
            pprint(val, out)
            out(":\n")
            pprint(case, out, indent="  " + indent)
    elif isinstance(x, SWhile):
        out(indent)
        out("while ")
        pprint(x.cond, out)
        out(":\n")
        pprint(x.body, out, indent="  "+indent)
    elif isinstance(x, EAssign):
        pprint(x.lval, out)
        out(" = ")
        pprint(x.rval, out)
    elif isinstance(x, ELt):
        pprint(x.e1, out)
        out(" < ")
        pprint(x.e2, out)
    elif isinstance(x, EEq):
        pprint(x.e1, out)
        out(" == ")
        pprint(x.e2, out)
    elif isinstance(x, EPlus):
        pprint(x.e1, out)
        out(" + ")
        pprint(x.e2, out)
    elif isinstance(x, EVar):
        out(x.id)
    elif isinstance(x, EVal):
        out(str(x.val))
    elif isinstance(x, ECall):
        out(x.f)
        out("(")
        for i in range(len(x.args)):
            if i > 0:
                out(", ")
            pprint(x.args[i], out)
        out(")")
    else:
        raise NotImplementedError(x)

number_yields(ast)

# pprint(ast, sys.stdout.write)
# pprint(run_to_first_yield(ast)[0], sys.stdout.write)
# pprint(list(enumerate_conts(ast)))

advance = SSeq([
    SExp(EAssign(_hn, EVal(False))),
    SExp(EAssign(_next, EVal(None))),
    SSwitch(_state,
        cases=[(EVal(0), run_to_first_yield(ast)[0])] +
        [(EVal(n), run_to_first_yield(k)[0]) for (n, k) in enumerate_conts(ast)])])

_tmpnext = EVar("_tmpnext")
getNext = SSeq([
    SExp(EAssign(_tmpnext, _next)),
    SExp(ECall("advance", [])),
    SReturn(_tmpnext)])

print("class Iterator:")
print("  init():")
print("    " + _hn.id + " = False")
print("    " + _next.id + " = None")
print("    " + _state.id + " = 0")
print("    advance()")

print("  advance():")
pprint(advance, sys.stdout.write, indent="    ")

print("  hasNext():")
pprint(SReturn(_hn), sys.stdout.write, indent="    ")

print("  next():")
pprint(getNext, sys.stdout.write, indent="    ")

"""

init():
    _hn = false
    _next = null
    _state = 0
    advance()
hasNext():
    return _hn
next():
    res = _next
    advance()
    return res
advance():
    s, e = runToNextYieldFromState(_state)
    run s
    if e:
        _next = e
    else:
        _next = null
        _hn = false

"""


