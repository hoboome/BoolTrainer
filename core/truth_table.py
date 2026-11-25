"""Построение таблицы истинности."""
from dataclasses import dataclass, field

from .parser import evaluate, parse, variables


@dataclass
class TruthTable:
    variables: list
    rows: list = field(default_factory=list)      # наборы значений переменных
    results: list = field(default_factory=list)   # значение функции на каждом наборе

    @property
    def minterms(self):
        """Номера наборов, на которых функция равна 1."""
        return [i for i, r in enumerate(self.results) if r == 1]

    @property
    def maxterms(self):
        """Номера наборов, на которых функция равна 0."""
        return [i for i, r in enumerate(self.results) if r == 0]

    def as_text(self):
        header = " ".join(self.variables + ["F"])
        lines = [header]
        for row, res in zip(self.rows, self.results):
            lines.append(" ".join(str(b) for b in row) + f" {res}")
        return "\n".join(lines)


def build_truth_table(expression):
    """Строит таблицу по строке или по готовому дереву выражения.

    Наборы идут по возрастанию, старшая переменная — первая (A).
    """
    node = parse(expression) if isinstance(expression, str) else expression
    names = variables(node)
    n = len(names)
    table = TruthTable(variables=names)
    for i in range(2 ** n):
        row = tuple((i >> (n - 1 - j)) & 1 for j in range(n))
        env = dict(zip(names, row))
        table.rows.append(row)
        table.results.append(evaluate(node, env))
    return table
