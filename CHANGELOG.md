# 🚀 Master File Validator 2.0

**V2.0.0 (Modular Release)**

This release is a complete rewrite of the application, migrating from **PyQt6** to **PySide6** and introducing a modern, multithreaded, and theme-aware interface.

---

## ✨ Added

- **Modern UI (PySide6):** Ported the entire application from PyQt6 to PySide6.  
- **Background Validation:** Validation now runs on a background thread (`QThreadPool`) to prevent the UI from freezing.  
- **System Theme Detection:** The app now automatically detects Windows/macOS light and dark modes and applies a native-looking theme.  
- **Windows Accent Color:** Automatically uses the Windows accent color for the “Run” button and highlights.  
- **DTD Validation:** Added a new input field to load one or more `.dtd` files for validating XML, XLIFF, and DITA files.  
- **Drag & Drop:**  
  - The main path input now accepts dropped folders.  
  - The DTD input accepts dropped `.dtd` files or folders containing DTDs.  
- **Results Table:** Replaced the plain text output with a 3-column `QTableWidget` (Path, Filename, Details).  
- **Column Sorting:** The results table can be sorted by clicking any column header.  
- **HTML Export:** Replaced the plain `.txt` export with a styled HTML report that color-codes valid and invalid file rows.  
- **BOM Support:** Added a checkbox to optionally allow UTF-8 BOM (Byte Order Mark) for JSON and YAML files.  
- **New File Support:** Added support for `.dita` files.  
- **SVG Icons:** Added theme-aware SVG icons for all buttons and the application window.  
- **Modular Codebase:** The application was completely refactored into six separate modules for maintainability:  
  - `run.py` — Entry point  
  - `main_window.py` — UI logic  
  - `validator.py` — File validation logic  
  - `theme.py` — Theme detection and styling  
  - `ui_widgets.py` — Custom drag & drop widgets  
  - `config.py` — Constants  

---

## 🔧 Changed

- **Improved XML Parsing:** Now uses lxml’s recovering parser to find and report multiple errors in a single XML file instead of stopping at the first error.  
- **Better XML Error Reporting:** Now specifically detects unescaped ampersands (`&`) and provides a user-friendly error message.  
- **UI Layout:** Replaced the simple VBox/HBox layout with a cleaner `QGridLayout` within a “card” frame.  
- **Styling:** Replaced all hardcoded inline `setStyleSheet` calls with a centralized, dynamic stylesheet system.  

---

## 🗑️ Removed

- **PyQt6 Dependency:** The project no longer uses PyQt6.  
- **Plain Text Output:** Removed the `QTextEdit` results view in favor of the new table.  
- **Plain Text Export:** Removed the `.txt` export feature.  
- **Hardcoded Icon Path:** Removed the old hardcoded `.ico` path.  
