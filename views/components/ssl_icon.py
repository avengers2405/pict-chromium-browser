from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap
import os

class SSLIcon(QLabel):
    def __init__(self):
        super().__init__()
        self.InitSSLIcon()

    def InitSSLIcon(self):
        self.setObjectName("SSLIcon")
        icon = QPixmap(os.path.join(os.path.dirname(__file__), "..", "..", "utils", "resources", "icons", "lock-icon.png"))
        self.setPixmap(icon)