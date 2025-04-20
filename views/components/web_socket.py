import json
import uuid
from PyQt5.QtCore import QUrl, QObject, pyqtSlot, QTimer
from PyQt5.QtWebSockets import QWebSocket, QWebSocketServer
import models.settings
from typing import TYPE_CHECKING
from PyQt5.QtNetwork import QAbstractSocket, QHostAddress

if TYPE_CHECKING:
    from views import main_window

class WebSocketClient(QObject):
    def __init__(self, url, parent:"main_window.mainWindow" = None):
        super().__init__(parent)
        self.url = url
        self.reconnect_timer = QTimer(self)
        self.reconnect_timer.timeout.connect(self.reconnect_ws)
        self.is_reconnect = False
        self.socket = QWebSocket()
        self.socket.open(QUrl(url)) 
        self.socket.connected.connect(self.on_connect) # self.on_connect() function will be called if 'connected' pyQt signal is triggered. connect() function here binds the slot (function) to the signal
        self.socket.disconnected.connect(self.on_disconnect)
        self.socket.textMessageReceived.connect(self.on_message)
        self.socket.error.connect(self.on_error)
        self.parent_window = parent
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
        

        # now creating a web socket server also here only since that is expected to be small in code and can be more easily integrated
        # with the the main ws, which is this ws_client class.
        self.ws_server = None
        self.client={}
        self.server_client = None
    
    # '0' is the code to initialise the connection
    # '1' is the code that connection is closed
    # '2' is the code to ping 
    # '3' is the code for pong
    # '4' is the code for message
    # '5' send config details first
    # '6' connection done
    # '7' connect through admin without login portal
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
                msg = json.loads(message[1:])
                if msg.get('type') == 'all_data':
                    self.server_client.sendTextMessage(message)
                elif msg.get('type') == 'update':
                    print('SENDING UPDATE TO HTML PAGE: ', message)
                    self.parent_window.interceptor.update_lists()
                    self.server_client.sendTextMessage(message)

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
    
    def create_ws_server(self):
        try:
            self.ws_server = QWebSocketServer("Browser WebSocket Server", QWebSocketServer.NonSecureMode, self.parent_window)
            if self.ws_server.listen(QHostAddress.Any, 3002):
                self.ws_server.newConnection.connect(self.server_on_new_connection)
                print('started ws server')
            else:
                print('failed to start ws server')
        except Exception as e:
            print('exception in starting ws server: ', e)
    
    @pyqtSlot()
    def server_on_new_connection(self):
        print('server CONN CALLED - 1.')
        client = self.ws_server.nextPendingConnection() # this retrieves the next pending connection AS WELL AS accepts it.
        # the client is already accepted at a TCP level when this function is being executed, however to accept it at application level
        # this function needs to be called to extract the client from network queue and accept it. If this function is not called, the
        # connection will eventually timeout and be closed.
        print("client RECIEVED: ", client, 2)
        self.server_client = client
        print('client ASSIGNED')
        if client is not None:
            print('new connection to server')
            client.textMessageReceived.connect(self.server_on_message)
            client.disconnected.connect(self.server_on_disconnect)
            client.error.connect(self.server_on_error)

    @pyqtSlot(str)
    def server_on_message(self, message):
        print('recieved message to browser server from client: ', message)
        if message[0]=='0':
            # accept all for now dev
            self.client['auth'] = True
            self.server_client.sendTextMessage('6')
            print('client authenticated, saved: ', self.client.get('auth', False))
            # secret = json.loads(message[1:]).get('secret', None)
            # if secret == self.parent_window.secret:
            #     # accept auth
            #     self.client['auth'] = True
            #     self.server_client.sendTextMessage('6')
            #     print('client authenticated, saved: ', self.client.get('auth', False))
            # else:
            #     # dont accept, so dont change self.client details to leave it empty / uninitialised.
            #     # in future, could be due to the fact that secret has expired. then send the appropriate message
            #     pass
        else:
            if not self.client.get('auth', False):
                print('rejecting message: ', message, '; due to auth failure')
                self.server_client.sendTextMessage('5')
            else:
                if message[0]=='2':
                    self.server_client.sendTextMessage('3')
                elif message[0]=='4':
                    try:
                        msg = json.loads(message[1:])
                        if msg.get('type')=='whitelist':
                            print('recieved whitelist request.')
                            self.send_message(message[1:])
                        elif msg.get('type')=='blacklist':
                            print('recieved blacklist request.')
                            self.send_message(message[1:])
                        elif msg.get('type')=='log':
                            print('recieved log request.')
                            self.send_message(message[1:])
                        elif msg.get('type')=='update_settings':
                            print('recieved req to update settings.')
                            self.send_message(message[1:])
                        else:
                            print('not handled this yet: ', msg.get('type'))
                    except Exception as e:
                        # received as plain text
                        print('message as plain text: ', message[1:], e)
                    print('message: ', message[1:])
                elif message[0]=='8':
                    print('recieved erro from client: ', message[1:])
                else:
                    self.server_client.sendTextMessage('8'+json.dumps({
                        "error": "send proper message type",
                    }))

        return
    
    @pyqtSlot()
    def server_on_disconnect(self):
        print('some client disconnected')
        return
    
    def server_on_error(self, error):
        print(f"WebSocket ERROR: {self.error_messages.get(error, f'Unknown error: {error}')}")
        return
    
    def server_is_on(self):
        try:
            if self.ws_server.isListening():
                return True
        except Exception as e:
            return False
        finally:
            return False
        