"""Тесты режима «Тренажёр»."""
import os
import random
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.parser import parse
from core.tasks import (TASK_KINDS, Task, check_answer, generate_task, is_sdnf,
                        load_theory)

THEORY = os.path.join(os.path.dirname(__file__), "..", "data", "theory.json")


def test_theory_file_is_valid():
    topics = load_theory(THEORY)
    assert len(topics) >= 3
    assert all(set(t["tasks"]) <= set(TASK_KINDS) for t in topics)


def test_generated_tasks_are_solved_by_their_own_answer():
    rng = random.Random(42)
    for kind in TASK_KINDS:
        for _ in range(60):
            task = generate_task(kind, rng)
            result = check_answer(task, task.correct_answer)
            assert result.correct, (kind, task.prompt, task.correct_answer, result.message)


def test_generation_is_reproducible_with_seed():
    a = generate_task("sdnf", random.Random(7))
    b = generate_task("sdnf", random.Random(7))
    assert a.expression == b.expression


def test_table_answer_checking():
    task = Task("table", "A AND B", ["A", "B"], "", "0001")
    assert check_answer(task, "0001").correct
    assert check_answer(task, "0 0 0 1").correct
    assert not check_answer(task, "0011").correct
    assert "4 цифры" in check_answer(task, "001").message
    assert "4 цифры" in check_answer(task, "abcd").message


def test_sdnf_answer_must_be_sdnf():
    task = Task("sdnf", "A XOR B", ["A", "B"], "", "(NOT A AND B) OR (A AND NOT B)")
    assert check_answer(task, "(NOT A AND B) OR (A AND NOT B)").correct
    assert check_answer(task, "(A AND NOT B) OR (NOT A AND B)").correct
    not_sdnf = check_answer(task, "A XOR B")
    assert not not_sdnf.correct and "не СДНФ" in not_sdnf.message
    assert not check_answer(task, "A OR B").correct
    assert "Ошибка" in check_answer(task, "A AND").message


def test_is_sdnf_rejects_incomplete_and_duplicate_terms():
    names = ["A", "B"]
    assert is_sdnf(parse("(A AND B) OR (NOT A AND B)"), names)
    assert not is_sdnf(parse("B"), names)
    assert not is_sdnf(parse("(A AND B) OR (A AND B)"), names)


def test_simplify_requires_real_simplification():
    task = Task("simplify", "(A AND B) OR (A AND NOT B)", ["A", "B"], "", "A")
    assert check_answer(task, "A").correct
    longer = check_answer(task, "(A AND B) OR (A AND NOT B)")
    assert not longer.correct and "упростить" in longer.message
    assert not check_answer(task, "B").correct
