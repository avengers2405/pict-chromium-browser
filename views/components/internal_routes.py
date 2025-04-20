import json
import os, secrets
from PyQt5.QtCore import QUrl, QBuffer, QIODevice
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestJob, QWebEngineUrlSchemeHandler
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from views import main_window

class CustomUrlSchemeHandler(QWebEngineUrlSchemeHandler):
    def __init__(self, parent:"main_window.mainWindow" = None):
        super().__init__(parent)
        self.base_path = ''
        self.parent_window = parent
        self.ws_client = parent.websocket_client
        # print('instantiated this object')
    
    def requestStarted(self, job: QWebEngineUrlRequestJob):
        url = job.requestUrl().toString()
        print('starting custom job')
        try:
            if url.startswith("pict://"):
                print('found custom scheme: ', url)
                # content = CustomUrlSchemeHandler.get_page(url)
                job.reply(b'text/html', self.get_page(url))
            else:
                print('in else part, returning None')
                return None
        except Exception as e:
            content = f"""
                        <html>
                            <head>
                                <title>
                                    Error
                                </title>
                            </head>
                            <body>
                                Some error occurred: {str(e)}
                            </body>
                        </html>    
                    """.encode('utf-8')
            job.reply(b'text/html', content)

    def get_page(self, url):
        assert(url.startswith("pict://"))
        buffer = QBuffer(self)
        buffer.open(QIODevice.ReadWrite)
        url = url.split("pict://")[1]
        print('inside get_page function')

        try:
            if url == 'login':
                # data needed for login: 
                # secret
                self.parent_window.secret = secrets.token_hex(30)
                html_page = open(os.path.join(os.path.dirname(__file__), '..', '..', 'utils', 'login.html'))
                buffer.write(html_page.read().replace(r"{{data_placeholder}}", f"const secret = '{self.parent_window.secret}';").encode('utf-8'))
                buffer.seek(0)
                return buffer
            
            elif url == 'icc':
                html_page = open(os.path.join(os.path.dirname(__file__), '..', '..', 'utils', 'init_client_conn.html'))
                buffer.write(html_page.read().encode('utf-8'))
                buffer.seek(0)
                return buffer
            
            elif url.startswith('admin_login_success'):
                # check whether secret matches
                secret = url.split('admin_login_success/')[1].strip()
                if secret == self.parent_window.secret:
                    self.parent_window.secret = None
                    # perform all browser actions to tell that admin has logged in the browser
                    self.parent_window.websocket_client.send_message(json.dumps({
                        "action": "log",
                        "actionType": "ADMIN_UPGRADE",
                    }))
                    self.parent_window.websocket_client.send_message(json.dumps({
                        "action": "admin",
                    }))
                    self.parent_window.set_admin_access(True) # telling browser that admin access is now alowed.
                    self.parent_window.set_admin_mode(True) # by default browser will go in admin mode after admin login.
                    print('admin login successful url hit.')
                else:
                    # dont do anything since wrong request.
                    pass
                # just reply anything as replied html code wont be rendered anywhere anyways.
                buffer.write("""
                                random reply. Thank you.
                            """.encode('utf-8'))
                buffer.seek(0)
                return buffer
            elif url == 'admin':
                # first start the browser ws server
                if not self.parent_window.websocket_client.server_is_on():
                    self.parent_window.websocket_client.create_ws_server()

                # data needed for dashboard:
                # secret
                self.parent_window.secret = secrets.token_hex(30)
                html_page = open(os.path.join(os.path.dirname(__file__), '..', '..', 'utils', 'admin.html'))
                buffer.write(html_page.read().replace(r"{{data_placeholder}}", f"""
                                                        if (typeof secret === undefined) var secret = '{self.parent_window.secret}';
                                                        else secret = '{self.parent_window.secret}';
                                                        if (typeof socketUrl === undefined) var socketUrl = 'ws://localhost:3002';
                                                        else socketUrl = 'ws://localhost:3002';
                                                    """).encode('utf-8'))
                # buffer.write(html_page.read().encode('utf-8'))
                buffer.seek(0)
                return buffer

            else:
                buffer.write("""
                            <html>
                                <head>
                                    <title>
                                        Not Implemented
                                    </title>
                                </head>
                                <body>
                                    This page is not implemented.
                                </body>
                            </html>
                        """.encode('utf-8'))
                buffer.seek(0)
                return buffer
        except Exception as e:
            print("Error while opening file: ", e)
            buffer.write("""
                        <html>
                            <head>
                                <title>
                                    ${url}
                                </title>
                            </head>
                            <body>
                                Internal error. We apologize.
                            </body>
                        </html>
                    """.encode('utf-8'))
            buffer.seek(0)
            return buffer
