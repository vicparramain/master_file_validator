"""
Theme Management
Handles system theme detection and QSS stylesheet generation.
"""

import platform
import subprocess
import logging

winreg = None
if platform.system().lower() == "windows":
    try:
        import winreg
    except ImportError:
        print("Note: 'winreg' module not found. Windows theme detection will be disabled.")


def get_windows_accent_color_explorer_hex() -> str | None:
    """Gets the Windows accent color. Returns None if not on Windows or fails."""
    if not winreg or platform.system().lower() != "windows":
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Accent") as key:
            value, _ = winreg.QueryValueEx(key, "AccentColorMenu")
            red = value & 0xFF
            green = (value >> 8) & 0xFF
            blue = (value >> 16) & 0xFF
            return f"#{red:02x}{green:02x}{blue:02x}"
    except Exception as e:
        logging.warning(f"Could not get Windows AccentColorMenu from registry: {e}")
        return None


def detect_system_theme() -> str:
    """Detects if the system is in 'light' or 'dark' mode."""
    if platform.system().lower() == "windows" and winreg:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return "light" if value == 1 else "dark"
        except Exception:
            logging.debug("Failed to detect Windows theme from registry.")
            pass
    elif platform.system() == "Darwin":
        try:
            result = subprocess.run(
                ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
                capture_output=True, text=True, check=False
            )
            if result.stdout and "Dark" in result.stdout.strip():
                return "dark"
        except Exception:
            logging.debug("Failed to detect macOS theme.")
            pass
    return "light"


def get_stylesheet(checkmark_icon_path: str) -> str:
    """
    Returns the complete QSS stylesheet for the application.

    Args:
        checkmark_icon_path: A theme-specific path to the checkmark icon.
    """
    return f"""
    QWidget {{ 
        background-color: palette(window); color: palette(window-text); 
        font-family: 'Segoe UI Variable', 'Segoe UI', sans-serif; font-size: 9pt; 
    }}

    QLineEdit, QComboBox {{ 
        background-color: palette(base); border: 1px solid palette(mid); 
        border-radius: 4px; padding: 4px 6px; color: palette(text); min-height: 20px; 
    }}

    QCheckBox {{
        spacing: 5px;
        color: palette(text);
        background-color: transparent;
        padding: 4px;
    }}
    QCheckBox::indicator {{
        width: 13px;
        height: 13px;
        border: 1px solid palette(midlight);
        border-radius: 3px;
        background-color: palette(base);
    }}
    QCheckBox::indicator:hover {{
        border-color: palette(highlight);
    }}
    QCheckBox::indicator:checked {{
        background-color: palette(highlight);
        border: 1px solid palette(highlight);
        image: url({checkmark_icon_path});
    }}
    QCheckBox::indicator:checked:hover {{
        border-color: palette(highlight);
        background-color: palette(highlight);
    }}

    QTableWidget {{
        background-color: palette(base);
        border: 1px solid palette(mid);
        gridline-color: palette(midlight);
    }}
    QHeaderView::section {{
        background-color: palette(button);
        border: 1px solid palette(mid);
        padding: 4px;
    }}
    QToolButton {{ 
        background-color: transparent; border: 1px solid transparent; padding: 4px; border-radius: 4px; 
    }}
    QToolButton:hover {{ background-color: palette(light); border-color: palette(mid); }}
    QPushButton {{ 
        background-color: palette(button); border: 1px solid palette(mid); 
        border-radius: 4px; padding: 6px 12px; min-height: 20px; 
    }}
    QPushButton:hover {{ background-color: palette(light); border-color: palette(highlight); }}
    QProgressBar {{ 
        height: 8px; border: 1px solid palette(mid); border-radius: 4px; 
        background-color: palette(base); text-align: center; 
    }}
    QProgressBar::chunk {{ background-color: palette(highlight); border-radius: 3px; margin: 1px; }}
    QScrollBar:vertical {{ background: transparent; width: 10px; }}
    QScrollBar::handle:vertical {{ background: palette(midlight); min-height: 25px; border-radius: 5px; }}
    QScrollBar::handle:vertical:hover {{ background-color: palette(light); }}
    QScrollBar:horizontal {{ background: transparent; height: 10px; }}
    QScrollBar::handle:horizontal {{ background: palette(midlight); min-width: 25px; border-radius: 5px; }}
    QScrollBar::handle:horizontal:hover {{ background-color: palette(light); }}
    """
