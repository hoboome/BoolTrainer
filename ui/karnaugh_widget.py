"""Виджет карты Карно: сетка со значениями функции и цветные рамки групп."""
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

PALETTE = ["#d62728", "#1f77b4", "#2ca02c", "#ff7f0e",
           "#9467bd", "#8c564b", "#e377c2", "#17becf"]
CELL = 72
LEFT = 110
TOP = 60
EMPTY_TEXT = "Нажмите «Рассчитать»: карта строится для 2–4 переменных"


class KarnaughWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.kmap = None
        self.groups = []          # список пар (импликанта, текст слагаемого)
        self.message = EMPTY_TEXT
        self.setMinimumSize(560, 460)

    def set_data(self, kmap, groups):
        self.kmap = kmap
        self.groups = groups
        self.message = ""
        self.update()

    def show_message(self, text):
        self.kmap = None
        self.groups = []
        self.message = text
        self.update()

    def clear(self):
        self.show_message(EMPTY_TEXT)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.kmap is None:
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.message)
            return

        kmap = self.kmap
        rows, cols = len(kmap.minterm_grid), len(kmap.minterm_grid[0])
        font = QFont()
        font.setPointSize(11)
        painter.setFont(font)
        painter.setPen(QColor("#222222"))

        # подписи осей
        corner = f"{''.join(kmap.row_vars)} \\ {''.join(kmap.col_vars)}"
        painter.drawText(QRect(5, TOP - 32, LEFT - 10, 28),
                         Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, corner)
        for c, label in enumerate(kmap.col_labels):
            painter.drawText(QRect(LEFT + c * CELL, TOP - 32, CELL, 28),
                             Qt.AlignmentFlag.AlignCenter, label)
        for r, label in enumerate(kmap.row_labels):
            painter.drawText(QRect(LEFT - 56, TOP + r * CELL, 50, CELL),
                             Qt.AlignmentFlag.AlignCenter, label)

        # клетки и значения функции
        value_font = QFont()
        value_font.setPointSize(16)
        value_font.setBold(True)
        for r in range(rows):
            for c in range(cols):
                x, y = LEFT + c * CELL, TOP + r * CELL
                if kmap.value_grid[r][c] == 1:
                    painter.fillRect(x, y, CELL, CELL, QColor("#f4f8ec"))
                painter.setPen(QPen(QColor("#888888"), 1))
                painter.drawRect(x, y, CELL, CELL)
                painter.setFont(value_font)
                painter.setPen(QColor("#222222"))
                painter.drawText(QRect(x, y, CELL, CELL), Qt.AlignmentFlag.AlignCenter,
                                 str(kmap.value_grid[r][c]))

        # рамки групп: у каждой группы свой цвет, рамки вложены друг в друга
        for g, (implicant, _) in enumerate(self.groups):
            painter.setPen(QPen(QColor(PALETTE[g % len(PALETTE)]), 3))
            inset = 3 + 3 * (g % len(PALETTE))
            for r, c in kmap.cells_of(implicant):
                painter.drawRoundedRect(LEFT + c * CELL + inset, TOP + r * CELL + inset,
                                        CELL - 2 * inset, CELL - 2 * inset, 8, 8)

        # легенда
        painter.setFont(font)
        y = TOP + rows * CELL + 28
        for g, (_, text) in enumerate(self.groups):
            color = QColor(PALETTE[g % len(PALETTE)])
            painter.fillRect(LEFT, y, 16, 16, color)
            painter.setPen(QColor("#222222"))
            painter.drawText(QRect(LEFT + 26, y - 4, 460, 24),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                             f"Группа {g + 1}: {text}")
            y += 26
