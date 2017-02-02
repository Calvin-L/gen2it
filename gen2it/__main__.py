import argparse
import sys
from collections import namedtuple

from plyj.parser import Parser as JavaParser
from plyj.model import *

from .prettyprint import dump

args = argparse.ArgumentParser(description="Generator to iterator converter.")
args.add_argument("-o", metavar="FILE", default=None, help="Output file")
args.add_argument("file", nargs="?", default=None, help="Input file (omit to use stdin)")
args = args.parse_args()

class Rewriter(object):
    def visit(self, x):
        if isinstance(x, list):
            return [self.visit(elem) for elem in x]
        elif isinstance(x, SourceElement):
            return type(x)(*[self.visit(getattr(x, f)) for f in x._fields])
        else:
            return x

_name = 0
def fresh_name():
    global _name
    _name += 1
    return "_name{}".format(_name)

def extract_declarations(stm, out, rename=None):
    class R(Rewriter):
        def __init__(self):
            super().__init__()
            self.scopes = [{}]
            self.rename = {}
        def push_scope(self):
            self.scopes.append({})
        def pop_scope(self):
            del self.scopes[-1]
        def visit(self, x):
            if isinstance(x, VariableDeclaration):
                t = x.type
                new_decls = []
                mods = x.modifiers
                for decl in x.variable_declarators:
                    new_name = fresh_name()
                    new_decls.append(VariableDeclarator(
                        Variable(new_name, decl.variable.dimensions),
                        self.visit(decl.initializer)))
                    self.rename[decl.variable.name] = new_name
                out(FieldDeclaration(t, new_decls, mods))
                return Block([Assignment(
                    operator="=",
                    lhs=Name(d.variable.name),
                    rhs=d.initializer)
                    for d in new_decls
                    if d.initializer])
            elif isinstance(x, Name):
                n = x.value
                if "." in n:
                    # I think this might be a bug in the parser...?
                    idx = n.rindex(".")
                    return self.visit(FieldAccess(target=Name(n[:idx]), name=n[idx+1:]))
                return Name(self.rename.get(n, n))
            elif isinstance(x, ForEach):
                assert not x.variable.dimensions
                assert isinstance(x.type, Type)
                v = Name(x.variable.name)
                t = x.type
                it = Name(fresh_name())
                it_t = Type("java.util.Iterator", [t])
                return self.visit(Block([
                    VariableDeclaration(t, [VariableDeclarator(Variable(v.value, 0))]),
                    VariableDeclaration(it_t, [VariableDeclarator(Variable(it.value, 0), MethodInvocation(target=x.iterable, name="iterator"))]),
                    While(MethodInvocation(target=it, name="hasNext"), Block([
                        Assignment(operator="=", lhs=v, rhs=MethodInvocation(target=it, name="next")),
                        x.body]))]))
            elif isinstance(x, For):
                raise NotImplementedError(x)
            return super().visit(x)
    return R().visit(stm)

class YieldNumberer(Visitor):
    def __init__(self):
        super().__init__(verbose=False)
        self.n = 0
    def visit_MethodInvocation(self, m):
        if m.name == "yield" and not m.target:
            m.number = self.n
            self.n += 1

def run_to_first_yield(stm, has_next_var, next_var, state_var, k=None):
    class R(Rewriter):
        def __init__(self):
            super().__init__()
            self.dead = False
        def visit(self, x):
            if x is None:
                return None
            if self.dead:
                return Empty()
            if isinstance(x, MethodInvocation) and not x.target and x.name == "yield":
                self.dead = True
                return Block([
                    Assignment(operator="=", lhs=has_next_var, rhs=Literal("true")),
                    Assignment(operator="=", lhs=next_var,     rhs=x.arguments[0]),
                    Assignment(operator="=", lhs=state_var,    rhs=Literal(str(x.number))) if state_var else Empty(),
                    Return()])
            if isinstance(x, While):
                new_body = self.visit(x.body)
                if self.dead:
                    if x.predicate == Literal("true"):
                        return new_body
                    self.dead = False
                    return IfThenElse(x.predicate, new_body)
                else:
                    self.dead = False
                    return While(x.predicate, new_body)
            if isinstance(x, IfThenElse):
                new_then = self.visit(x.if_true)
                d1 = self.dead
                self.dead = False
                new_else = self.visit(x.if_false)
                self.dead = d1 and self.dead
                return IfThenElse(x.predicate, new_then, new_else)
            return super().visit(x)
    rw = R()
    res = [rw.visit(stm)]
    if k and not rw.dead:
        res += [k]
    return res

def enumerate_conts(stm):
    if stm is None:
        return
    elif isinstance(stm, Block):
        for i in range(len(stm.statements)):
            for (e, k) in enumerate_conts(stm.statements[i]):
                yield (e, Block([k] + stm.statements[i+1:]))
    elif isinstance(stm, MethodInvocation) and not stm.target and stm.name == "yield":
        yield (stm.number, Empty())
    elif isinstance(stm, Expression):
        return
    elif isinstance(stm, While):
        for (e, k) in enumerate_conts(stm.body):
            yield (e, Block([k, stm]))
    elif isinstance(stm, IfThenElse):
        yield from enumerate_conts(stm.if_true)
        yield from enumerate_conts(stm.if_false)
    else:
        raise NotImplementedError(type(stm))

def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)

def go(in_f, out_f):
    parser = JavaParser()
    print("Parsing...")

    if in_f is not None:
        with open(in_f, "r") as f:
            contents = f.read()
    else:
        contents = sys.stdin.read()

    ast = parser.parse_string(contents)
    # print(ast)

    print("Finding 'generate' function...")
    clazz = ast.type_declarations[0]
    decls_to_keep = []
    stm = None
    for decl in clazz.body:
        if isinstance(decl, MethodDeclaration) and decl.name == "generate":
            if stm is not None:
                die("found duplicate generate() method")
            generated_type = decl.return_type
            args = decl.parameters
            stm = Block(decl.body)
        else:
            decls_to_keep.append(decl)
    if stm is None:
        die("found no generate() method")

    print("Extracting declarations...")
    decls = []
    stm = extract_declarations(stm, decls.append)
    # print(decls)

    print("Numbering yield statements...")
    stm.accept(YieldNumberer())

    print("Constructing iterator...")
    _hn    = FieldDeclaration(modifiers=["private"], type="boolean", variable_declarators=[VariableDeclarator(Variable(fresh_name()), Literal("false"))])
    _next  = FieldDeclaration(modifiers=["private"], type=generated_type, variable_declarators=[VariableDeclarator(Variable(fresh_name()), Literal("null"))])
    _state = FieldDeclaration(modifiers=["private"], type="int", variable_declarators=[VariableDeclarator(Variable(fresh_name()), Literal("0"))])

    _hn_var = Name(_hn.variable_declarators[0].variable.name)
    _next_var = Name(_next.variable_declarators[0].variable.name)
    conts = list(enumerate_conts(stm))
    _state_var = Name(_state.variable_declarators[0].variable.name) if len(conts) > 1 else None

    init = ConstructorDeclaration(
        clazz.name,
        modifiers=["public"],
        parameters=args,
        block=
            [Assignment(operator="=", lhs=FieldAccess(target="this", name=a.variable.name), rhs=Name(a.variable.name)) for a in args] +
            run_to_first_yield(stm, _hn_var, _next_var, _state_var, k=Break()))

    has_next = MethodDeclaration(
        "hasNext",
        modifiers=["public"],
        parameters=[],
        return_type="boolean",
        body=[Return(Name(_hn.variable_declarators[0].variable.name))])

    _tmpnext = VariableDeclarator(Variable(fresh_name()), Name(_next.variable_declarators[0].variable.name))
    get_next = MethodDeclaration(
        "next",
        modifiers=["public"],
        parameters=[],
        return_type=generated_type,
        body=[
            VariableDeclaration(generated_type, [_tmpnext]),
            MethodInvocation("advance", []),
            Return(Name(_tmpnext.variable.name))])

    advance = MethodDeclaration(
        "advance",
        modifiers=["private"],
        parameters=[],
        return_type="void",
        body=[Assignment(operator="=", lhs=_hn_var, rhs=Literal("false")),
            Switch(_state_var, [SwitchCase([Literal(str(i))], run_to_first_yield(k, _hn_var, _next_var, _state_var, k=Break())) for (i, k) in conts])
                if _state_var else
                Block(run_to_first_yield(conts[0][1], _hn_var, _next_var, _state_var, k=Empty())) if conts else
                Empty()])

    it = CompilationUnit(
        package_declaration=ast.package_declaration,
        import_declarations=ast.import_declarations,
        type_declarations=[
            ClassDeclaration(clazz.name,
                modifiers=clazz.modifiers,
                type_parameters=clazz.type_parameters,
                extends=clazz.extends,
                implements=clazz.implements,
                body=
                    decls_to_keep +
                    [FieldDeclaration(a.type, [VariableDeclarator(a.variable)], modifiers=["private"]) for a in args] +
                    [FieldDeclaration(d.type, [VariableDeclarator(v.variable) for v in d.variable_declarators], ["private"] + d.modifiers) for d in decls] +
                    [_hn, _next] + ([_state] if _state_var else []) +
                    [init, has_next, get_next, advance])])

    # print(it)
    print("Writing output...")
    if out_f is not None:
        with open(out_f, "w") as f:
            dump(it, f.write)
    else:
        dump(it, sys.stdout.write)

    print("Done.")

go(args.file, args.o)
