"""
Custom UI Widgets
Contains custom PySide6 widgets used in the application.
"""

import os
from PySide6 import QtGui, QtWidgets
from PySide6.QtWidgets import QLineEdit

class DragDropLineEdit(QLineEdit):
    """A QLineEdit that accepts drag-and-drop for file/folder paths."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent):
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            if url.isLocalFile():
                self.setText(url.toLocalFile())
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

class DragDropDtdInput(DragDropLineEdit):
    """
    A specialized LineEdit that scans dropped folders for DTD files
    and appends them to the current text.
    """
    def dropEvent(self, event: QtGui.QDropEvent):
        if event.mimeData().hasUrls():
            dtd_paths = set()
            urls = event.mimeData().urls()

            for url in urls:
                if url.isLocalFile():
                    path = url.toLocalFile()
                    if os.path.isdir(path):
                        for root, _, files in os.walk(path):
                            for name in files:
                                if name.lower().endswith(".dtd"):
                                    dtd_paths.add(os.path.join(root, name))
                    elif os.path.isfile(path) and path.lower().endswith(".dtd"):
                        dtd_paths.add(path)

            if dtd_paths:
                current_paths = {p.strip() for p in self.text().split(';') if p.strip()}
                all_paths = sorted(list(current_paths.union(dtd_paths)))
                self.setText(";".join(all_paths))
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
