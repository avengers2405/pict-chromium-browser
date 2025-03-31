import os
from PyQt5.QtCore import QUrl, QBuffer, QIODevice
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineProfile
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestJob, QWebEngineUrlScheme, QWebEngineUrlSchemeHandler

class CustomUrlSchemeHandler(QWebEngineUrlSchemeHandler):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.base_path = ''
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

        if url == 'login':
            try:
                html_page = open(os.path.join(os.path.dirname(__file__), '..', '..', 'utils', 'login.html'))
                buffer.write(html_page.read().encode('utf-8'))
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
        elif url == 'icc':
            try:
                html_page = open(os.path.join(os.path.dirname(__file__), '..', '..', 'utils', 'init_client_conn.html'))
                buffer.write(html_page.read().encode('utf-8'))
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

# class InternalRoutes:

#     @staticmethod
#     def get_page(url):
#         assert(url.startswith("pict://"))
#         url = url.split("pict://")[1]

#         if url == 'login':
#             try:
#                 html_page = open(os.path.join(os.path.dirname(__file__), '..', '..', 'utils', 'login.html'))
#                 return {
#                     'url': QUrl('pict://'+url),
#                     'content': html_page.read().encode('utf-8'),
#                     'mimeType': 'text/html'
#                 }
#             except Exception as e:
#                 print("Error while opening file: ", e)
#                 return {
#                     'url': QUrl('pict://'+url),
#                     'content': """
#                             <html>
#                                 <head>
#                                     <title>
#                                         ${url}
#                                     </title>
#                                 </head>
#                                 <body>
#                                     Internal error. We apologize.
#                                 </body>
#                             </html>
#                         """,
#                     'mimeType': 'text/html'
#                 }
            
def get_page(url):
    assert(url.startswith("pict://"))
    url = url.split("pict://")[1]
    print('actual url: ', url)
    if url == 'login':
        print('mathched with login')
        try:
            html_page = open(os.path.join(os.path.dirname(__file__), '..', '..', 'utils', 'login.html'))
            print('returning page: ', {
                'url': QUrl('pict://'+url),
                'content': html_page.read().encode('utf-8'),
                'mimeType': 'text/html'
            })
            return {
                'url': QUrl('pict://'+url),
                'content': html_page.read().encode('utf-8'),
                'mimeType': 'text/html'
            }
        except Exception as e:
            print("Error while opening file: ", e)
            return {
                'url': QUrl('pict://'+url),
                'content': """
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
                    """,
                'mimeType': 'text/html'
            }
    else:
        print('url recieved: ', url)