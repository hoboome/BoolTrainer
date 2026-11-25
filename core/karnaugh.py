"""Раскладка карты Карно для функций от 2–4 переменных."""
from dataclasses import dataclass

from .minimizer import covers

# Какие переменные идут по строкам, а какие по столбцам
_LAYOUT = {2: (1, 1), 3: (1, 2), 4: (2, 2)}


def gray(bits):
    """Код Грея длины bits: соседние коды отличаются одним разрядом."""
    return [i ^ (i >> 1) for i in range(2 ** bits)]


@dataclass
class KarnaughMap:
    variables: list
    row_vars: list
    col_vars: list
    row_labels: list      # подписи строк, например ['00', '01', '11', '10']
    col_labels: list
    minterm_grid: list    # номер набора в каждой клетке
    value_grid: list      # значение функции в каждой клетке

    def cells_of(self, implicant):
        """Клетки (строка, столбец), которые покрывает импликанта."""
        n = len(self.variables)
        return [
            (r, c)
            for r, row in enumerate(self.minterm_grid)
            for c, m in enumerate(row)
            if covers(implicant, m, n)
        ]


def build_karnaugh_map(table):
    n = len(table.variables)
    if n not in _LAYOUT:
        raise ValueError("Карта Карно строится для функций от 2 до 4 переменных.")
    rb, cb = _LAYOUT[n]
    row_codes, col_codes = gray(rb), gray(cb)
    minterm_grid = [[(rc << cb) | cc for cc in col_codes] for rc in row_codes]
    value_grid = [[table.results[m] for m in row] for row in minterm_grid]
    return KarnaughMap(
        variables=table.variables,
        row_vars=table.variables[:rb],
        col_vars=table.variables[rb:],
        row_labels=[format(c, f"0{rb}b") for c in row_codes],
        col_labels=[format(c, f"0{cb}b") for c in col_codes],
        minterm_grid=minterm_grid,
        value_grid=value_grid,
    )
