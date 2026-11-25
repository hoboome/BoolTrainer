"""Разбор булевых выражений в дерево и вычисление значений.

Дерево (AST) состоит из кортежей:
    ("var", "A"), ("const", 0), ("not", узел), ("bin", "AND", левый, правый)

Приоритеты операций (от высшего к низшему):
    NOT > AND, NAND > XOR > OR, NOR > IMPL (правоассоциативна) > EQV
"""
from .validator import ExpressionError, check_tokens, tokenize

PRECEDENCE = {"EQV": 1, "IMPL": 2, "OR": 3, "NOR": 3, "XOR": 4, "AND": 5, "NAND": 5}
RIGHT_ASSOC = {"IMPL"}


class _Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def expr(self, min_prec):
        left = self.unary()
        while True:
            t = self.peek()
            if t is None or t.kind != "op" or PRECEDENCE[t.value] < min_prec:
                break
            self.pos += 1
            prec = PRECEDENCE[t.value]
            right = self.expr(prec if t.value in RIGHT_ASSOC else prec + 1)
            left = ("bin", t.value, left, right)
        return left

    def unary(self):
        t = self.tokens[self.pos]
        self.pos += 1
        if t.kind == "not":
            return ("not", self.unary())
        if t.kind == "var":
            return ("var", t.value)
        if t.kind == "const":
            return ("const", int(t.value))
        inner = self.expr(1)   # t — открывающая скобка
        self.pos += 1          # пропускаем закрывающую
        return inner


def parse(text):
    """Строит дерево выражения; при ошибке синтаксиса выбрасывает ExpressionError."""
    tokens = tokenize(text)
    check_tokens(tokens)
    return _Parser(tokens).expr(1)


def variables(node):
    """Отсортированный список переменных выражения."""
    found = set()

    def walk(n):
        if n[0] == "var":
            found.add(n[1])
        elif n[0] == "not":
            walk(n[1])
        elif n[0] == "bin":
            walk(n[2])
            walk(n[3])

    walk(node)
    return sorted(found)


def evaluate(node, env):
    """Значение выражения (0 или 1) для набора env = {"A": 1, ...}."""
    kind = node[0]
    if kind == "var":
        return env[node[1]]
    if kind == "const":
        return node[1]
    if kind == "not":
        return 1 - evaluate(node[1], env)
    op = node[1]
    a = evaluate(node[2], env)
    b = evaluate(node[3], env)
    if op == "AND":
        return a & b
    if op == "OR":
        return a | b
    if op == "XOR":
        return a ^ b
    if op == "IMPL":
        return int((not a) or b)
    if op == "EQV":
        return int(a == b)
    if op == "NOR":
        return 1 - (a | b)
    if op == "NAND":
        return 1 - (a & b)
    raise ExpressionError(f"Неизвестная операция: {op}")


def to_string(node, top=True):
    """Запись дерева в виде строки (бинарные подвыражения — в скобках)."""
    kind = node[0]
    if kind == "var":
        return node[1]
    if kind == "const":
        return str(node[1])
    if kind == "not":
        return "NOT " + to_string(node[1], top=False)
    s = f"{to_string(node[2], False)} {node[1]} {to_string(node[3], False)}"
    return s if top else f"({s})"


def count_literals(node):
    """Число вхождений переменных в выражение."""
    kind = node[0]
    if kind == "var":
        return 1
    if kind == "const":
        return 0
    if kind == "not":
        return count_literals(node[1])
    return count_literals(node[2]) + count_literals(node[3])


def equivalent(a, b):
    """Проверяет, что два дерева задают одну и ту же функцию."""
    names = sorted(set(variables(a)) | set(variables(b)))
    n = len(names)
    for i in range(2 ** n):
        env = {v: (i >> (n - 1 - j)) & 1 for j, v in enumerate(names)}
        if evaluate(a, env) != evaluate(b, env):
            return False
    return True
