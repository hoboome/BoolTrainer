"""Совершенные нормальные формы: СДНФ и СКНФ."""


def _literal(name, positive):
    return name if positive else f"NOT {name}"


def _join(terms, inner_op, outer_op):
    """Собирает форму из термов; скобки ставятся, только если они нужны."""
    wrap = len(terms) > 1
    parts = []
    for literals in terms:
        s = f" {inner_op} ".join(literals)
        parts.append(f"({s})" if wrap and len(literals) > 1 else s)
    return f" {outer_op} ".join(parts)


def sdnf(table):
    """СДНФ: дизъюнкция конъюнкций по наборам, где функция равна 1.

    Если функция тождественно равна 0, возвращается "0".
    """
    terms = []
    for row, res in zip(table.rows, table.results):
        if res == 1:
            terms.append([_literal(v, bool(b)) for v, b in zip(table.variables, row)])
    if not terms:
        return "0"
    if not table.variables:
        return "1"
    return _join(terms, "AND", "OR")


def sknf(table):
    """СКНФ: конъюнкция дизъюнкций по наборам, где функция равна 0.

    Если функция тождественно равна 1, возвращается "1".
    """
    terms = []
    for row, res in zip(table.rows, table.results):
        if res == 0:
            terms.append([_literal(v, not b) for v, b in zip(table.variables, row)])
    if not terms:
        return "1"
    if not table.variables:
        return "0"
    return _join(terms, "OR", "AND")
