"""
Main window GUI for the Job Instruction Downloader application.
"""

import logging
from typing import Dict, Any, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QPushButton, QProgressBar,
    QLabel, QTextEdit, QSplitter, QGroupBox,
    QStatusBar, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction

GUI_FRAMEWORK = "PyQt6"


class MainWindow(QMainWindow):
    """Main application window."""

    download_started = pyqtSignal()
    download_paused = pyqtSignal()
    download_stopped = pyqtSignal()

    def __init__(self, config: Dict[str, Any], parent: Optional[QWidget] = None):
        """Initialize main window.

        Args:
            config: Application configuration dictionary.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()

        self.is_downloading = False
        self.is_paused = False

        self.logger.info(f"Main window initialized using {GUI_FRAMEWORK}")

    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Job Instruction Downloader v1.0")
        self.setGeometry(100, 100, 1200, 800)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        left_panel = self.create_sources_panel()
        splitter.addWidget(left_panel)

        right_panel = self.create_control_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([400, 800])

    def create_sources_panel(self) -> QWidget:
        """Create the sources selection panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        sources_group = QGroupBox("Источники данных")
        sources_layout = QVBoxLayout(sources_group)

        self.sources_tree = QTreeWidget()
        self.sources_tree.setHeaderLabels(["Источник", "Документы"])
        self.sources_tree.setRootIsDecorated(True)

        self.populate_sources_tree()

        sources_layout.addWidget(self.sources_tree)
        layout.addWidget(sources_group)

        return panel

    def create_control_panel(self) -> QWidget:
        """Create the control and progress panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        control_group = QGroupBox("Управление процессом")
        control_layout = QVBoxLayout(control_group)

        button_layout = QHBoxLayout()

        self.start_button = QPushButton("Старт")
        self.pause_button = QPushButton("Пауза")
        self.stop_button = QPushButton("Стоп")

        self.start_button.clicked.connect(self.start_download)
        self.pause_button.clicked.connect(self.pause_download)
        self.stop_button.clicked.connect(self.stop_download)

        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.stop_button)

        control_layout.addLayout(button_layout)

        progress_layout = QVBoxLayout()

        self.overall_progress_label = QLabel("Общий прогресс:")
        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setRange(0, 100)

        progress_layout.addWidget(self.overall_progress_label)
        progress_layout.addWidget(self.overall_progress_bar)

        self.current_progress_label = QLabel("Текущий ресурс:")
        self.current_progress_bar = QProgressBar()
        self.current_progress_bar.setRange(0, 100)

        progress_layout.addWidget(self.current_progress_label)
        progress_layout.addWidget(self.current_progress_bar)

        self.stats_label = QLabel("Скорость: 0 файлов/мин\nОсталось: --")

        progress_layout.addWidget(self.stats_label)

        control_layout.addLayout(progress_layout)
        layout.addWidget(control_group)

        log_group = QGroupBox("Журнал событий")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)

        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group)

        return panel

    def populate_sources_tree(self):
        """Populate the sources tree with sample data."""
        consultant_item = QTreeWidgetItem(self.sources_tree)
        consultant_item.setText(0, "Consultant.ru")
        consultant_item.setText(1, "63 документа")
        consultant_item.setCheckState(0, Qt.CheckState.Checked)

        departments = [
            ("ПЛАНОВО-ЭКОНОМИЧЕСКИЙ ОТДЕЛ", "15"),
            ("ФИНАНСОВЫЙ ОТДЕЛ", "10"),
            ("КОНТРАКТНАЯ СЛУЖБА", "7"),
            ("ОТДЕЛ ОРГАНИЗАЦИИ", "14"),
            ("ОХРАНА ТРУДА", "17")
        ]

        for dept_name, count in departments:
            dept_item = QTreeWidgetItem(consultant_item)
            dept_item.setText(0, dept_name)
            dept_item.setText(1, count)
            dept_item.setCheckState(0, Qt.CheckState.Checked)

        consultant_item.setExpanded(True)

    def setup_menu(self):
        """Setup the menu bar."""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("Файл")

        settings_action = QAction("Настройки", self)
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        resources_menu = menubar.addMenu("Ресурсы")

        add_resource_action = QAction("Добавить ресурс", self)
        add_resource_action.triggered.connect(self.add_resource)
        resources_menu.addAction(add_resource_action)

        help_menu = menubar.addMenu("Справка")

        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_status_bar(self):
        """Setup the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе")

    def start_download(self):
        """Start the download process."""
        if not self.is_downloading:
            self.is_downloading = True
            self.is_paused = False

            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)

            self.status_bar.showMessage("Загрузка...")
            self.log_message("Начата загрузка документов")

            self.download_started.emit()

    def pause_download(self):
        """Pause/resume the download process."""
        if self.is_downloading:
            self.is_paused = not self.is_paused

            if self.is_paused:
                self.pause_button.setText("Продолжить")
                self.status_bar.showMessage("Приостановлено")
                self.log_message("Загрузка приостановлена")
            else:
                self.pause_button.setText("Пауза")
                self.status_bar.showMessage("Загрузка...")
                self.log_message("Загрузка возобновлена")

            self.download_paused.emit()

    def stop_download(self):
        """Stop the download process."""
        if self.is_downloading:
            self.is_downloading = False
            self.is_paused = False

            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.pause_button.setText("Пауза")

            self.status_bar.showMessage("Остановлено")
            self.log_message("Загрузка остановлена")

            self.download_stopped.emit()

    def log_message(self, message: str):
        """Add a message to the log output."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)
        self.logger.info(message)

    def show_settings(self):
        """Show settings dialog."""
        QMessageBox.information(self, "Настройки", "Диалог настроек будет реализован в следующей версии")

    def add_resource(self):
        """Show add resource dialog."""
        QMessageBox.information(
            self, "Добавить ресурс", "Мастер добавления ресурсов будет реализован в следующей версии"
        )

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "О программе",
            "Job Instruction Downloader v1.0\n\n"
            "Универсальное приложение для автоматизации\n"
            "скачивания документов с веб-ресурсов.\n\n"
            "© 2025 CoreTwin"
        )
