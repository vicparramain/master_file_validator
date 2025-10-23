"""
Main Window
Contains the FileValidator class, which defines the main application GUI.
"""

import sys
import os
import logging
import html
import platform
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, QTimer, QSize, Qt
from PySide6.QtGui import QIcon, QPalette, QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLineEdit, QPushButton, QFileDialog, QProgressBar,
    QLabel, QFrame, QToolButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox
)

# Local project imports
from config import WINDOW_WIDTH, WINDOW_HEIGHT, ICONS_DIR
from validator import ValidatorWorker
from ui_widgets import DragDropLineEdit, DragDropDtdInput
import theme as theme_manager

class FileValidator(QtWidgets.QWidget):
    """
    The main application window, handling UI layout, interactions,
    and coordinating the validation worker.
    """
    def __init__(self):
        super().__init__()
        self.current_theme = theme_manager.detect_system_theme()
        self.threadpool = QThreadPool()

        self.initUI()
        self.apply_stylesheet(self.current_theme)

        self.theme_change_timer = QTimer(self)
        self.theme_change_timer.timeout.connect(self._check_and_apply_theme_changes)
        self.theme_change_timer.start(2000)

    def initUI(self):
        """Initializes all UI components and layouts."""
        self.setWindowTitle("Master File Validator")
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(8)

        # Input Card
        input_frame = QFrame()
        input_frame.setObjectName("card")

        grid_layout = QGridLayout(input_frame)
        grid_layout.setSpacing(8)

        # Directory Path
        self.path_input = DragDropLineEdit()
        self.path_input.setPlaceholderText("Path to files (JSON, PO, XML, XLIFF, XLF, YAML, YML, DITA)")
        grid_layout.addWidget(self.path_input, 0, 0)

        self.browse_button = QtWidgets.QToolButton()
        self.browse_button.setIcon(self._get_icon("folder"))
        self.browse_button.setToolTip("Browse for directory...")
        self.browse_button.setAutoRaise(True)
        self.browse_button.clicked.connect(self.browse_directory)
        grid_layout.addWidget(self.browse_button, 0, 1)

        # DTD Path
        self.dtd_input = DragDropDtdInput()
        self.dtd_input.setPlaceholderText("Optional: Select/Drop DTD file(s) or folder(s)")
        grid_layout.addWidget(self.dtd_input, 1, 0)

        self.browse_dtd_button = QtWidgets.QToolButton()
        self.browse_dtd_button.setIcon(self._get_icon("dtd"))
        self.browse_dtd_button.setToolTip("Browse for DTD file(s)...")
        self.browse_dtd_button.setAutoRaise(True)
        self.browse_dtd_button.clicked.connect(self.browse_dtd_files)
        grid_layout.addWidget(self.browse_dtd_button, 1, 1)

        # BOM Checkbox
        self.bom_checkbox = QtWidgets.QCheckBox("Allow UTF-8 BOM (for JSON/YAML)")
        self.bom_checkbox.setToolTip("If checked, JSON and YAML files starting with a Byte Order Mark (BOM) will be processed correctly.")
        grid_layout.addWidget(self.bom_checkbox, 2, 0)

        # Control Buttons
        self.validate_button = QtWidgets.QPushButton("Run")
        self.validate_button.setIcon(self._get_icon("run"))
        self.validate_button.setObjectName("runButton")
        self.validate_button.clicked.connect(self.start_validation)
        grid_layout.addWidget(self.validate_button, 0, 2)

        self.export_button = QtWidgets.QPushButton("Export")
        self.export_button.setIcon(self._get_icon("export"))
        self.export_button.clicked.connect(self.export_results)
        grid_layout.addWidget(self.export_button, 1, 2)

        grid_layout.setColumnStretch(0, 1)
        self.layout.addWidget(input_frame)

        # Results Table
        self.result_table = QtWidgets.QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["Path", "Filename", "Details"])
        header = self.result_table.horizontalHeader()

        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)

        self.result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.verticalHeader().setVisible(False)
        self.result_table.setWordWrap(True)
        self.result_table.setSortingEnabled(True)

        self.layout.addWidget(self.result_table, 1)

        # Progress Bar
        self.progress_container = QWidget()
        progress_layout = QHBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, 5, 0, 0)

        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setTextVisible(False)
        progress_layout.addWidget(self.progress_bar, 1)

        self.progress_label = QLabel("")
        progress_layout.addWidget(self.progress_label, 0)

        self.layout.addWidget(self.progress_container)
        self.progress_container.hide()

        self.setWindowIcon(self._get_icon("app"))
        self.setLayout(self.layout)

    def browse_directory(self):
        """Opens a dialog to select the main validation directory."""
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.path_input.setText(directory)

    def browse_dtd_files(self):
        """Opens a dialog to select one or more DTD files."""
        dtd_files, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Select DTD File(s)", "", "DTD Files (*.dtd);;All Files (*)")
        if dtd_files:
            current_paths = {p.strip() for p in self.dtd_input.text().split(';') if p.strip()}
            new_paths = set(dtd_files)
            all_paths = sorted(list(current_paths.union(new_paths)))
            self.dtd_input.setText(";".join(all_paths))

    def start_validation(self):
        """Begins the validation process in a worker thread."""
        input_path = self.path_input.text()
        if not input_path or not os.path.isdir(input_path):
            self.on_error("Input Error", "Please select a valid directory to validate.")
            return

        self.result_table.setRowCount(0)
        self.progress_container.show()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Scanning files...")
        self.validate_button.setEnabled(False)
        self.export_button.setEnabled(False)

        allow_bom = self.bom_checkbox.isChecked()
        worker = ValidatorWorker(input_path, self.dtd_input.text(), allow_bom)

        worker.signals.progress_max_set.connect(self.on_progress_max_set)
        worker.signals.file_processed.connect(self.on_file_processed)
        worker.signals.finished.connect(self.on_validation_finished)
        worker.signals.error.connect(self.on_error)

        self.threadpool.start(worker)

    def export_results(self):
        """Exports the contents of the results table to an HTML file."""
        if self.result_table.rowCount() == 0:
            self.on_error("Export Error", "There are no results to export.")
            return

        default_path = os.path.join(self.path_input.text(), "validation_report.html")
        export_path, _ = QFileDialog.getSaveFileName(self, "Save Report", default_path, "HTML Files (*.html)")

        if not export_path:
            return

        try:
            html_content = self._generate_html_report()
            with open(export_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            self.progress_label.setText(f"Report saved!")
        except Exception as e:
            self.on_error("Export Failed", f"Could not save the report: {e}")

    def _generate_html_report(self) -> str:
        """Constructs the HTML report string from table data."""
        html_parts = [
            "<!DOCTYPE html><html><head><title>Validation Report</title><style>",
            "body { font-family: sans-serif; }",
            "table { border-collapse: collapse; width: 100%; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }",
            "th { background-color: #f2f2f2; }",
            ".status { font-weight: bold; }",
            ".valid { color: #28a745; }",
            ".invalid { color: #dc3545; }",
            ".info { color: #17a2b8; }",
            ".error { color: #dc3545; }",
            "tr.valid-row { background-color: #e9f5e9; }",
            "tr.invalid-row { background-color: #fbe9e9; }",
            "ul { margin: 0; padding-left: 20px; }",
            "</style></head><body><h1>Validation Report</h1><table>",
            "<thead><tr><th>Path</th><th>Filename</th><th>Details</th></tr></thead><tbody>"
        ]

        for row in range(self.result_table.rowCount()):
            path = self.result_table.item(row, 0).text()
            filename = self.result_table.item(row, 1).text()
            details_text = self.result_table.item(row, 2).text()

            if "Valid" in details_text:
                row_class = "valid-row"
            else:
                row_class = "invalid-row"

            html_parts.append(f"<tr class='{row_class}'>")
            html_parts.append(f"<td>{html.escape(path)}</td>")
            html_parts.append(f"<td>{html.escape(filename)}</td>")

            details_list = [f"<li>{html.escape(line)}</li>" for line in details_text.split('\n') if line]
            details_html = f"<ul>{''.join(details_list)}</ul>" if len(details_list) > 1 else html.escape(details_text)

            html_parts.append(f"<td>{details_html}</td>")
            html_parts.append("</tr>")

        html_parts.append("</tbody></table></body></html>")
        return "".join(html_parts)

    def on_progress_max_set(self, max_value: int):
        """Slot for 'progress_max_set' signal."""
        self.progress_bar.setRange(0, max_value)
        self.progress_bar.setValue(0)
        self.progress_label.setText(f"0 / {max_value}")

    def on_file_processed(self, file_path: str, results: list[str]):
        """Slot for 'file_processed' signal. Adds a row to the table."""
        is_special_message = file_path.startswith("DTD:")

        if is_special_message:
            is_ok = "Error" not in results[0]
            dir_path = "System Message"
            filename = file_path
        else:
            is_ok = len(results) == 1 and any(s in results[0] for s in ["Valid", "compliant"])
            dir_path = os.path.dirname(file_path)
            filename = os.path.basename(file_path)

        row_position = self.result_table.rowCount()
        self.result_table.insertRow(row_position)

        if self.current_theme == 'dark':
            row_color = QColor("#1e4a2a") if is_ok else QColor("#5a2a2a")
        else:
            row_color = QColor("#d4edda") if is_ok else QColor("#f8d7da")

        path_item = QTableWidgetItem(dir_path)
        filename_item = QTableWidgetItem(filename)
        details_item = QTableWidgetItem("\n".join(results))

        items = [path_item, filename_item, details_item]
        for i, item in enumerate(items):
            item.setBackground(row_color)
            self.result_table.setItem(row_position, i, item)

        self.result_table.resizeRowsToContents()
        self.result_table.scrollToBottom()

        if not is_special_message:
            current_val = self.progress_bar.value() + 1
            self.progress_bar.setValue(current_val)
            self.progress_label.setText(f"{current_val} / {self.progress_bar.maximum()}")

    def on_validation_finished(self):
        """Slot for 'finished' signal."""
        total = self.progress_bar.maximum()
        self.progress_label.setText(f"100%")
        self.progress_bar.setValue(total)
        self.validate_button.setEnabled(True)
        self.export_button.setEnabled(True)

        self.result_table.resizeColumnsToContents()
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)

    def on_error(self, title: str, message: str):
        """Slot for 'error' signal. Displays a critical error message."""
        logging.error(f"{title}: {message}")
        self.progress_label.setText(f"Error!")
        QtWidgets.QMessageBox.critical(self, title, message)
        self.validate_button.setEnabled(True)
        self.export_button.setEnabled(True)

    def _get_icon(self, name: str) -> QIcon:
        """Gets a theme-aware icon."""
        variant = "dark" if self.current_theme == "dark" else "light"
        icon_path = os.path.join(ICONS_DIR, f"{name}_{variant}.svg")
        return QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

    def _check_and_apply_theme_changes(self):
        """Polls for system theme changes and updates UI."""
        new_detected_theme = theme_manager.detect_system_theme()
        if new_detected_theme != self.current_theme:
            self.current_theme = new_detected_theme
            self.apply_stylesheet(self.current_theme)

            self.setWindowIcon(self._get_icon("app"))
            self.browse_button.setIcon(self._get_icon("folder"))
            self.browse_dtd_button.setIcon(self._get_icon("dtd"))
            self.validate_button.setIcon(self._get_icon("run"))
            self.export_button.setIcon(self._get_icon("export"))

    def _style_run_button_dynamically(self):
        """Applies accent color to the 'run' button."""
        if not QApplication.instance(): return
        palette = QApplication.instance().palette()
        accent = palette.color(QPalette.ColorRole.Highlight)
        text = palette.color(QPalette.ColorRole.HighlightedText)
        hover = accent.lighter(120) if self.current_theme == "dark" else accent.darker(120)
        self.validate_button.setStyleSheet(
            f"QPushButton#runButton {{ background-color: {accent.name()}; color: {text.name()}; border: 1px solid {accent.name()}; font-weight: bold; }}"
            f"QPushButton#runButton:hover {{ background-color: {hover.name()}; border: 1px solid {hover.name()}; }}"
        )

    def apply_stylesheet(self, theme_name: str):
        """Applies the full QSS stylesheet."""
        app_palette = QPalette()
        windows_accent_hex = theme_manager.get_windows_accent_color_explorer_hex()
        highlight_color_chosen = False

        if windows_accent_hex:
            accent_qcolor = QColor(windows_accent_hex)
            if accent_qcolor.isValid():
                app_palette.setColor(QPalette.ColorRole.Highlight, accent_qcolor)
                luminance = (0.299 * accent_qcolor.red() + 0.587 * accent_qcolor.green() + 0.114 * accent_qcolor.blue()) / 255
                app_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black if luminance > 0.5 else Qt.GlobalColor.white)
                highlight_color_chosen = True

        if not highlight_color_chosen:
            default_highlight = QColor("#0078d7") if theme_name == "light" else QColor("#388bfd")
            app_palette.setColor(QPalette.ColorRole.Highlight, default_highlight)
            app_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)

        if theme_name == "dark":
            base_colors = {
                QPalette.ColorRole.Window: "#2b2b2b", QPalette.ColorRole.WindowText: "#e0e0e0",
                QPalette.ColorRole.Base: "#222222", QPalette.ColorRole.Text: "#e0e0e0",
                QPalette.ColorRole.Button: "#3a3a3a", QPalette.ColorRole.ButtonText: "#e0e0e0",
                QPalette.ColorRole.Midlight: "#444444", QPalette.ColorRole.Light: "#555555",
                QPalette.ColorRole.Dark: "#1e1e1e"
            }
        else:
            base_colors = {
                QPalette.ColorRole.Window: "#f0f0f0", QPalette.ColorRole.WindowText: "#000000",
                QPalette.ColorRole.Base: "#ffffff", QPalette.ColorRole.Text: "#000000",
                QPalette.ColorRole.Button: "#e0e0e0", QPalette.ColorRole.ButtonText: "#000000",
                QPalette.ColorRole.Midlight: "#dcdcdc", QPalette.ColorRole.Light: "#c0c0c0",
                QPalette.ColorRole.Dark: "#a0a0a0"
            }
        for role, color in base_colors.items():
            app_palette.setColor(role, QColor(color))

        if QApplication.instance():
            QApplication.instance().setPalette(app_palette)

        checkmark_icon_path = f"icons/check_dark.svg" if theme_name == "dark" else f"icons/check_light.svg"
        checkmark_icon_path = checkmark_icon_path.replace("\\", "/")

        self.setStyleSheet(theme_manager.get_stylesheet(checkmark_icon_path))
        self._style_run_button_dynamically()
