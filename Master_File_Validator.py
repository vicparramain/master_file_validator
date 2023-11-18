import sys
import os
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import QTimer
from lxml import etree
import json
import polib
import ruamel.yaml

# Define constants
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400

class FileValidator(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Master File Validator")
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)

        self.layout = QtWidgets.QVBoxLayout()

        self.path_layout = QtWidgets.QHBoxLayout()

        self.path_input = QtWidgets.QLineEdit()
        self.path_input.setPlaceholderText("Path to files (JSON, PO, XML, XLIFF, XLF, YAML, YML)")
        self.path_input.setStyleSheet(
            """
            padding: 6px;
            border: 2px solid #ccc;
            border-radius: 4px;
            font-size: 10px;
            """
        )
        self.path_layout.addWidget(self.path_input)

        # Connect the returnPressed signal to the validate_file method
        self.path_input.returnPressed.connect(self.validate_file)

        self.browse_button = QtWidgets.QPushButton("...")
        self.browse_button.setStyleSheet(
            """
            padding: 6px;
            background-color: #A9A9A9;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 10px;
            """
        )
        self.browse_button.clicked.connect(self.browse_directory)
        self.browse_button.clicked.connect(self.set_button_down)
        self.path_layout.addWidget(self.browse_button)

        self.validate_button = QtWidgets.QPushButton("Validate")
        self.validate_button.setStyleSheet(
            """
            padding: 6px;
            background-color: green;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 10px;
            """
        )
        self.validate_button.clicked.connect(self.validate_file)
        self.validate_button.clicked.connect(self.set_button_down)
        self.path_layout.addWidget(self.validate_button)

        self.export_button = QtWidgets.QPushButton("Export results")
        self.export_button.setStyleSheet(
            """
            padding: 6px;
            background-color: blue;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 10px;
            """
        )
        self.export_button.clicked.connect(self.export_results)
        self.path_layout.addWidget(self.export_button)

        self.layout.addLayout(self.path_layout)

        self.progress_bar = QtWidgets.QProgressBar(self)
        self.layout.addWidget(self.progress_bar)

        self.result_text = QtWidgets.QTextEdit()
        self.result_text.setStyleSheet(
            """
            border: 2px solid #ccc;
            border-radius: 4px;
            font-size: 10px;
            """
        )
        self.result_text.setReadOnly(True)
        self.layout.addWidget(self.result_text)

        # Set the window icon
        icon_path = 'C:\Work\Scripts\compile_2\icono.ico'
        self.setWindowIcon(QtGui.QIcon(icon_path))

        self.setLayout(self.layout)

    def browse_directory(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.path_input.setText(directory)

    def validate_file(self):
        input_path = self.path_input.text()
        validation_results = self.process_directory(input_path)

        self.result_text.clear()
        self.display_validation_results(validation_results)

    def export_results(self):
        validation_results = self.result_text.toPlainText()
        input_path = self.path_input.text()

        if validation_results:
            export_path = os.path.join(input_path, "validation_report.txt")
            with open(export_path, "w") as txt_file:
                txt_file.write(validation_results)

    def process_directory(self, directory_path):
        # Strip trailing spaces from the directory path
        directory_path = directory_path.rstrip()

        validation_results = ""
        file_count = 0

        valid_extensions = (".json", ".xml", ".xliff", ".xlf", ".po", ".yaml", ".yml")

        for root, _, files in os.walk(directory_path):
            for filename in files:
                if filename.endswith(valid_extensions):
                    file_count += 1

        self.progress_bar.setMaximum(file_count)
        self.progress_bar.setValue(0)

        for root, _, files in os.walk(directory_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                extension = os.path.splitext(file_path)[1].lower()
                if extension in valid_extensions:
                    validation_result = self.validate_file_by_extension(file_path, extension)
                    validation_results += f"{file_path}: {validation_result}\n"
                    self.progress_bar.setValue(self.progress_bar.value() + 1)

        return validation_results

    def validate_file_by_extension(self, file_path, extension):
        try:
            if extension == ".json":
                with open(file_path, "r", encoding="utf-8") as json_file:
                    json.load(json_file)
                return "JSON file is valid"
            elif extension == ".xml":
                with open(file_path, "rb") as xml_file:
                    etree.fromstring(xml_file.read())
                return "XML file is valid"
            elif extension in (".xliff", ".xlf"):
                with open(file_path, "r", encoding="utf-8") as xliff_file:
                    etree.fromstring(xliff_file.read())
                return "XLIFF file is valid"
            elif extension == ".po":
                po = polib.pofile(file_path)
                return "PO file is valid"
            elif extension in (".yaml", ".yml"):
                with open(file_path, "r", encoding="utf-8") as yaml_file:
                    ruamel.yaml.safe_load(yaml_file)
                return "YAML file is valid"
            else:
                return "Unsupported file format"
        except Exception as e:
            return f"Invalid {extension.upper()}: {str(e)}"

    def display_validation_results(self, validation_results):
        results = validation_results.split("\n")

        self.result_text.clear()

        for result in results:
            if "Invalid" in result:
                self.result_text.insertHtml(f'<font color="red">{result}</font><br>')
            else:
                self.result_text.insertHtml(f'<font color="green">{result}</font><br>')

    def set_button_down(self):
        sender = self.sender()
        if sender:
            sender.setDown(True)

            QTimer.singleShot(100, lambda: sender.setDown(False))


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    window = FileValidator()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
