"""
Validation Worker
Contains the background thread logic for performing file validation.
"""

import os
import json
import logging
from lxml import etree
import polib
import ruamel.yaml

from PySide6.QtCore import QObject, QRunnable, Signal

class WorkerSignals(QObject):
    """
    Defines signals available from a running worker thread.
    """
    progress_max_set = Signal(int)
    file_processed = Signal(str, list)
    finished = Signal()
    error = Signal(str, str)

class ValidatorWorker(QRunnable):
    """
    Worker thread for handling file validation.
    """
    def __init__(self, directory_path: str, dtd_paths_str: str | None, allow_bom: bool = False):
        super().__init__()
        self.directory_path = directory_path.rstrip()
        self.dtd_paths = [path.strip() for path in dtd_paths_str.split(';') if path.strip()] if dtd_paths_str else []
        self.allow_bom = allow_bom
        self.signals = WorkerSignals()
        self.dtds = []
        self.recovering_parser = etree.XMLParser(recover=True, dtd_validation=False)

    def run(self):
        """
        Main worker logic. Scans for files and validates them.
        """
        try:
            files_to_validate = []
            valid_extensions = (".json", ".xml", ".xliff", ".xlf", ".po", ".yaml", ".yml", ".dita")

            for root, _, files in os.walk(self.directory_path):
                for filename in files:
                    extension = os.path.splitext(filename)[1].lower()
                    if extension in valid_extensions:
                        file_path = os.path.join(root, filename)
                        files_to_validate.append((file_path, extension))

            self.signals.progress_max_set.emit(len(files_to_validate))

            if self.dtd_paths:
                for dtd_path in self.dtd_paths:
                    if not os.path.isfile(dtd_path):
                        self.signals.file_processed.emit(f"DTD: {os.path.basename(dtd_path)}", ["Error: File not found"])
                    else:
                        try:
                            with open(dtd_path, "rb") as f:
                                dtd_obj = etree.DTD(f)
                            self.dtds.append(dtd_obj)
                            self.signals.file_processed.emit(f"DTD: {os.path.basename(dtd_path)}", ["Successfully loaded"])
                        except Exception as e:
                            self.signals.file_processed.emit(f"DTD: {os.path.basename(dtd_path)}", [f"Error parsing DTD: {e}"])

            for file_path, extension in files_to_validate:
                results = self._validate_file(file_path, extension)
                self.signals.file_processed.emit(file_path, results)

        except Exception as e:
            logging.error(f"Critical worker error: {e}", exc_info=True)
            self.signals.error.emit("Worker Error", f"An unexpected error occurred: {e}")
        finally:
            self.signals.finished.emit()

    def _validate_file(self, file_path: str, extension: str) -> list[str]:
        """
        Validates a single file, returning a list of result messages.
        """
        try:
            if extension == ".json":
                json_encoding = "utf-8-sig" if self.allow_bom else "utf-8"
                with open(file_path, "r", encoding=json_encoding) as json_file:
                    json.load(json_file)
                return ["Valid JSON"]

            elif extension in (".xml", ".dita", ".xliff", ".xlf"):
                error_messages = []
                with open(file_path, "rb") as f:
                    doc = etree.parse(f, self.recovering_parser)

                for error in self.recovering_parser.error_log:
                    if "EntityRef: expecting" in error.message:
                         msg = f"L{error.line}, C{error.column}: Unescaped ampersand '&' must be written as '&amp;'."
                    else:
                        msg = f"L{error.line}, C{error.column}: {error.message}"
                    error_messages.append(msg)

                if not error_messages and self.dtds:
                    is_dtd_valid = False
                    last_dtd_errors = []
                    for dtd in self.dtds:
                        if dtd.validate(doc):
                            is_dtd_valid = True
                            last_dtd_errors.clear()
                            break
                        else:
                            last_dtd_errors = [f"L{e.line}, C{e.column}: {e.message}" for e in dtd.error_log]

                    if not is_dtd_valid:
                        error_messages.extend(last_dtd_errors)

                if error_messages:
                    return error_messages

                if self.dtds:
                    return ["Valid and DTD compliant"]
                else:
                    return ["Valid"]

            elif extension == ".po":
                polib.pofile(file_path)
                return ["Valid PO"]

            elif extension in (".yaml", ".yml"):
                yaml_encoding = "utf-8-sig" if self.allow_bom else "utf-8"
                yaml = ruamel.yaml.YAML(typ='safe')
                with open(file_path, "r", encoding=yaml_encoding) as yaml_file:
                    yaml.load(yaml_file)
                return ["Valid YAML"]

            else:
                return ["Unsupported file format"]

        except Exception as e:
            return [f"Critical Error: {e}"]
