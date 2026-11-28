"""Главное окно: вкладки «Конструктор» и «Тренажёр»."""
from PySide6.QtWidgets import QMainWindow, QTabWidget

from .constructor_view import ConstructorView
from .trainer_view import TrainerView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BoolTrainer — тренажёр по булевым функциям")
        self.resize(1100, 680)

        tabs = QTabWidget()
        tabs.addTab(ConstructorView(), "Конструктор")
        tabs.addTab(TrainerView(), "Тренажёр")
        self.setCentralWidget(tabs)
