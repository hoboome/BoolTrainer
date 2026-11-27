"""Вкладка «Конструктор»: ввод выражения и вывод представлений функции."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.karnaugh import build_karnaugh_map
from core.minimizer import minimize_table
from core.normal_forms import sdnf, sknf
from core.parser import parse
from core.truth_table import build_truth_table
from core.validator import ExpressionError

from .export import render_table_image
from .karnaugh_widget import KarnaughWidget

OPERATIONS = ["NOT", "AND", "OR", "XOR", "IMPL", "EQV", "NOR", "NAND", "(", ")"]
OPERANDS = ["A", "B", "C", "D", "E", "0", "1"]


class ConstructorView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_table = None        # таблица последнего расчёта (понадобится для экспорта)
        self.last_expression = ""
        self._build_ui()

    # ---------- построение интерфейса ----------

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.addWidget(self._build_left_panel(), 0)
        root.addWidget(self._build_results_panel(), 1)

    def _build_left_panel(self):
        panel = QWidget()
        panel.setFixedWidth(400)
        layout = QVBoxLayout(panel)

        input_box = QGroupBox("Введите выражение")
        input_layout = QVBoxLayout(input_box)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Например: (A AND B) OR NOT C")
        self.input.setStyleSheet("font-size: 16px; padding: 4px;")
        self.input.returnPressed.connect(self.calculate)
        input_layout.addWidget(self.input)
        layout.addWidget(input_box)

        layout.addWidget(self._button_group("Операции", OPERATIONS, columns=5))
        layout.addWidget(self._button_group("Переменные и константы", OPERANDS, columns=7))

        calc_button = QPushButton("Рассчитать")
        calc_button.clicked.connect(self.calculate)
        clear_button = QPushButton("Очистить всё")
        clear_button.clicked.connect(self.clear_all)
        export_button = QPushButton("Экспорт таблицы в PNG")
        export_button.clicked.connect(self.export_png)
        layout.addWidget(calc_button)
        layout.addWidget(clear_button)
        layout.addWidget(export_button)
        layout.addStretch(1)
        return panel

    def _button_group(self, title, labels, columns):
        box = QGroupBox(title)
        grid = QGridLayout(box)
        for i, text in enumerate(labels):
            button = QPushButton(text)
            button.clicked.connect(lambda checked=False, t=text: self.insert_text(t))
            grid.addWidget(button, i // columns, i % columns)
        return box

    def _build_results_panel(self):
        self.results = QTabWidget()

        self.table = QTableWidget()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results.addTab(self.table, "Таблица истинности")

        self.forms_text = self._read_only_text()
        self.results.addTab(self.forms_text, "СДНФ и СКНФ")

        self.min_text = self._read_only_text()
        self.results.addTab(self.min_text, "Минимизация")

        self.karnaugh = KarnaughWidget()
        self.results.addTab(self.karnaugh, "Карта Карно")

        # Вкладка схемы будет заполнена в следующем коммите
        stub = QLabel("«Схема» появится позже")
        stub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.results.addTab(stub, "Схема")
        return self.results

    @staticmethod
    def _read_only_text():
        text = QTextEdit()
        text.setReadOnly(True)
        text.setStyleSheet("font-size: 15px;")
        return text

    # ---------- действия ----------

    def insert_text(self, text):
        """Вставляет операцию или переменную в позицию курсора."""
        if text in ("(", ")"):
            self.input.insert(text)
        else:
            self.input.insert(f" {text} ")
        self.input.setFocus()

    def calculate(self):
        text = self.input.text()
        if not text.strip():
            QMessageBox.warning(self, "Ошибка в выражении", "Введите выражение.")
            return
        try:
            node = parse(text)
        except ExpressionError as e:
            QMessageBox.warning(self, "Ошибка в выражении", str(e))
            return

        table = build_truth_table(node)
        self.last_table = table
        self.last_expression = " ".join(text.split())
        self._show_table(table)
        self._show_forms(table)
        result = minimize_table(table)
        self._show_minimization(result)
        self._show_karnaugh(table, result)

    def clear_all(self):
        self.input.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.forms_text.clear()
        self.min_text.clear()
        self.karnaugh.clear()
        self.last_table = None
        self.last_expression = ""
        self.input.setFocus()

    # ---------- вывод результатов ----------

    def _show_table(self, table):
        names = table.variables + ["F"]
        self.table.setRowCount(len(table.rows))
        self.table.setColumnCount(len(names))
        self.table.setHorizontalHeaderLabels(names)
        for r, (row, result) in enumerate(zip(table.rows, table.results)):
            for c, value in enumerate(list(row) + [result]):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if c == len(row) and result == 1:
                    item.setBackground(QColor("#e2f0d9"))
                self.table.setItem(r, c, item)

    def _show_forms(self, table):
        self.forms_text.setPlainText(
            f"Функция F = {self.last_expression}\n\n"
            f"СДНФ:\n{sdnf(table)}\n\n"
            f"СКНФ:\n{sknf(table)}"
        )

    def _show_minimization(self, result):
        implicants = ", ".join(result.implicants) if result.implicants else "нет"
        self.min_text.setPlainText(
            f"Минимальная ДНФ:\n{result.expression}\n\n"
            f"Слагаемых: {len(result.terms)}, литералов: {result.literal_count}\n"
            f"Выбранные импликанты (- означает, что переменная не входит): {implicants}"
        )

    def _show_karnaugh(self, table, result):
        if not 2 <= len(table.variables) <= 4:
            self.karnaugh.show_message("Карта Карно строится для функций от 2 до 4 переменных.")
            return
        kmap = build_karnaugh_map(table)
        groups = []
        for implicant, term in zip(result.implicants, result.terms):
            text = " AND ".join(name if positive else f"NOT {name}" for name, positive in term)
            groups.append((implicant, text or "1"))
        self.karnaugh.set_data(kmap, groups)

    # ---------- экспорт ----------

    def export_png(self):
        if self.last_table is None:
            QMessageBox.warning(self, "Экспорт", "Сначала рассчитайте таблицу истинности.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить таблицу истинности", "truth_table.png", "Изображение PNG (*.png)")
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"
        image = render_table_image(self.last_table, self.last_expression)
        if image.save(path):
            QMessageBox.information(self, "Экспорт завершён", f"Таблица сохранена:\n{path}")
        else:
            QMessageBox.warning(self, "Ошибка экспорта", f"Не удалось сохранить файл:\n{path}")
