"""Модульные тесты логического ядра (запуск: pytest)."""
import itertools
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.karnaugh import build_karnaugh_map, gray
from core.minimizer import minimize, minimize_table, prime_implicants
from core.normal_forms import sdnf, sknf
from core.parser import equivalent, evaluate, parse, to_string, variables
from core.truth_table import build_truth_table
from core.validator import ExpressionError, validate


def results(expr):
    return build_truth_table(expr).results


def raises_expression_error(expr):
    try:
        parse(expr)
    except ExpressionError:
        return True
    return False


# ---------- проверка синтаксиса ----------

def test_valid_expressions():
    valid = ["A", "1", "NOT A", "A AND B", "(A OR B) IMPL C", "A EQV B",
             "A NOR B", "A NAND B", "NOT (A AND B)", "A XOR B", "a and b",
             "A → B", "A -> B", "NOT NOT A", "((A))"]
    for expr in valid:
        ok, msg = validate(expr)
        assert ok, f"'{expr}' должно быть корректным, но ошибка: {msg}"


def test_invalid_expressions():
    invalid = ["", "   ", "A B", "AND A", "A AND", "()", "(A", "A)", "A & B",
               "F", "A AND OR B", "A NOT B", "NOT", "A (B)", "ABC", "( AND A)"]
    for expr in invalid:
        ok, msg = validate(expr)
        assert not ok and msg, f"'{expr}' должно быть некорректным"


def test_error_messages_are_specific():
    cases = {
        "A B": "Пропущен оператор",
        "(A": "незакрытые",
        "A)": "без открывающей",
        "()": "Пустые скобки",
        "F": "Недопустимая переменная",
        "A & B": "Недопустимый символ",
        "": "пустое",
    }
    for expr, fragment in cases.items():
        ok, msg = validate(expr)
        assert not ok and fragment in msg, (expr, msg)


# ---------- вычисление ----------

def test_basic_operations():
    assert results("A AND B") == [0, 0, 0, 1]
    assert results("A OR B") == [0, 1, 1, 1]
    assert results("A XOR B") == [0, 1, 1, 0]
    assert results("A IMPL B") == [1, 1, 0, 1]
    assert results("A EQV B") == [1, 0, 0, 1]
    assert results("A NOR B") == [1, 0, 0, 0]
    assert results("A NAND B") == [1, 1, 1, 0]
    assert results("NOT A") == [1, 0]


def test_constants_and_no_variables():
    table = build_truth_table("1 OR 0")
    assert table.variables == [] and table.results == [1]
    assert results("0") == [0]


def test_precedence_and_brackets():
    # AND сильнее OR
    assert results("A OR B AND C") == results("A OR (B AND C)")
    assert results("A OR B AND C") != results("(A OR B) AND C")
    # NOT сильнее AND
    assert results("NOT A AND B") == results("(NOT A) AND B")
    # IMPL правоассоциативна
    assert results("A IMPL B IMPL C") == results("A IMPL (B IMPL C)")


def test_symbol_aliases():
    assert equivalent(parse("A → B"), parse("A IMPL B"))
    assert equivalent(parse("A ≡ B"), parse("A EQV B"))
    assert equivalent(parse("A ↓ B"), parse("A NOR B"))
    assert equivalent(parse("A | B"), parse("A NAND B"))
    assert equivalent(parse("¬A ∧ B"), parse("NOT A AND B"))


def test_variables_sorted_and_unique():
    assert variables(parse("C AND A OR B AND A")) == ["A", "B", "C"]
    assert variables(parse("1 OR 0")) == []


def test_row_order_matches_binary_counting():
    table = build_truth_table("A")
    assert table.rows == [(0,), (1,)]
    table = build_truth_table("A AND B AND C")
    assert table.rows[1] == (0, 0, 1) and table.rows[7] == (1, 1, 1)


def test_to_string_roundtrip():
    for expr in ["A AND (B OR C)", "NOT (A XOR B)", "(A IMPL B) EQV C"]:
        assert equivalent(parse(expr), parse(to_string(parse(expr))))


def test_five_variables():
    table = build_truth_table("(A OR B) AND (C OR D) AND E")
    assert len(table.rows) == 32 and sum(table.results) == 9


# ---------- СДНФ и СКНФ ----------

def test_sdnf_sknf_xor():
    table = build_truth_table("A XOR B")
    assert sdnf(table) == "(NOT A AND B) OR (A AND NOT B)"
    assert sknf(table) == "(A OR B) AND (NOT A OR NOT B)"


def test_normal_forms_are_equivalent_to_source():
    for expr in ["A IMPL B", "(A AND B) OR NOT C", "A EQV B EQV C", "A NOR B XOR C"]:
        table = build_truth_table(expr)
        node = parse(expr)
        assert equivalent(node, parse(sdnf(table))), expr
        assert equivalent(node, parse(sknf(table))), expr


def test_normal_forms_constants():
    assert sdnf(build_truth_table("A AND NOT A")) == "0"
    assert sknf(build_truth_table("A OR NOT A")) == "1"


# ---------- минимизация ----------

def test_minimize_classic_examples():
    assert minimize(["A", "B"], [1, 3]).expression == "B"
    assert minimize(["A", "B", "C"], [0, 1, 2, 3]).expression == "NOT A"
    assert minimize(["A", "B", "C"], []).expression == "0"
    assert minimize(["A", "B"], [0, 1, 2, 3]).expression == "1"


def test_prime_implicants_known_case():
    # f = Σ(0,1,2,5,6,7) — циклическая функция, у неё 6 простых импликант
    primes = prime_implicants([0, 1, 2, 5, 6, 7], 3)
    assert sorted(primes) == sorted(["00-", "0-0", "-01", "1-1", "11-", "-10"])


def test_minimize_is_equivalent_and_not_longer_than_sdnf():
    # перебираем все 256 функций от трёх переменных
    names = ["A", "B", "C"]
    for mask in range(256):
        minterms = [i for i in range(8) if (mask >> i) & 1]
        result = minimize(names, minterms)
        node = parse(result.expression)
        table = build_truth_table(node)
        got = set()
        for i in range(8):
            env = {v: (i >> (2 - j)) & 1 for j, v in enumerate(names)}
            if evaluate(node, env):
                got.add(i)
        assert got == set(minterms), (minterms, result.expression)
        assert result.literal_count <= 3 * len(minterms)


def test_minimize_four_variables_checkerboard_is_not_reduced():
    minterms = [i for i in range(16) if bin(i).count("1") % 2 == 1]   # A XOR B XOR C XOR D
    result = minimize(["A", "B", "C", "D"], minterms)
    assert len(result.implicants) == 8


# ---------- карта Карно ----------

def test_gray_code():
    assert gray(1) == [0, 1]
    assert gray(2) == [0, 1, 3, 2]


def test_karnaugh_layout_4_variables():
    kmap = build_karnaugh_map(build_truth_table("A OR B OR C OR D"))
    assert kmap.row_labels == ["00", "01", "11", "10"]
    assert kmap.col_labels == ["00", "01", "11", "10"]
    # соседние клетки отличаются одним разрядом номера набора, включая края
    grid = kmap.minterm_grid
    for r, c in itertools.product(range(4), range(4)):
        for dr, dc in ((0, 1), (1, 0)):
            r2, c2 = (r + dr) % 4, (c + dc) % 4
            assert bin(grid[r][c] ^ grid[r2][c2]).count("1") == 1


def test_karnaugh_values_match_truth_table():
    table = build_truth_table("(A AND B) OR (C AND NOT D)")
    kmap = build_karnaugh_map(table)
    for r, row in enumerate(kmap.minterm_grid):
        for c, m in enumerate(row):
            assert kmap.value_grid[r][c] == table.results[m]


def test_karnaugh_group_cells():
    # A AND (B OR NOT B) = A: вся нижняя половина карты 2×2 (строка A = 1)
    table = build_truth_table("A AND (B OR NOT B)")
    kmap = build_karnaugh_map(table)
    result = minimize_table(table)
    assert result.implicants == ["1-"]
    assert sorted(kmap.cells_of("1-")) == [(1, 0), (1, 1)]


def test_karnaugh_wrap_around_group():
    table = build_truth_table("NOT B AND NOT D AND (A OR NOT A) AND (C OR NOT C)")   # углы карты 4×4
    kmap = build_karnaugh_map(table)
    result = minimize_table(table)
    cells = kmap.cells_of(result.implicants[0])
    assert sorted(cells) == [(0, 0), (0, 3), (3, 0), (3, 3)]


def test_karnaugh_rejects_wrong_size():
    try:
        build_karnaugh_map(build_truth_table("A"))
    except ValueError:
        return
    raise AssertionError("ожидалась ошибка для одной переменной")
