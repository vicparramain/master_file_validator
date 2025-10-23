"""
File Validator Application
Main entry point for the application.
"""

import sys
import os
import logging
from PySide6 import QtWidgets
from main_window import FileValidator
from config import ICONS_DIR

def _create_dummy_icons_if_missing():
    """Creates an 'icons' directory and dummy SVG icons if they don't exist."""
    if not os.path.exists(ICONS_DIR):
        os.makedirs(ICONS_DIR, exist_ok=True)

    icons_to_create = ["app", "folder", "run", "export", "dtd", "check"]

    for name in icons_to_create:
        for variant in ["light", "dark"]:
            path = os.path.join(ICONS_DIR, f"{name}_{variant}.svg")
            if not os.path.exists(path):
                with open(path, "w") as f:
                    if name == "check":
                        fill_color = "white" if variant == "dark" else "black"
                        f.write(f"<svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24'><path fill='{fill_color}' d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z'/></svg>")
                    else:
                        f.write("<svg width='16' height='16'><rect width='16' height='16' style='fill:gray'/></svg>")

def main():
    """Initializes and runs the application."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    _create_dummy_icons_if_missing()

    app = QtWidgets.QApplication(sys.argv)
    window = FileValidator()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
