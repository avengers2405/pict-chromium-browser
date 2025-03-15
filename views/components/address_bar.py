from PyQt5.QtWidgets import QLineEdit
import os

class AddressBar(QLineEdit):
    def __init__(self):
        super().__init__()
        self.setFocus()

    def mousePressEvent(self, e):
        self.selectAll()

    def initAddressBar(self):
        # Set the placeholder text
        self.setPlaceholderText("Search or enter web address")

        # Set focus to the address bar
        self.setFocus()
        with open(os.path.join(os.path.dirname(__file__), "..", "..", "utils", "styles", "addr_bar.css")) as f:
            self.setStyleSheet(f.read())