import json
import os
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QWidget

import views
import models.settings


class UserSettings(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.settings_data = models.settings.settings_data
        self.default_search_engine = self.settings_data["defaultSearchEngine"]
        self.filterMode = "blacklist"
        self.mainWidget = QWidget(self)

        self.init_ui()
        self.retranslateUi()

    def init_ui(self):
        self.resize(706, 585)
        self.addDefaultSearchEngineSelector()
        self.setFilterMode()

        self.title_label_size = 10

        # Add Settings title
        self.settingsTitle = QtWidgets.QLabel(self.mainWidget)
        self.settingsTitle.setGeometry(QtCore.QRect(10, 10, 71, 21))
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(self.title_label_size)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(50)
        self.settingsTitle.setFont(font)
        self.settingsTitle.setStyleSheet('font: 12pt "Segoe UI";')
        self.settingsTitle.setObjectName("settingsTitle")

        # self.check_box_enable = QtWidgets.QCheckBox("Use same page used in home button in all", self.mainWidget)
        # self.check_box_enable.setGeometry(QtCore.QRect(10, 130, 70, 17))

        # On startup section
        self.onStartupSubTitle = QtWidgets.QLabel(self.mainWidget)
        self.onStartupSubTitle.setGeometry(QtCore.QRect(10, 130, 91, 21))
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(self.title_label_size)
        font.setBold(True)
        font.setWeight(75)
        self.onStartupSubTitle.setFont(font)
        self.onStartupSubTitle.setObjectName("onStartupSubTitle")

        self.onStartupDescription = QtWidgets.QLabel(self.mainWidget)
        self.onStartupDescription.setGeometry(QtCore.QRect(10, 160, 235, 20))
        self.onStartupDescription.setObjectName("onStartupDescription")
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        self.onStartupDescription.setFont(font)

        self.startup_page = QtWidgets.QLineEdit(self.mainWidget)
        self.startup_page.setGeometry(QtCore.QRect(480, 150, 211, 33))
        self.startup_page.setText(self.settings_data["startupPage"])
        self.startup_page.setObjectName("startup_page")

        # Default Engine
        self.defaultEngineTitle = QtWidgets.QLabel(self.mainWidget)
        self.defaultEngineTitle.setGeometry(QtCore.QRect(10, 60, 171, 21))
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(self.title_label_size)
        font.setBold(True)
        font.setWeight(75)
        self.defaultEngineTitle.setFont(font)
        self.defaultEngineTitle.setObjectName("defaultEngineTitle")

        self.defaultEngineDescription = QtWidgets.QLabel(self.mainWidget)
        self.defaultEngineDescription.setGeometry(QtCore.QRect(10, 90, 270, 20))
        self.defaultEngineDescription.setObjectName("defaultEngineDescription")
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        self.defaultEngineDescription.setFont(font)

        # Home page section
        self.homePageTitle = QtWidgets.QLabel(self.mainWidget)
        self.homePageTitle.setGeometry(QtCore.QRect(10, 230, 101, 21))
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(self.title_label_size)
        font.setBold(True)
        font.setWeight(75)
        self.homePageTitle.setFont(font)
        self.homePageTitle.setObjectName("homePageTitle")

        self.homePageDescription = QtWidgets.QLabel(self.mainWidget)
        self.homePageDescription.setGeometry(QtCore.QRect(10, 260, 360, 20))
        self.homePageDescription.setObjectName("homePageDescription")
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        self.homePageDescription.setFont(font)

        # Home page input
        self.home_button_page = QtWidgets.QLineEdit(self.mainWidget)
        self.home_button_page.setGeometry(QtCore.QRect(480, 230, 211, 33))
        self.home_button_page.setText(self.settings_data["homeButtonPage"])
        self.home_button_page.setObjectName("home_button_page")

        # New tab page
        self.newtabPage = QtWidgets.QLabel(self.mainWidget)
        self.newtabPage.setGeometry(QtCore.QRect(10, 330, 101, 21))
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(self.title_label_size)
        font.setBold(True)
        font.setWeight(75)
        self.newtabPage.setFont(font)
        self.newtabPage.setObjectName("newtabPage")

        self.newtabDescription = QtWidgets.QLabel(self.mainWidget)
        self.newtabDescription.setGeometry(QtCore.QRect(10, 360, 320, 20))
        self.newtabDescription.setObjectName("newtabDescription")
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        self.newtabDescription.setFont(font)

        # Page to open on each tab
        self.new_tab_page = QtWidgets.QLineEdit(self.mainWidget)
        self.new_tab_page.setText(self.settings_data["newTabPage"])
        self.new_tab_page.setGeometry(QtCore.QRect(480, 360, 211, 33))
        self.new_tab_page.setObjectName("new_tab_page")

        # Filter options page
        self.filterModeTitle = QtWidgets.QLabel(self.mainWidget)
        self.filterModeTitle.setGeometry(QtCore.QRect(10, 410, 101, 21))
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(self.title_label_size)
        font.setBold(True)
        font.setWeight(75)
        self.filterModeTitle.setFont(font)
        self.filterModeTitle.setObjectName("filterModeTitle")

        self.filterModeDescription = QtWidgets.QLabel(self.mainWidget)
        self.filterModeDescription.setGeometry(QtCore.QRect(10, 440, 320, 20))
        self.filterModeDescription.setObjectName("filterModeDescription")
        font = QtGui.QFont()
        font.setFamily("Segoe UI")
        font.setPointSize(10)
        self.filterModeDescription.setFont(font)

        # Save button
        self.save_settings = QtWidgets.QPushButton(self.mainWidget)
        self.save_settings.setGeometry(QtCore.QRect(572, 540, 121, 33))
        self.save_settings.setObjectName("save_settings")
        self.save_settings.clicked.connect(self.saveChangesToJson)

        # Discard button
        self.discard_changes = QtWidgets.QPushButton(self.mainWidget)
        self.discard_changes.setGeometry(QtCore.QRect(430, 540, 121, 33))
        self.discard_changes.setObjectName("discard_changes")
        self.discard_changes.clicked.connect(self.closeWindow)

        QtCore.QMetaObject.connectSlotsByName(self.mainWidget)

        with open(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "utils", "styles", "settings_style.css")
        ) as f:  # Read styles from settings_style.css
            self.setStyleSheet(f.read())

    # Add drop-down menu to select default search engine
    def addDefaultSearchEngineSelector(self):
        self.searchEngineSelector = QtWidgets.QComboBox(self.mainWidget)
        self.searchEngineSelector.setEnabled(True)
        self.searchEngineSelector.setGeometry(QtCore.QRect(480, 80, 211, 33))

        # Search engines
        self.searchEngineSelector.addItem("Google")
        self.searchEngineSelector.addItem("Yahoo")
        self.searchEngineSelector.addItem("Bing")
        self.searchEngineSelector.addItem("DuckDuckGo")
        self.searchEngineSelector.currentTextChanged.connect(self.addDropDownItemToJson)

        if self.default_search_engine == "Google":
            self.searchEngineSelector.setCurrentIndex(0)
        elif self.default_search_engine == "Yahoo":
            self.searchEngineSelector.setCurrentIndex(1)
        elif self.default_search_engine == "Bing":
            self.searchEngineSelector.setCurrentIndex(2)
        elif self.default_search_engine == "DuckDuckGo":
            self.searchEngineSelector.setCurrentIndex(3)
    
    # Dropdown for choosing between blacklist and whitelist
    def setFilterMode(self):
        self.filterModeSelector = QtWidgets.QComboBox(self.mainWidget)
        self.filterModeSelector.setEnabled(True)
        self.filterModeSelector.setGeometry(QtCore.QRect(480, 440, 211, 33))

        self.filterModeSelector.addItem("Blacklist")
        self.filterModeSelector.addItem("Whitelist")
        self.filterModeSelector.currentTextChanged.connect(self.setFilterModeToJson)

    # Write to json

    def saveChangesToJson(self):  # startup pg
        try:
            if len(self.startup_page.text()) > 0:
                self.settings_data["startupPage"] = self.startup_page.text()
                with open("./models/settings.json", "w") as f:
                    json.dump(self.settings_data, f, indent=2)

            if len(self.home_button_page.text()) > 0:
                self.settings_data["homeButtonPage"] = self.home_button_page.text()
                with open("./models/settings.json", "w") as f:
                    json.dump(self.settings_data, f, indent=2)

            if len(self.new_tab_page.text()) > 0:
                self.settings_data["newTabPage"] = self.new_tab_page.text()
                with open("./models/settings.json", "w") as f:
                    json.dump(self.settings_data, f, indent=2)
        except Exception as e:
            print('error ocurred: ', e)

    def addDropDownItemToJson(self):
        self.settings_data[
            "defaultSearchEngine"
        ] = self.searchEngineSelector.currentText()
        with open("./models/settings.json", "w") as f:
            json.dump(self.settings_data, f, indent=2)

    def setFilterModeToJson(self):
        self.settings_data["filterMode"] = self.filterModeSelector.currentText()
        with open("./models/settings.json", "w") as f:
            json.dump(self.settings_data, f, indent=2)

    def closeWindow(self):
        self.close()

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.settingsTitle.setText(_translate("Form", "Settings"))
        self.onStartupSubTitle.setText(_translate("Form", "On startup"))
        self.onStartupDescription.setText(
            _translate("Form", "Choose what page to display on startup")
        )
        self.defaultEngineTitle.setText(_translate("Form", "Default Search Engine"))
        self.defaultEngineDescription.setText(
            _translate("Form", "Default search engine used in the address bar")
        )
        self.homePageTitle.setText(_translate("Form", "Home button"))
        self.homePageDescription.setText(
            _translate("Form", "Choose what page to navigate when home button is pressed")
        )
        self.newtabPage.setText(_translate("Form", "New tab"))
        self.newtabDescription.setText(
            _translate("Form", "Choose what page to show when a new tab is opened")
        )
        self.filterModeTitle.setText(_translate("Form", "Filter mode"))
        self.filterModeDescription.setText(
            _translate("Form", "Choose between blacklist or whitelist mode")
        )
        self.discard_changes.setText(_translate("Form", "Discard changes"))
        self.save_settings.setText(_translate("Form", "Save settings"))