"""Проверка синтаксиса булевых выражений.

Выражение разбивается на токены, затем проверяется порядок соседних
токенов, баланс скобок и допустимость символов. При первой найденной
ошибке выбрасывается ExpressionError с понятным описанием на русском.
"""
from dataclasses import dataclass

VARIABLES = "ABCDE"
BINARY_OPS = ("AND", "OR", "XOR", "IMPL", "EQV", "NOR", "NAND")

# Допустимые символьные обозначения операций
SYMBOLS = {
    "¬": "NOT",
    "∧": "AND",
    "∨": "OR",
    "⊕": "XOR",
    "^": "XOR",
    "→": "IMPL",
    "≡": "EQV",
    "↓": "NOR",
    "|": "NAND",
}


class ExpressionError(ValueError):
    """Ошибка в записи выражения (текст ошибки предназначен для пользователя)."""


@dataclass(frozen=True)
class Token:
    kind: str   # var, const, op, not, lp, rp
    value: str


def tokenize(text):
    """Разбивает строку на токены. Регистр букв не учитывается."""
    s = text.upper()
    tokens = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch.isspace():
            i += 1
        elif ch == "(":
            tokens.append(Token("lp", "("))
            i += 1
        elif ch == ")":
            tokens.append(Token("rp", ")"))
            i += 1
        elif s.startswith("<->", i):
            tokens.append(Token("op", "EQV"))
            i += 3
        elif s.startswith("->", i):
            tokens.append(Token("op", "IMPL"))
            i += 2
        elif ch in SYMBOLS:
            name = SYMBOLS[ch]
            tokens.append(Token("not" if name == "NOT" else "op", name))
            i += 1
        elif ch in "01":
            tokens.append(Token("const", ch))
            i += 1
        elif ch.isalpha():
            j = i
            while j < len(s) and s[j].isalpha():
                j += 1
            word = s[i:j]
            if word == "NOT":
                tokens.append(Token("not", "NOT"))
            elif word in BINARY_OPS:
                tokens.append(Token("op", word))
            elif len(word) == 1 and word in VARIABLES:
                tokens.append(Token("var", word))
            elif len(word) == 1:
                raise ExpressionError(
                    f"Недопустимая переменная '{word}'. Допустимы: A, B, C, D, E.")
            else:
                raise ExpressionError(
                    f"Недопустимое слово '{word}'. Операции пишутся словами "
                    f"(NOT, AND, OR, XOR, IMPL, EQV, NOR, NAND), "
                    f"переменные — одной буквой.")
            i = j
        else:
            raise ExpressionError(f"Недопустимый символ '{ch}'.")
    return tokens


def check_tokens(tokens):
    """Проверяет порядок токенов и скобки; при ошибке выбрасывает ExpressionError."""
    if not tokens:
        raise ExpressionError("Выражение пустое.")

    first, last = tokens[0], tokens[-1]
    if first.kind == "op":
        raise ExpressionError(
            f"Выражение не может начинаться с оператора '{first.value}'.")
    if first.kind == "rp":
        raise ExpressionError(
            "Выражение не может начинаться с закрывающей скобки ')'.")

    depth = 0
    for i, t in enumerate(tokens):
        if t.kind == "lp":
            depth += 1
        elif t.kind == "rp":
            if depth == 0:
                raise ExpressionError("Закрывающая скобка ')' без открывающей.")
            depth -= 1
            if tokens[i - 1].kind == "lp":
                raise ExpressionError("Пустые скобки: '()'.")
    if depth > 0:
        raise ExpressionError("Есть незакрытые открывающие скобки '('.")

    if last.kind == "op":
        raise ExpressionError(
            f"Выражение не может заканчиваться оператором '{last.value}'.")
    if last.kind == "not":
        raise ExpressionError("Выражение не может заканчиваться на 'NOT'.")

    for a, b in zip(tokens, tokens[1:]):
        a_ends_operand = a.kind in ("var", "const", "rp")
        b_starts_operand = b.kind in ("var", "const", "not", "lp")
        if a_ends_operand and b.kind == "not":
            raise ExpressionError(
                f"Оператор 'NOT' должен стоять перед операндом, а не после '{a.value}'.")
        if a_ends_operand and b_starts_operand:
            raise ExpressionError(
                f"Пропущен оператор между '{a.value}' и '{b.value}'.")
        if a.kind == "op" and b.kind in ("op", "rp"):
            raise ExpressionError(
                f"Оператор '{a.value}' не может стоять перед '{b.value}'.")
        if a.kind == "lp" and b.kind == "op":
            raise ExpressionError(
                f"Оператор '{b.value}' не может стоять сразу после '('.")
        if a.kind == "not" and b.kind in ("op", "rp"):
            raise ExpressionError(
                "Оператор 'NOT' должен применяться к переменной, константе "
                f"или выражению в скобках, а не к '{b.value}'.")


def validate(text):
    """Возвращает (True, '') для корректного выражения и (False, сообщение) иначе."""
    try:
        check_tokens(tokenize(text))
    except ExpressionError as e:
        return False, str(e)
    return True, ""
