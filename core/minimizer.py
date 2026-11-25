"""Минимизация булевой функции методом Куайна — Мак-Класки.

Импликанта записывается строкой из символов '0', '1' и '-' по числу
переменных: '-' означает, что переменная в импликанту не входит.
Например, для переменных A, B, C строка '1-0' задаёт A AND NOT C.
"""
from dataclasses import dataclass, field


@dataclass
class MinimizationResult:
    implicants: list                              # выбранные импликанты, например ['1-0', '-11']
    terms: list = field(default_factory=list)     # то же в виде [[("A", True), ("C", False)], ...]
    expression: str = "0"                         # минимальная ДНФ в виде строки

    @property
    def literal_count(self):
        return sum(len(t) for t in self.terms)


def _combine(a, b):
    """Склеивает две импликанты, отличающиеся ровно одной позицией; иначе None."""
    diff = -1
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            if x == "-" or y == "-" or diff != -1:
                return None
            diff = i
    if diff == -1:
        return None
    return a[:diff] + "-" + a[diff + 1:]


def prime_implicants(minterms, n):
    """Все простые импликанты функции от n переменных с заданными минтермами."""
    current = {format(m, f"0{n}b") if n else "" for m in minterms}
    primes = set()
    while current:
        used = set()
        nxt = set()
        items = sorted(current)
        for i, a in enumerate(items):
            for b in items[i + 1:]:
                c = _combine(a, b)
                if c is not None:
                    nxt.add(c)
                    used.add(a)
                    used.add(b)
        primes |= current - used
        current = nxt
    return sorted(primes)


def covers(implicant, minterm, n):
    """Покрывает ли импликанта минтерм с номером minterm."""
    bits = format(minterm, f"0{n}b") if n else ""
    return all(p == "-" or p == b for p, b in zip(implicant, bits))


def _literals_count(implicant):
    return sum(1 for ch in implicant if ch != "-")


def _choose_cover(primes, minterms, n):
    """Выбирает набор простых импликант минимальной стоимости.

    Стоимость — (число импликант, число литералов). Используется перебор
    с отсечением: на каждом шаге берётся непокрытый минтерм, который
    покрывают меньше всего импликант.
    """
    cover_sets = {p: {m for m in minterms if covers(p, m, n)} for p in primes}
    best = {"cost": None, "sel": None}

    def search(uncovered, chosen):
        cost = (len(chosen), sum(_literals_count(p) for p in chosen))
        if best["cost"] is not None and cost >= best["cost"]:
            return
        if not uncovered:
            best["cost"], best["sel"] = cost, list(chosen)
            return
        target = min(uncovered, key=lambda m: sum(1 for p in primes if m in cover_sets[p]))
        for p in primes:
            if target in cover_sets[p]:
                search(uncovered - cover_sets[p], chosen + [p])

    search(set(minterms), [])
    return sorted(best["sel"])


def implicant_to_term(implicant, variables):
    """Импликанта -> список литералов [(имя, True/False), ...]."""
    return [(v, ch == "1") for v, ch in zip(variables, implicant) if ch != "-"]


def _term_to_string(term):
    return " AND ".join(name if positive else f"NOT {name}" for name, positive in term)


def minimize(variables, minterms):
    """Минимальная ДНФ по списку переменных и номерам минтермов."""
    n = len(variables)
    minterms = sorted(set(minterms))
    if not minterms:
        return MinimizationResult(implicants=[], terms=[], expression="0")
    if len(minterms) == 2 ** n:
        return MinimizationResult(implicants=["-" * n], terms=[[]], expression="1")

    primes = prime_implicants(minterms, n)
    chosen = _choose_cover(primes, minterms, n)
    terms = [implicant_to_term(p, variables) for p in chosen]
    wrap = len(terms) > 1
    parts = []
    for t in terms:
        s = _term_to_string(t)
        parts.append(f"({s})" if wrap and len(t) > 1 else s)
    return MinimizationResult(implicants=chosen, terms=terms, expression=" OR ".join(parts))


def minimize_table(table):
    """Минимальная ДНФ функции, заданной таблицей истинности."""
    return minimize(table.variables, table.minterms)
