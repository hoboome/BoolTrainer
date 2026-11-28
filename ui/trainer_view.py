"""Вкладка «Тренажёр»: теория по темам и случайные задания с проверкой ответа."""
import os
import random

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.tasks import check_answer, generate_task, load_theory

THEORY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "theory.json")
GREEN = "color: #2e7d32; font-size: 15px;"
RED = "color: #c62828; font-size: 15px;"
# Такие сообщения означают ошибку записи ответа, а не неверный ответ: попытка не засчитывается
FORMAT_ERRORS = ("Ошибка в записи", "Нужно ввести")


class TrainerView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.topics = []
        self.task = None
        self.answered = False
        self.correct_count = 0
        self.total_count = 0
        self.rng = random.Random()
        self._build_ui()
        self._load_topics()

    # ---------- построение интерфейса ----------

    def _build_ui(self):
        root = QHBoxLayout(self)

        self.topic_list = QListWidget()
        self.topic_list.setFixedWidth(260)
        self.topic_list.currentRowChanged.connect(self._on_topic_changed)
        root.addWidget(self.topic_list, 0)

        right = QVBoxLayout()
        self.title_label = QLabel("")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.theory_label = QLabel("")
        self.theory_label.setWordWrap(True)
        self.theory_label.setStyleSheet("font-size: 15px;")
        self.prompt_label = QLabel("")
        self.prompt_label.setWordWrap(True)
        self.prompt_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.answer_edit = QLineEdit()
        self.answer_edit.setStyleSheet("font-size: 16px; padding: 4px;")
        self.answer_edit.returnPressed.connect(self.check)

        buttons = QHBoxLayout()
        self.check_button = QPushButton("Проверить")
        self.check_button.clicked.connect(self.check)
        self.new_button = QPushButton("Новое задание")
        self.new_button.clicked.connect(self.new_task)
        buttons.addWidget(self.check_button)
        buttons.addWidget(self.new_button)

        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        self.score_label = QLabel("")
        self.score_label.setStyleSheet("font-size: 14px; color: #555555;")
        self._update_score()

        for widget in (self.title_label, self.theory_label, self.prompt_label,
                       self.answer_edit):
            right.addWidget(widget)
        right.addLayout(buttons)
        right.addWidget(self.result_label)
        right.addStretch(1)
        right.addWidget(self.score_label)
        root.addLayout(right, 1)

    def _load_topics(self):
        try:
            self.topics = load_theory(THEORY_PATH)
        except (OSError, ValueError) as e:
            self.theory_label.setText(f"Не удалось загрузить теорию: {e}")
            self.check_button.setEnabled(False)
            self.new_button.setEnabled(False)
            return
        for topic in self.topics:
            self.topic_list.addItem(topic["title"])
        self.topic_list.setCurrentRow(0)

    # ---------- действия ----------

    def _on_topic_changed(self, row):
        if row < 0 or row >= len(self.topics):
            return
        topic = self.topics[row]
        self.title_label.setText(topic["title"])
        self.theory_label.setText("\n\n".join(topic["text"]))
        self.new_task()

    def new_task(self):
        row = self.topic_list.currentRow()
        if row < 0 or row >= len(self.topics):
            return
        kind = self.rng.choice(self.topics[row]["tasks"])
        self.task = generate_task(kind, self.rng)
        self.answered = False
        self.prompt_label.setText(self.task.prompt)
        if kind == "table":
            self.answer_edit.setPlaceholderText("Например: 0110")
        else:
            self.answer_edit.setPlaceholderText("Введите выражение, например: (NOT A AND B) OR A")
        self.answer_edit.clear()
        self.answer_edit.setEnabled(True)
        self.check_button.setEnabled(True)
        self.result_label.setText("")
        self.answer_edit.setFocus()

    def check(self):
        if self.task is None or self.answered:
            return
        text = self.answer_edit.text()
        if not text.strip():
            self._show_result("Введите ответ.", ok=False)
            return

        result = check_answer(self.task, text)
        if result.message.startswith(FORMAT_ERRORS):
            self._show_result(result.message, ok=False)   # попытка не засчитывается
            return

        self.answered = True
        self.total_count += 1
        if result.correct:
            self.correct_count += 1
            self._show_result(result.message, ok=True)
        else:
            self._show_result(f"{result.message}\nПравильный ответ: {result.correct_answer}", ok=False)
        self.answer_edit.setEnabled(False)
        self.check_button.setEnabled(False)
        self._update_score()

    def _show_result(self, message, ok):
        self.result_label.setStyleSheet(GREEN if ok else RED)
        self.result_label.setText(message)

    def _update_score(self):
        self.score_label.setText(
            f"Верных ответов за сеанс: {self.correct_count} из {self.total_count}")
