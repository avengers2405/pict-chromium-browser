from PyQt5.QtCore import QObject, pyqtSignal, QUrl

class BrowserState(QObject):
    # Signals for communication between components
    url_changed = pyqtSignal(QUrl)
    tab_added = pyqtSignal(int)  # tab index
    tab_closed = pyqtSignal(int)  # tab index
    tab_selected = pyqtSignal(int)  # tab index
    
    def __init__(self):
        super().__init__()
        self.current_url = QUrl()
        self.tabs = []
        self.current_tab_index = -1
        
    def update_url(self, url):
        self.current_url = url
        self.url_changed.emit(url)
    