import json
from PyQt5.QtCore import QUrl, QObject, pyqtSlot, QTimer
from PyQt5.QtWebSockets import QWebSocket
import models.settings
from typing import TYPE_CHECKING
from PyQt5.QtNetwork import QAbstractSocket

if TYPE_CHECKING:
    from views import main_window

class WebSocketClient(QObject):
    def __init__(self, url, parent:"main_window.mainWindow" =None):
        super().__init__(parent)
        self.ping_timer = QTimer(self)
        self.ping_timer.timeout.connect(self.ping_server)
        self.socket = QWebSocket()
        self.socket.open(QUrl(url))
        self.socket.connected.connect(self.on_connect) # self.on_connect() function will be called if 'connected' pyQt signal is triggered. connect() function here binds the slot (function) to the signal
        self.socket.disconnected.connect(self.on_disconnect)
        self.socket.textMessageReceived.connect(self.on_message)
        self.socket.error.connect(self.on_error)
        self.parent = parent
        self.states = {
            QAbstractSocket.UnconnectedState: "Unconnected",
            QAbstractSocket.HostLookupState: "Looking up host",
            QAbstractSocket.ConnectingState: "Connecting",
            QAbstractSocket.ConnectedState: "Connected",
            QAbstractSocket.BoundState: "Bound",
            QAbstractSocket.ClosingState: "Closing",
            QAbstractSocket.ListeningState: "Listening"
        }
        self.error_messages = {
            QAbstractSocket.ConnectionRefusedError: "Connection refused",
            QAbstractSocket.RemoteHostClosedError: "Remote host closed connection",
            QAbstractSocket.HostNotFoundError: "Host not found",
            QAbstractSocket.SocketAccessError: "Socket access error",
            QAbstractSocket.SocketResourceError: "Socket resource error",
            QAbstractSocket.SocketTimeoutError: "Socket operation timed out",
            QAbstractSocket.NetworkError: "Network error",
            QAbstractSocket.UnsupportedSocketOperationError: "Unsupported operation",
        }
        state = self.socket.state()
        print(self.states.get(state, f"unkown state: {state}"))
        if models.settings.get_setting("id", None) is not None:
            pass
        else:
            self.parent.toggle_access(False)
            print('parent is: ', parent)
    
    # '0' is the code to initialise the connection
    # '1' is the code that connection is code
    # '2' is the code to ping 
    # '3' is the code for pong
    # '4' is the code for message
    
    @pyqtSlot()
    def ping_server(self):
        print('sending ping to server')
        self.socket.sendTextMessage("2")
    
    @pyqtSlot()
    def on_connect(self):
        print('CONNECTED')
        self.ping_timer.start(10000)
        return
    
    @pyqtSlot()
    def on_disconnect(self):
        self.ping_timer.stop()
        self.sid = None
        print('DISCONNECTED')
        return

    @pyqtSlot(str)
    def on_message(self, message):
        if message[0]=='0':
            config_data = json.loads(message[1:])
            self.sid = config_data.get('sid', None)
            print('set sid', self.sid)
        print('MESSAGE RECIEVED: ', message)
        return

    # @pyqtSlot(int)
    def on_error(self, error):
        print(f"WebSocket ERROR: {self.error_messages.get(error, f'Unknown error: {error}')}")
        return
    
    def is_connected(self):
        return self.socket.state() == QAbstractSocket.ConnectedState