from plyj.model import *

def dump_seq(seq, out, sep="", indent="", **kwargs):
    if not isinstance(seq, list) and not isinstance(seq, tuple):
        seq = list(seq)
    for i in range(len(seq)):
        if i > 0 and sep:
            out(sep)
        dump(seq[i], out, indent, **kwargs)

INDENT = "  "

def dump(ast, out, indent="", as_stm=False):
    if isinstance(ast, CompilationUnit):
        if ast.package_declaration:
            out("package ")
            out(ast.package_declaration)
            out(";\n")
        for imp in ast.import_declarations:
            assert not imp.on_demand
            out("import ")
            if imp.static:
                out("static ")
            dump(imp.name, out)
            out(";\n")
        for t in ast.type_declarations:
            dump(t, out)
    elif isinstance(ast, ClassDeclaration):
        out(indent)
        for m in ast.modifiers:
            out(m)
            out(" ")
        out("class ")
        out(ast.name)
        assert not ast.type_parameters
        assert not ast.extends
        if ast.implements:
            out(" implements ")
            dump_seq(ast.implements, out, sep=", ")
        out(" {\n")
        dump_seq(ast.body, out, indent=INDENT+indent)
        out(indent)
        out("}\n")
    elif isinstance(ast, Name):
        out(ast.value)
    elif isinstance(ast, Type):
        dump(ast.name, out)
        if ast.type_arguments == "diamond":
            out("<>")
        elif ast.type_arguments:
            out("<")
            dump_seq(ast.type_arguments, out, sep=", ")
            out(">")
        assert not ast.enclosed_in
        assert not ast.dimensions
    elif isinstance(ast, FieldDeclaration):
        out(indent)
        for m in ast.modifiers:
            out(m)
            out(" ")
        dump(ast.type, out)
        out(" ")
        dump_seq(ast.variable_declarators, out, sep=", ");
        out(";\n")
    elif isinstance(ast, VariableDeclarator):
        dump(ast.variable, out)
        if ast.initializer:
            out(" = ")
            dump(ast.initializer, out)
    elif isinstance(ast, Variable):
        out(ast.name)
        out("[]" * ast.dimensions)
    elif isinstance(ast, Literal):
        out(ast.value)
    elif isinstance(ast, str):
        out(ast)
    elif isinstance(ast, ConstructorDeclaration):
        assert not ast.throws
        out(indent)
        for m in ast.modifiers:
            out(m)
            out(" ")
        out(ast.name)
        out("(")
        dump_seq(ast.parameters, out, sep=", ")
        out(") {\n")
        for stm in ast.block:
            dump(stm, out, indent=INDENT+indent, as_stm=True)
        out(indent)
        out("}\n")
    elif isinstance(ast, MethodDeclaration):
        assert not ast.throws
        assert not ast.type_parameters
        out(indent)
        for m in ast.modifiers:
            out(m)
            out(" ")
        dump(ast.return_type, out)
        out(" ")
        out(ast.name)
        out("(")
        dump_seq(ast.parameters, out, sep=", ")
        out(") {\n")
        for stm in ast.body:
            dump(stm, out, indent=INDENT+indent, as_stm=True)
        out(indent)
        out("}\n")
    elif isinstance(ast, FormalParameter):
        for m in ast.modifiers:
            out(m)
            out(" ")
        dump(ast.type, out)
        out(" ")
        dump(ast.variable, out)
        if ast.vararg:
            out("...")
    elif isinstance(ast, Assignment):
        out(indent)
        dump(ast.lhs, out)
        out(" ")
        out(ast.operator)
        out(" ")
        dump(ast.rhs, out)
        out(";\n")
    elif isinstance(ast, Return):
        out(indent)
        if ast.result:
            out("return ")
            dump(ast.result, out)
            out(";\n")
        else:
            out("return;\n")
    elif isinstance(ast, Break):
        out(indent)
        out("break;\n")
    elif isinstance(ast, Continue):
        out(indent)
        out("continue;\n")
    elif isinstance(ast, FieldAccess):
        dump(ast.target, out)
        out(".")
        out(ast.name)
    elif isinstance(ast, MethodInvocation):
        if as_stm:
            out(indent)
        if ast.target:
            dump(ast.target, out)
            out(".")
        out(ast.name)
        out("(")
        dump_seq(ast.arguments, out, sep=", ")
        out(")")
        if as_stm:
            out(";\n")
    elif isinstance(ast, Block):
        out(indent)
        out("{\n")
        dump_seq(ast.statements, out, indent=INDENT+indent, as_stm=True)
        out(indent)
        out("}\n")
    elif isinstance(ast, IfThenElse):
        out(indent)
        out("if (")
        dump(ast.predicate, out)
        out(")\n")
        dump(ast.if_true, out, indent=indent, as_stm=True)
        if ast.if_false:
            out(indent)
            out("else\n")
            dump(ast.if_false, out, indent=indent, as_stm=True)
    elif isinstance(ast, Empty):
        return
    elif isinstance(ast, While):
        out(indent)
        out("while (")
        dump(ast.predicate, out)
        out(")\n")
        dump(ast.body, out, indent=indent, as_stm=True)
    elif isinstance(ast, BinaryExpression):
        out("(")
        dump(ast.lhs, out)
        out(" ")
        out(ast.operator)
        out(" ")
        dump(ast.rhs, out)
        out(")")
    elif isinstance(ast, Unary):
        out("(")
        out(ast.sign)
        dump(ast.expression, out)
        out(")")
    elif isinstance(ast, Switch):
        out(indent)
        out("switch (")
        dump(ast.expression, out)
        out(") {\n")
        for branch in ast.switch_cases:
            for case in branch.cases:
                out(indent)
                out(INDENT)
                if case == "default":
                    out("default:\n")
                else:
                    out("case ")
                    dump(case, out)
                    out(":\n")
            dump_seq(branch.body, out, indent=INDENT*2+indent, as_stm=True)
        out(indent)
        out("}\n")
    elif isinstance(ast, InstanceCreation):
        assert not ast.enclosed_in
        assert not ast.type_arguments
        assert not ast.body
        out("new ")
        dump(ast.type, out)
        out("(")
        dump_seq(ast.arguments, out, sep=", ")
        out(")")
    else:
        raise NotImplementedError(ast)
