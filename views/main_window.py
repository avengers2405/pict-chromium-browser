from PyQt5.QtWebEngineWidgets import (
    QWebEngineDownloadItem,
    QWebEngineSettings,
    QWebEngineView,
    QWebEngineProfile
)
from PyQt5.QtWidgets import (
    QMainWindow,
    QPushButton,
    QShortcut,
    QToolBar,
    QMenu,
    QAction,
    QFileDialog,
)
from PyQt5.QtCore import QSize, QUrl, Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5 import QtCore
from PyQt5 import QtGui
import views.components.address_bar
from views.components.network import RequestInterceptor
from views.components.internal_routes import CustomUrlSchemeHandler
import views.components.ssl_icon
import views.components.custom_web_engine
import controllers.printer
import controllers.errors
import views.components.settings.about
import views.components.settings.history
import views.components.settings.settings
import views.components.web_socket
import controllers.tabs
import views
import models.settings
import sys
import os
import re
import pyperclip as pc
import datetime
from dotenv import load_dotenv


# Regular expressions to match urls
pattern = re.compile(
    r"^(http|https)?:?(\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
)
without_http_pattern = re.compile(
    r"[\-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
)
file_pattern = re.compile(r"^file://")

pict_scheme_pattern = re.compile(r"^pict://")
load_dotenv()


class mainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(mainWindow, self).__init__(*args, **kwargs)

        self.webview = QWebEngineView(self)
        self.profile = QWebEngineProfile("SecureBrowserProfile")
        self.websocket_client = views.components.web_socket.WebSocketClient("ws://localhost:3001", self)
        self.interceptor = RequestInterceptor(self)
        self.profile.setUrlRequestInterceptor(self.interceptor)
        self.scheme_handler = CustomUrlSchemeHandler(self)
        self.profile.installUrlSchemeHandler(b'pict', self.scheme_handler)
        self.managed_tabs = [] # an array to store tab objects + their metadata to specially manage them.
        self.secret = None # this will be used for any kind of connection between browser, and html pages.
        self.__admin_access = False
        self.__admin_mode = False
        # self.create_ws_server()
        # self.client={}

    def init_ui(self):
        self.tabs = controllers.tabs.Tabs()  # create tabs

        # create history table
        views.cursor.execute(
            """CREATE TABLE IF NOT EXISTS "history" (
                "id"	INTEGER,
                "title"	TEXT,
                "url"	TEXT,
                "date"	TEXT,
                PRIMARY KEY("id")
            )"""
        )

        InspectShortcut = QShortcut("Ctrl+Shift+I", self)
        InspectShortcut.activated.connect(self.open_dev_tools)

        # open new tab when 
        AddNewTabKeyShortcut = QShortcut("Ctrl+T", self)
        AddNewTabKeyShortcut.activated.connect(
            lambda: self.add_new_tab(
                QUrl(models.settings.settings_data["newTabPage"]), label="New tab"
            )
        )
        SwitchToNextTabShortcut = QShortcut("Ctrl+Tab", self)
        SwitchToNextTabShortcut.activated.connect(lambda: self.switch_to_next_tab())
        
        SwitchToPrevTabShortcut = QShortcut("Ctrl+Shift+Tab", self)
        SwitchToPrevTabShortcut.activated.connect(lambda: self.switch_to_previous_tab())
        # Close current tab on Ctrl+W
        CloseCurrentTabKeyShortcut = QShortcut("Ctrl+W", self)
        # print("Ctrl+W pressed, argument sent: ", lambda: self.close_current_tab(self.tabs.currentIndex()))
        CloseCurrentTabKeyShortcut.activated.connect(
            lambda: self.close_current_tab(self.tabs.currentIndex())
        )

        # Exit browser on shortcut Ctrl+Shift+W
        ExitBrowserShortcutKey = QShortcut("Ctrl+Shift+W", self)
        ExitBrowserShortcutKey.activated.connect(sys.exit)

        # nav bar
        self.navbar = QToolBar()
        self.navbar.setMovable(False)
        self.addToolBar(self.navbar)

        # back button
        back_btn = QPushButton(self)
        back_btn.setObjectName("back_btn")
        back_btn.setIcon(
            QtGui.QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "left-arrow.png"))
        )
        back_btn.setToolTip("Back to previous page")
        back_btn.setShortcut("Alt+Left")
        back_btn.clicked.connect(self.navigate_back_tab)
        self.navbar.addWidget(back_btn)

        # forward button
        forward_butn = QPushButton(self)
        forward_butn.setObjectName("forward_butn")
        forward_butn.setIcon(
            QtGui.QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "right-arrow.png"))
        )
        forward_butn.setToolTip("Go forward")
        forward_butn.setShortcut("Alt+Right")
        forward_butn.clicked.connect(self.forward_tab)
        self.navbar.addWidget(forward_butn)

        # Refresh button
        self.reload_butn = QPushButton(self)
        self.reload_butn.setObjectName("reload_butn")
        self.reload_butn.setToolTip("Reload current page")
        self.reload_butn.setShortcut("Ctrl+R")
        self.reload_butn.resize(QSize(50, 50))
        self.reload_butn.setIcon(
            QtGui.QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "refresh.png"))
        )
        self.reload_butn.clicked.connect(self.reload_tab)

        self.stop_btn = QPushButton(self)
        self.stop_btn.setObjectName("stop_butn")
        self.stop_btn.setToolTip("Stop loading current page")
        self.stop_btn.setShortcut("Escape")
        self.stop_btn.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "cross.png")))
        self.stop_btn.clicked.connect(self.stop_loading_tab)

        # Added stop button
        self.stop_action = self.navbar.addWidget(self.stop_btn)

        # Added reload button
        self.reload_action = self.navbar.addWidget(self.reload_butn)

        # Home button
        self.home_button = QPushButton(self)
        self.home_button.setObjectName("home_button")
        self.home_button.setToolTip("Back to home")
        self.home_button.setIcon(
            QtGui.QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "home.png"))
        )
        self.home_button.clicked.connect(self.goToHome)
        self.navbar.addWidget(self.home_button)

        # Add Address bar
        self.url_bar = views.components.address_bar.AddressBar()
        self.url_bar.initAddressBar()
        self.url_bar.setFrame(False)
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.url_bar.setShortcutEnabled(True)
        self.url_bar.setToolTip(self.url_bar.text())

        # Set focus on the Addressbar by pressing Ctrl+E
        FocusOnAddressBar = QShortcut("Ctrl+E", self)
        FocusOnAddressBar.activated.connect(self.url_bar.setFocus)

        # Set stop action to be invisible
        self.stop_action.setVisible(False)

        # Add a separator
        self.navbar.addSeparator()

        # Shows ssl security icon
        self.httpsicon = views.components.ssl_icon.SSLIcon()

        # Add http icon to the navbar bar
        self.navbar.addWidget(self.httpsicon)

        # Add Address Bar to the navbar
        self.navbar.addWidget(self.url_bar)

        # The context menu
        context_menu = QMenu(self)

        # Set the object's name
        context_menu.setObjectName("ContextMenu")

        # Button for the three dot context menu button
        ContextMenuButton = QPushButton(self)
        ContextMenuButton.setObjectName("ContextMenuButton")

        # Enable three dot menu by pressing Alt+F
        ContextMenuButton.setShortcut("Alt+F")

        # Give the three dot image to the Qpushbutton
        ContextMenuButton.setIcon(
            QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "more.png"))
        )  # Add icon
        ContextMenuButton.setObjectName("ContextMenuTriggerButn")
        ContextMenuButton.setToolTip("More")

        # Add the context menu to the three dot context menu button
        ContextMenuButton.setMenu(context_menu)

        """Actions of the three dot context menu"""

        # Add new tab
        newTabAction = QAction("New tab", self)
        newTabAction.setIcon(
            QtGui.QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "newtab.png"))
        )
        newTabAction.triggered.connect(
            lambda: self.add_new_tab(
                QUrl(models.settings.settings_data["newTabPage"]), "Homepage"
            )
        )
        newTabAction.setToolTip("Add a new tab")
        context_menu.addAction(newTabAction)

        # New window action
        newWindowAction = QAction("New window", self)
        newWindowAction.setIcon(
            QtGui.QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "app_window_ios.png"))
        )
        newWindowAction.triggered.connect(self.CreateNewWindow)
        context_menu.addAction(newWindowAction)

        # Close tab action
        CloseTabAction = QAction("Close tab", self)
        CloseTabAction.setIcon(
            QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "closetab.png"))
        )
        CloseTabAction.triggered.connect(
            lambda: self.close_current_tab(self.tabs.currentIndex())
        )
        CloseTabAction.setToolTip("Close current tab")
        context_menu.addAction(CloseTabAction)

        # A separator
        context_menu.addSeparator()

        # Another separator
        context_menu.addSeparator()

        # Feature to copy site url
        CopySiteAddress = QAction(
            QtGui.QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "url.png")),
            "Copy site url",
            self,
        )
        CopySiteAddress.triggered.connect(self.CopySiteLink)
        CopySiteAddress.setToolTip("Copy current site address")
        context_menu.addAction(CopySiteAddress)

        # Fetaure to go to copied site url
        PasteAndGo = QAction(
            QtGui.QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "paste.png")),
            "Paste and go",
            self,
        )
        PasteAndGo.triggered.connect(self.PasteUrlAndGo)
        PasteAndGo.setToolTip("Go to the an url copied to your clipboard")
        context_menu.addAction(PasteAndGo)

        # A separator
        context_menu.addSeparator()

        # View history
        ViewHistory = QAction("History", self)
        ViewHistory.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "history.png")))
        ViewHistory.triggered.connect(self.openHistory)
        ViewHistory.setShortcut("Ctrl+h")
        context_menu.addAction(ViewHistory)

        # Open page
        OpenPgAction = QAction("Open", self)
        OpenPgAction.setIcon(
            QtGui.QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "openclickhtml.png"))
        )
        OpenPgAction.setToolTip("Open a file in this browser")
        OpenPgAction.setShortcut("Ctrl+O")
        OpenPgAction.triggered.connect(self.open_local_file)
        context_menu.addAction(OpenPgAction)

        # Save page as
        SavePageAs = QAction("Save page as", self)
        SavePageAs.setIcon(
            QtGui.QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "save-disk.png"))
        )
        SavePageAs.setToolTip("Save current page to this device")
        SavePageAs.setShortcut("Ctrl+S")
        SavePageAs.triggered.connect(self.save_page)
        context_menu.addAction(SavePageAs)

        # Print this page action
        PrintThisPageAction = QAction("Print this page", self)
        PrintThisPageAction.setIcon(
            QtGui.QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "printer.png"))
        )
        PrintThisPageAction.triggered.connect(self.print_this_page)
        PrintThisPageAction.setShortcut("Ctrl+P")
        PrintThisPageAction.setToolTip("Print current page")
        context_menu.addAction(PrintThisPageAction)

        # Print with preview
        PrintPageWithPreview = QAction(
            QtGui.QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "printerprev.png")),
            "Print page with preview",
            self,
        )
        PrintPageWithPreview.triggered.connect(self.print_with_preview)
        PrintPageWithPreview.setShortcut("Ctrl+Shift+P")
        context_menu.addAction(PrintPageWithPreview)

        # Save page as PDF
        SavePageAsPDF = QAction(
            QtGui.QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "adobepdf.png")),
            "Save as PDF",
            self,
        )
        SavePageAsPDF.triggered.connect(self.save_as_pdf)
        context_menu.addAction(SavePageAsPDF)

        context_menu.addSeparator()

        # Settings widget:
        userSettingsAction = QAction(
            QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "settings.png")),
            "Settings",
            self,
        )
        userSettingsAction.triggered.connect(self.openSettings)
        context_menu.addAction(userSettingsAction)

        # The help submenu
        HelpMenu = QMenu("Help", self)
        HelpMenu.setObjectName("HelpMenu")
        HelpMenu.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "question.png")))
        context_menu.addMenu(HelpMenu)

        # About action
        AboutAction = QAction("About this browser", self)
        AboutAction.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "info.png")))
        AboutAction.triggered.connect(self.about)
        HelpMenu.addAction(AboutAction)

        # Visit action
        # VisitGithubAction = QAction("Visit Github", self)
        # VisitGithubAction.triggered.connect(self.visitGithub)
        # HelpMenu.addAction(VisitGithubAction)

        # Add a separator
        context_menu.addSeparator()

        # Close browser
        CloseBrowser = QAction("Close browser", self)
        CloseBrowser.triggered.connect(lambda: sys.exit())
        context_menu.addAction(CloseBrowser)

        """ 
        Set menu for the button
        ContextMenuButton.add
        Add the context menu to the navbar
        """

        self.navbar.addWidget(ContextMenuButton)

        # Stuffs to see at startup
        self.add_new_tab(QUrl(models.settings.settings_data["startupPage"]), "Homepage")

        # Set the address focus
        self.url_bar.setFocus()

        # what to display on the window
        self.setCentralWidget(self.tabs)

        # Stuffs to set the window
        self.showMaximized()

        # Set minimum size
        self.setMinimumWidth(400)

        _browser = self.tabs.currentWidget().load(QUrl("pict://icc"))
        # _browser = self.add_new_tab(QUrl("pict://icc"))
        # self.managed_tabs.append({
        #     "browser": _browser,
        #     "label": "connecting_page"
        # })

    """
    Instead of managing 2 slots associated with the progress and completion of loading,
    only one of them should be used since, for example, the associated slot is also called when
    it is loaded at 100% so it could be hidden since it can be invoked together with finished.
    """

    def open_dev_tools(self):
        dev_tools = QWebEngineView()
        self.tabs.currentWidget().page().setDevToolsPage(dev_tools.page())
        dev_tools.show()
        dev_tools.showMaximized()
        dev_tools.adjustSize()
        print('opened dev tools: ', dev_tools.isFullScreen())
        self.dev_tools = dev_tools

    def toggle_access(self, val):
        RequestInterceptor.set_login(val)
    
    def init_connected_browser(self):
        """
        this will run once the browser is opened and web socket connects to the server successfully.
        this function should only run once. if the client disconnects in the middle, this should not 
        run. instead, the above function, toggle_access() should run.
        """
        while self.tabs.count()>1:
            self.tabs.currentWidget().close()
        self.toggle_access(True)
        self.tabs.currentWidget().load(QUrl(models.settings.get_setting("startupPage", "https://google.com")))
    
    def init_reconnected_browser(self):
        """
        this will run only on reconnection trials, not on initial connection
        """
        self.toggle_access(True)
        for tab in self.managed_tabs:
            if tab.get("label", None) == "connecting_page":
                if self.tabs.count()==1:
                    # practically should never be reached
                    self.tabs.currentWidget().load(QUrl(models.settings.get_setting("startupPage", "https://google.com")))
                else:
                    ind = self.tabs.indexOf(tab.get("browser", None))
                    self.tabs.removeTab(ind)
        # self.tabs.currentWidget().reload() # reload only if a site was under loading progress when server disconnected and failed to load.
    
    def disconnect_browser(self):
        self.toggle_access(False)
        _browser = self.add_new_tab(QUrl("pict://icc"))
        self.managed_tabs.append({
            "browser": _browser,
            "label": "connecting_page"
        })

    @QtCore.pyqtSlot(int)
    def loadProgressHandler(self, prog):
        if self.tabs.currentWidget() is not self.sender():
            return

        loading = prog < 100

        self.stop_action.setVisible(loading)
        self.reload_action.setVisible(not loading)

    # funcion to navigate to home when home icon is pressed

    def goToHome(self):
        self.tabs.currentWidget().setUrl(QUrl(models.settings.settings_data["homeButtonPage"]))

    # Define open a new window

    def CreateNewWindow(self):
        window = mainWindow()
        window.show()

    # Copy url of currently viewed page to clipboard
    def CopySiteLink(self):
        pc.copy(self.tabs.currentWidget().url().toString())

    # Adds a new tab and load the content of the clipboard

    def PasteUrlAndGo(self):
        self.add_new_tab(QUrl(pc.paste()), self.tabs.currentWidget().title())

    # navigate backward tab

    def navigate_back_tab(self):
        self.tabs.currentWidget().back()

    # go forward tab

    def forward_tab(self):
        self.tabs.currentWidget().forward()

    # reload tab

    def reload_tab(self):
        self.tabs.currentWidget().reload()

    # stop load current tab

    def stop_loading_tab(self):
        if self.tabs.currentWidget() is None:
            return

        self.tabs.currentWidget().stop()

    """
    Functions to open a local file and save a website to user's local storage
    """

    # Function to open a local file

    def open_local_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            parent=self,
            caption="Open file",
            directory="",
            filter="Hypertext Markup Language (*.htm *.html *.mhtml);;All files (*.*)",
        )
        if filename:
            try:
                with open(filename, "r", encoding="utf8") as f:
                    opened_file = f.read()
                    self.tabs.currentWidget().setHtml(opened_file)

            except:
                dlg = controllers.errors.fileErrorDialog()
                dlg.exec_()

        self.url_bar.setText(filename)

    # Function to save current site to user's local storage

    def save_page(self):
        filepath, filter = QFileDialog.getSaveFileName(
            parent=self,
            caption="Save Page As",
            directory="",
            filter="Webpage, complete (*.htm *.html);;Hypertext Markup Language (*.htm *.html);;All files (*.*)",
        )
        try:
            if filter == "Hypertext Markup Language (*.htm *.html)":
                self.tabs.currentWidget().page().save(
                    filepath, format=QWebEngineDownloadItem.MimeHtmlSaveFormat
                )

            elif filter == "Webpage, complete (*.htm *.html)":
                self.tabs.currentWidget().page().save(
                    filepath, format=QWebEngineDownloadItem.CompleteHtmlSaveFormat
                )

        except:
            self.showErrorDlg()

    # Print handler
    def print_this_page(self):
        try:
            handler_print = controllers.printer.PrintHandler()
            handler_print.setPage(self.tabs.currentWidget().page())
            handler_print.print()

        except:
            self.showErrorDlg()

    # Print page with preview
    def print_with_preview(self):
        handler = controllers.printer.PrintHandler()
        handler.setPage(self.tabs.currentWidget().page())
        handler.printPreview()

    # Save as pdf
    def save_as_pdf(self):
        filename, filter = QFileDialog.getSaveFileName(
            parent=self, caption="Save as", filter="PDF File (*.pdf);;All files (*.*)"
        )

        self.tabs.currentWidget().page().printToPdf(filename)

    # doubleclick on empty space for new tab
    def tab_open_doubleclick(self, i):
        print("Tab bar double clicked")
        if i == -1:  # No tab under the click
            self.add_new_tab(QUrl(models.settings.settings_data["newTabPage"]), label="New tab")

    # to update the tab
    def tab_changed(self, i):
        qurl = self.tabs.currentWidget().url()
        self.update_urlbar(qurl, self.tabs.currentWidget())
        self.update_title(self.tabs.currentWidget())

    # to close current tab
    def close_current_tab(self, i):
        if self.tabs.count() < 2:
            # If it's the last tab, close the entire window
            self.close()

        self.tabs.removeTab(i)
    def switch_to_next_tab(self):
        # ... implementation from previous steps ...
        current_index = self.tabs.currentIndex()
        count = self.tabs.count()
        if count > 0:
            next_index = (current_index + 1) % count
            self.tabs.setCurrentIndex(next_index)
    def switch_to_previous_tab(self):
        current_index = self.tabs.currentIndex()
        count = self.tabs.count()
        if count > 0: # Only switch if there are tabs
            # Calculate previous index with wrap-around
            # (current_index - 1 + count) % count handles the wrap from 0 to count-1
            previous_index = (current_index - 1 + count) % count
            self.tabs.setCurrentIndex(previous_index)

    # Update window title
    def update_title(self, views):
        if views != self.tabs.currentWidget():
            return

        title = self.tabs.currentWidget().page().title()

        if 0 > len(title):
            self.setWindowTitle("{} - PICT Browser".format(title))

        else:
            self.setWindowTitle("PICT Browser")

    # function to add new tab
    def add_new_tab(self, qurl=None, label="Blank"):
        print('Opening new tab function called')
        if qurl is None:
            qurl = QUrl(models.settings.settings_data["newTabPage"])

        _browser = QWebEngineView()  # Define the main webview to browse the internet

        # Set page
        _browser.setPage(views.components.custom_web_engine.customWebEnginePage(self.profile, _browser))

        # Full screen enable
        _browser.settings().setAttribute(
            QWebEngineSettings.FullScreenSupportEnabled, True
        )
        _browser.page().fullScreenRequested.connect(lambda request: request.accept())

        _browser.loadProgress.connect(self.loadProgressHandler)

        # _browser.page().WebAction() # This line seems incomplete or incorrect, commenting out

        _browser.settings().setAttribute(QWebEngineSettings.ScreenCaptureEnabled, True)

        i = self.tabs.addTab(_browser, label)
        self.tabs.setCurrentIndex(i)

        # Explicitly update the URL bar for the new tab immediately after making it current
        self.update_urlbar(qurl, _browser)

        _browser.load(qurl)
        self.url_bar.setFocus() # Consider moving this after update_urlbar or keeping it here

        # update url when it's from the correct tab
        _browser.urlChanged.connect(
            lambda qurl, browser=_browser: self.update_urlbar(qurl, browser)
        )

        _browser.loadFinished.connect(
            lambda _, i=i, browser=_browser: self.tabs.setTabText(
                i, browser.page().title()
            )
        )

        # update history when loading finished
        _browser.page().loadFinished.connect(self.updateHistory)

        return _browser


    def showErrorDlg(self):
        dlg = controllers.errors.errorMsg()
        dlg.exec_()

    def about(self):
        self.AboutDialogue = views.components.settings.about.AboutDialog()
        self.AboutDialogue.show()

    # Update address bar to show current pages's url
    def update_urlbar(self, q, _browser=None):
        if _browser != self.tabs.currentWidget():
            # if signal is not from the current tab, then ignore
            return

        if q.toString() == models.settings.settings_data["newTabPage"]:
            self.httpsicon.setPixmap(
                QPixmap(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "info_24.png"))
            )
            self.httpsicon.setToolTip("This is browser's new tab page")
            self.url_bar.clear()

        else:
            if q.scheme() == "https":
                # secure padlock icon
                self.httpsicon.setPixmap(
                    QPixmap(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "security.png"))
                )
                self.httpsicon.setToolTip(
                    "Connection to this is is secure\n\nThis site have a valid certificate"
                )

            elif q.scheme() == "file":
                self.httpsicon.setPixmap(
                    QPixmap(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "info_24.png"))
                )
                self.httpsicon.setToolTip("You are viewing a local or shared file")

            elif q.scheme() == "data":
                self.httpsicon.setPixmap(
                    QPixmap(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "info_24.png"))
                )
                self.httpsicon.setToolTip("You are viewing a local or shared file")

            elif q.scheme() == "pict":
                self.httpsicon.setPixmap(
                    QPixmap(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "security.png"))
                )
                self.httpsicon.setToolTip("You are viewing an internal browser page")

            else:
                # Set insecure padlock
                self.httpsicon.setPixmap(
                    QPixmap(os.path.join(os.path.dirname(__file__), "..", "utils", "resources", "icons", "warning.png"))
                )
                self.httpsicon.setToolTip("Connection to this site may not be secured")

        # if q.toString() == browser.settings_data["newTabPage"]:
        #     self.url_bar.clear()

        self.url_bar.setCursorPosition(0)

    # function to search google from the search box
    def searchWeb(self, text):
        Engine = models.settings.settings_data["defaultSearchEngine"]
        if text:
            if Engine == "Google":
                return "https://www.google.com/search?q=" + "+".join(text.split())

            elif Engine == "Yahoo":
                return "https://search.yahoo.com/search?q=" + "+".join(text.split())

            elif Engine == "Bing":
                return "https://www.bing.com/search?q=" + "+".join(text.split())

            elif Engine == "DuckDuckGo":
                return "https://duckduckgo.com/?q=" + "+".join(text.split())

    """
    function to navigate to url, if the url ends with the domains from the domains tuple,
    then "http://" will be added after what the user have written if not, then it will call
    the searchWeb() function to search bing directly from the search box
    """

    def navigate_to_url(self):
        in_url = self.url_bar.text()
        print('requested for this url: ', in_url)
        url = ""
        """ if the text in the search box endswith one of the domain in the domains tuple, then "http://" will be added
            if the text is pre "http://" or "https://" added, then not"""
        # [0-9A-Za-z]+\.+[A-Za-z0-9]{2}
        if len(str(in_url)) < 1:
            return

        if self.tabs.currentWidget is None:  # To avoid exception
            # If QTabWidget's currentwidget is none, the ignore
            return

        if file_pattern.search(in_url):
            file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), in_url))
            local_url = QUrl.fromLocalFile(file_path)
            self.tabs.currentWidget().load(local_url)
        
        elif pict_scheme_pattern.search(in_url):
            print('found url: ', in_url)
            self.tabs.currentWidget().load(QUrl(in_url))
            return

        elif without_http_pattern.search(in_url) and any(
            [i in in_url for i in ["http://", "https://"]]
        ):
            url = in_url

        elif pattern.search(in_url) and not any(
            i in in_url for i in ("http://", "https://", "file:///")
        ):
            url = "http://" + in_url

        # this will search google
        elif not "/" in in_url:
            url = self.searchWeb(in_url)

        self.tabs.currentWidget().load(QUrl.fromUserInput(url))

    def updateHistory(self):
        title = self.tabs.currentWidget().page().title()
        url = str(self.tabs.currentWidget().page().url())
        url = url[19 : len(url) - 2]
        hour = datetime.datetime.now().strftime("%X")
        day = datetime.datetime.now().strftime("%x")
        date = hour + " - " + day

        data = views.cursor.execute("SELECT * FROM history")
        siteInfoList = data.fetchall()

        for i in range(len(siteInfoList)):
            if url == siteInfoList[i][2]:
                views.cursor.execute("DELETE FROM history WHERE url = ?", [url])

        views.cursor.execute(
            "INSERT INTO history (title,url,date) VALUES (:title,:url,:date)",
            {"title": title, "url": url, "date": date},
        )

        views.connection.commit()

    def openHistory(self):
        self.historyWindow = views.components.settings.history.HistoryWindow()
        self.historyWindow.setWindowFlags(Qt.Popup)
        self.historyWindow.setGeometry(
            int(self.tabs.currentWidget().frameGeometry().width() / 2 + 400),
            70,
            300,
            500,
        )
        self.historyWindow.setContentsMargins(0, 0, 0, 0)
        self.historyWindow.setStyleSheet(
            """
            background-color:#edf4f7;
            """
        )
        self.historyWindow.show()

    def openSiteHistoryClicked(self, url, *args):
        self.tabs.currentWidget().load(url)

    def openSettings(self):
        self.userSettingswindow = views.components.settings.settings.UserSettings()
        self.userSettingswindow.setWindowFlag(Qt.MSWindowsFixedSizeDialogHint)
        self.userSettingswindow.show()

    def get_admin_access(self):
        return self.__admin_access
    
    def set_admin_access(self, val):
        self.__admin_access = val
    
    def get_admin_mode(self):
        return self.__admin_mode
    
    def set_admin_mode(self, val):
        self.__admin_mode = val
    

    # def create_ws_server(self):
    #     try:
    #         self.ws_server = QWebSocketServer("Browser WebSocket Server", QWebSocketServer.NonSecureMode)
    #         if self.ws_server.listen(QHostAddress.Any, 3002):
    #             self.ws_server.newConnection.connect(self.server_on_new_connection)
    #             print('started ws server')
    #         else:
    #             print('failed to start ws server')
    #     except Exception as e:
    #         print('exception in starting ws server: ', e)
    
    # @pyqtSlot()
    # def server_on_new_connection(self):
    #     print('new connection to server')
    #     client = self.ws_server.nextPendingConnection() # this retrieves the next pending connection AS WELL AS accepts it.
    #     # the client is already accepted at a TCP level when this function is being executed, however to accept it at application level
    #     # this function needs to be called to extract the client from network queue and accept it. If this function is not called, the
    #     # connection will eventually timeout and be closed.
    #     self.server_client = client
    #     if client is not None:
    #         client.textMessageReceived.connect(self.server_on_message)
    #         client.disconnected.connect(self.server_on_disconnect)
    #         client.error.connect(self.server_on_error)

    # @pyqtSlot(str)
    # def server_on_message(self, message):
    #     if message[0]=='0':
    #         # secret = json.loads(message[1:]).get('secret', None)
    #         # if secret == self.parent_window.secret:
    #         # accept auth
    #         self.client['auth'] = True
    #         self.server_client.sendTextMessage('6')
    #         print('client authenticated, saved')
    #         # else:
    #         # dont accept, so dont change self.client details to leave it empty / uninitialised.
    #         # in future, could be due to the fact that secret has expired. then send the appropriate message
    #         # pass
    #     else:
    #         if self.client.get('auth', False):
    #             self.server_client.sendTextMessage('5')
    #         else:
    #             print('recieved message from client: ', message)
    #             if message[0]=='2':
    #                 self.server_client.sendTextMessage('3')
    #             elif message[0]=='4':
    #                 print('message: ', message[1:])
    #             elif message[0]=='8':
    #                 print('recieved erro from client: ', message[1:])
    #             else:
    #                 self.server_client.sendTextMessage('8'+json.dumps({
    #                     "error": "send proper message type",
    #                 }))

    #     return
    
    # @pyqtSlot()
    # def server_on_disconnect(self):
    #     return
    
    # def server_on_error(self, error):
    #     print(f"WebSocket ERROR: BLAHBLAH BLAH")
    #     return