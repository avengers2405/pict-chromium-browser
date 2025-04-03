import os
import sys
import json
import sqlite3

from PyQt5.QtGui import QFontDatabase, QIcon, QFont
from PyQt5.QtWebEngineCore import QWebEngineUrlScheme
from PyQt5.QtWidgets import QApplication
import views.main_window


# DB to open
connection = sqlite3.connect("BrowserLocalDB.db", check_same_thread=False)
# connection = sqlite3.connect(":memory:")
cursor = connection.cursor()

# Font
textFont = QFont("Times", 14)

window=None

if os.path.isfile("settings.json"):  # If settings file exists, then open it
    with open("settings.json", "r") as f:
        settings_data = json.load(f)
else:  # If settings not exists, then create a new file with default settings
    json_data = json.loads(
    """
    {
        "defaultSearchEngine": "Google",
        "startupPage": "https://google.com",
        "newTabPage": "https://google.com",
        "homeButtonPage": "https://google.com"
    }
    """
    )
    with open("settings.json", "w") as f:
        json.dump(json_data, f, indent=2)
    with open("settings.json", "r") as f:
        settings_data = json.load(f)


def main():
    scheme = QWebEngineUrlScheme(b'pict')
    scheme.setFlags(
        QWebEngineUrlScheme.Flag.SecureScheme | 
        QWebEngineUrlScheme.Flag.LocalScheme | 
        QWebEngineUrlScheme.Flag.LocalAccessAllowed
    )
    QWebEngineUrlScheme.registerScheme(scheme)
    print("shceme status: ", QWebEngineUrlScheme.schemeByName(b'pict'))

    gui_app = QApplication(sys.argv)

    # Disable shortcut in context menu
    gui_app.styleHints().setShowShortcutsInContextMenus(False)

    # Set the window name
    QApplication.setApplicationName("Simple Web Browser")

    # Set the window icon
    QApplication.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "logos", "pict.jpg")))

    # App styles
    if os.path.isfile(os.path.join(os.path.dirname(__file__), "..", "utils", "styles", "styles.css")):
        with open(os.path.join(os.path.dirname(__file__), "..", "utils", "styles", "styles.css")) as f:
            gui_app.setStyleSheet(f.read())

    QFontDatabase.addApplicationFont(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "fonts", "fa-solid-900.ttf"))

    try:
        global window
        window = views.main_window.mainWindow()
        window.init_ui()
    except Exception as e:
        print('excepion caught in main widnow: ', e)

    sys.exit(gui_app.exec_())
