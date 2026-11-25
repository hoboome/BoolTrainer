"""Режим «Тренажёр»: загрузка теории, генерация и проверка заданий.

Ответ проверяется по смыслу, а не по тексту: любое выражение, равносильное
эталону, считается верным (для СДНФ дополнительно проверяется вид формы,
для упрощения — что выражение действительно стало короче).
"""
import json
import random
from dataclasses import dataclass

from .minimizer import minimize_table
from .normal_forms import sdnf
from .parser import count_literals, equivalent, parse, to_string, variables
from .truth_table import build_truth_table
from .validator import ExpressionError

TASK_KINDS = ("table", "sdnf", "simplify")

_OPS = ["AND", "OR", "XOR", "IMPL", "EQV", "NOR", "NAND"]
_WEIGHTS = [4, 4, 2, 2, 1, 1, 1]


@dataclass
class Task:
    kind: str             # table, sdnf или simplify
    expression: str       # исходное выражение
    variables: list
    prompt: str           # текст задания для пользователя
    correct_answer: str   # эталонный ответ для показа


@dataclass
class CheckResult:
    correct: bool
    message: str
    correct_answer: str


# ---------- теория ----------

def load_theory(path):
    """Читает файл с темами и проверяет его структуру."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Файл теории должен содержать список тем.")
    for topic in data:
        for key in ("id", "title", "text", "tasks"):
            if key not in topic:
                raise ValueError(f"В теме отсутствует поле '{key}'.")
        if not isinstance(topic["text"], list):
            raise ValueError(f"Поле 'text' темы '{topic['id']}' должно быть списком абзацев.")
        for kind in topic["tasks"]:
            if kind not in TASK_KINDS:
                raise ValueError(f"Неизвестный тип задания '{kind}' в теме '{topic['id']}'.")
    return data


def _digits_phrase(n):
    """«4 цифры», «8 цифр» — с правильным склонением."""
    return f"{n} цифры" if n in (2, 3, 4) else f"{n} цифр"


# ---------- генерация ----------

def _random_node(rng, names, depth):
    if depth == 0 or rng.random() < 0.2:
        leaf = ("var", rng.choice(names))
        return ("not", leaf) if rng.random() < 0.3 else leaf
    op = rng.choices(_OPS, _WEIGHTS)[0]
    return ("bin", op, _random_node(rng, names, depth - 1), _random_node(rng, names, depth - 1))


def random_expression(rng, n_vars, depth):
    """Случайное выражение, использующее все n_vars переменных и не равное константе."""
    names = list("ABCDE"[:n_vars])
    for _ in range(500):
        node = _random_node(rng, names, depth)
        if len(variables(node)) != n_vars:
            continue
        results = build_truth_table(node).results
        if 0 < sum(results) < len(results):
            return node
    return ("bin", "XOR", ("var", "A"), ("var", "B"))   # запасной вариант


def generate_task(kind, rng=None):
    """Создаёт случайное задание типа kind."""
    if kind not in TASK_KINDS:
        raise ValueError(f"Неизвестный тип задания '{kind}'.")
    rng = rng or random.Random()
    if kind == "simplify":
        node = random_expression(rng, 3, 3)
    else:
        node = random_expression(rng, rng.choice([2, 3]), 2)
    text = to_string(node)
    table = build_truth_table(node)
    names = table.variables

    if kind == "table":
        prompt = (f"Найдите значения функции F = {text} на всех наборах "
                  f"({', '.join(names)}), идущих по возрастанию. "
                  f"Введите {_digits_phrase(2 ** len(names))} подряд.")
        correct = "".join(str(r) for r in table.results)
    elif kind == "sdnf":
        prompt = f"Запишите СДНФ функции F = {text}."
        correct = sdnf(table)
    else:
        prompt = f"Упростите выражение F = {text}."
        correct = minimize_table(table).expression
    return Task(kind, text, names, prompt, correct)


# ---------- проверка ----------

def _flatten(node, op):
    if node[0] == "bin" and node[1] == op:
        return _flatten(node[2], op) + _flatten(node[3], op)
    return [node]


def _literal(node):
    """('var','A') -> ('A', True); ('not',('var','A')) -> ('A', False); иначе None."""
    if node[0] == "var":
        return node[1], True
    if node[0] == "not" and node[1][0] == "var":
        return node[1][1], False
    return None


def is_sdnf(node, names):
    """Проверяет, что выражение записано как СДНФ: ИЛИ из полных И-термов."""
    seen = set()
    for term in _flatten(node, "OR"):
        literals = [_literal(x) for x in _flatten(term, "AND")]
        if None in literals:
            return False
        if sorted(name for name, _ in literals) != sorted(names):
            return False
        key = frozenset(literals)
        if key in seen:
            return False
        seen.add(key)
    return True


def check_answer(task, answer):
    """Проверяет ответ пользователя и возвращает CheckResult."""
    ok_result = CheckResult(True, "Верно!", task.correct_answer)

    def wrong(msg):
        return CheckResult(False, msg, task.correct_answer)

    if task.kind == "table":
        extra = [ch for ch in answer if ch not in "01 ,;\t"]
        digits = [ch for ch in answer if ch in "01"]
        n_rows = 2 ** len(task.variables)
        if extra or len(digits) != n_rows:
            return wrong(f"Нужно ввести {_digits_phrase(n_rows)} (0 и 1).")
        return ok_result if "".join(digits) == task.correct_answer else wrong("Неверно.")

    try:
        user = parse(answer)
    except ExpressionError as e:
        return wrong(f"Ошибка в записи ответа: {e}")
    if not equivalent(parse(task.expression), user):
        return wrong("Неверно: ваше выражение не равносильно исходному.")

    if task.kind == "sdnf":
        if not is_sdnf(user, task.variables):
            return wrong("Функция записана верно, но это не СДНФ: каждый терм "
                         "должен содержать все переменные, а термы соединяются через OR.")
        return ok_result

    # simplify
    best = minimize_table(build_truth_table(task.expression))
    if count_literals(user) > best.literal_count:
        return wrong("Выражение равносильно исходному, но его можно упростить дальше.")
    return ok_result
