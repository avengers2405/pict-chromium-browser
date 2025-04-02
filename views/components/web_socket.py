import json
import uuid
from PyQt5.QtCore import QUrl, QObject, pyqtSlot, QTimer
from PyQt5.QtWebSockets import QWebSocket
import models.settings
from typing import TYPE_CHECKING
from PyQt5.QtNetwork import QAbstractSocket

if TYPE_CHECKING:
    from views import main_window

class WebSocketClient(QObject):
    def __init__(self, url, parent:"main_window.mainWindow" = None):
        super().__init__(parent)
        self.url = url
        self.reconnect_timer = QTimer(self)
        self.reconnect_timer.timeout.connect(self.reconnect_ws)
        # self.reconnect_timer.start(7000)
        self.is_reconnect = False
        self.socket = QWebSocket()
        self.socket.open(QUrl(url)) 
        self.socket.connected.connect(self.on_connect) # self.on_connect() function will be called if 'connected' pyQt signal is triggered. connect() function here binds the slot (function) to the signal
        self.socket.disconnected.connect(self.on_disconnect)
        self.socket.textMessageReceived.connect(self.on_message)
        self.socket.error.connect(self.on_error)
        self.parent_window = parent
        self.entity_id = None # this will be upgraded to admin id if needed
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
            self.parent_window.toggle_access(False)
            print('parent is: ', parent)
    
    # '0' is the code to initialise the connection
    # '1' is the code that connection is closed
    # '2' is the code to ping 
    # '3' is the code for pong
    # '4' is the code for message
    # '5' send config details first
    # '6' connection done
    # '7' connecting through admin without login portal
    # '8' error
    
    @pyqtSlot()
    def ping_server(self):
        print('sending ping to server')
        self.socket.sendTextMessage("2")
    
    @pyqtSlot()
    def on_connect(self):
        print('CONNECTED')
        # self.ping_timer.start(10000) # no need to start ping timer bcz why to start it?
        # print('timer started')
        if self.is_reconnect:
            self.reconnect_timer.stop()
        self.socket.sendTextMessage('0'+json.dumps({
            "mac": ":".join(["{:02x}".format((uuid.getnode() >> ele) & 0xff) for ele in range(0,8*6,8)][::-1])
        }))
        return
    
    @pyqtSlot()
    def on_disconnect(self):
        # self.ping_timer.stop() # since never started
        self.parent_window.disconnect_browser()
        self.reconnect_timer.start(7000)
        self.is_reconnect = True
        print('DISCONNECTED')
        return

    @pyqtSlot(str)
    def on_message(self, message):
        try:
            if message[0]=='0':
                print('recieved config details: ', message[1:])
            elif message[0]=='2':
                print('3')
            elif message[0]=='4':
                # normal message recieved here
                print('message: ', message[1:])
            elif message[0]=='5':
                self.socket.sendTextMessage('0'+json.dumps({
                    "mac": ":".join(["{:02x}".format((uuid.getnode() >> ele) & 0xff) for ele in range(0,8*6,8)][::-1])
                }))
            elif message[0]=='6':
                # server successfully authenticated
                if self.is_reconnect:
                    self.parent_window.init_reconnected_browser()
                else:
                    self.parent_window.init_connected_browser()
                ws_data = json.loads(message[1:])
                self.entity_id = ws_data.get("client_id", None) # we are assuming server will always send client id, so no validation.
            elif message[0]=='8':
                # handle server error here
                pass
        except Exception as e:
            print('exception: ', e)
        print('MESSAGE RECIEVED: ', message)
        return

    # @pyqtSlot(int)
    def on_error(self, error):
        print(f"WebSocket ERROR: {self.error_messages.get(error, f'Unknown error: {error}')}")
        return
    
    def is_connected(self):
        return self.socket.state() == QAbstractSocket.ConnectedState

    def send_message(self, message):
        try:
            self.socket.sendTextMessage('4'+message)
        except Exception as e:
            print('exception: ', e)
        return
    
    def reconnect_ws(self):
        try:
            self.socket.open(QUrl("ws://localhost:3001"))
        except Exception as e:
            print('connection to ws failed: ', e)