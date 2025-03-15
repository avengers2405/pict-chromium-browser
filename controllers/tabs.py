import os

from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtGui import QFont
# import views.main_window
import views

class Tabs(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setDocumentMode(True)

        # Set the tabs closable
        self.setTabsClosable(True)

        # Set the tabs movable
        self.setMovable(True)

        # Add font family
        font = QFont("Segoe UI", 8)
        self.setFont(font)

        # Add some styles to the tabs
        with open(
            os.path.join(os.path.dirname(__file__), "..", "utils", "styles", "tab_style.css")
        ) as f:  # Open tab_styles.css file
            self.setStyleSheet(f.read())

        # Add new tab when tab tab is doubleclicked
        self.tabBarDoubleClicked.connect(views.window.tab_open_doubleclick)

        # To connect to a function when current tab has been changed
        self.currentChanged.connect(views.window.tab_changed)

        # Function to handle tab closing
        self.tabCloseRequested.connect(views.window.close_current_tab)