import json
import re

import requests
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PyQt5.QtCore import QUrl
from controllers.errors import errorMsg
from dotenv import load_dotenv
import os
from typing import TYPE_CHECKING
load_dotenv()

if TYPE_CHECKING:
    from views import main_window

class RequestInterceptor(QWebEngineUrlRequestInterceptor):
    __logged_in: bool = False
    def __init__(self, parent:"main_window.mainWindow"=None):
        super().__init__(parent)
        self.whitelist = []
        self.blacklist = []
        self.update_lists()
        self.parent_window = parent
    
    @classmethod
    def set_login(cls, val):
        cls.__logged_in = val
    
    @classmethod
    def get_login(cls):
        return cls.__logged_in
    
    def interceptRequest(self, info):
        # print('called')
        url = info.requestUrl().toString()
        domain = self.extract_domain(url)
        # print('domain recieved: ', domain)

        if not self.__logged_in and not url.startswith("pict://") and not url.startswith(os.getenv('SERVER_URL')):
            # later add a redircetion to custom page saying you need to first log in
            # or maybe just redirect to the login page bruh.
            self.parent_window.websocket_client.send_message(json.dumps({
                "action": "log",
                "actionType": "INTERNET_ACCESS",
                "description": url,
                "blocked": True,
            }))
            print('blocking: ', url)
            info.block(True)
            return
        
        # check whether access for internal link is authorized.
        if url.startswith("pict://"):
            resource = url.split("pict://")[1]
            if not (self.parent_window.get_admin_access() and self.parent_window.get_admin_mode()):
                if resource == "admin": # append all resources here that non admins should NOT be able to access
                    if self.parent_window.websocket_client.is_connected():
                        self.parent_window.websocket_client.send_message(json.dumps({
                            "action": "log",
                            "actionType": "LOCAL_ACCESS",
                            "description": url,
                            "blocked": True,
                        }))
                    info.block(True)
                    return
            if self.parent_window.websocket_client.is_connected():
                self.parent_window.websocket_client.send_message(json.dumps({
                    "action": "log",
                    "actionType": "LOCAL_ACCESS",
                    "description": url,
                    "blocked": False,
                }))
            return

        # Determine request type
        resource_type = info.resourceType()
        
        # Main frame navigations (user explicitly navigating to a page)
        
        if resource_type == QWebEngineUrlRequestInfo.ResourceTypeMainFrame or info.navigationType() == QWebEngineUrlRequestInfo.NavigationTypeLink or info.navigationType() == QWebEngineUrlRequestInfo.NavigationTypeRedirect or info.navigationType() == QWebEngineUrlRequestInfo.NavigationTypeTyped or info.navigationType() == QWebEngineUrlRequestInfo.NavigationTypeFormSubmitted:
            print('called by mainfraim')
            # Apply strict whitelist/blacklist rules
            if not self.is_url_allowed(domain):
                if resource_type == QWebEngineUrlRequestInfo.ResourceTypeMainFrame :
                    self.parent_window.websocket_client.send_message(json.dumps({
                        "action": "log",
                        "actionType": "INTERNET_ACCESS",
                        "description": url,
                        "blocked": True,
                    }))
                # dlg = errorMsg("Access Denied: This website is not allowed by administrator")
                # dlg.exec_()
                    info.block(True)
                    return
            if resource_type == QWebEngineUrlRequestInfo.ResourceTypeMainFrame:
                self.parent_window.websocket_client.send_message(json.dumps({
                    "action": "log",
                    "actionType": "INTERNET_ACCESS",
                    "description": url,
                    "blocked": False,
                }))
        # else allow everything not initiated explictly
    
    def is_url_allowed(self, domain):
        # Extract the domain
        # print('checking if allowed: ', domain)
        
        # Check blacklist first (explicit deny has priority)
        for pattern in self.blacklist:
            if self.match_pattern(pattern, domain):
                return False
        
        # If using whitelist mode, must match a whitelist entry
        if self.whitelist:
            for pattern in self.whitelist:
                if self.match_pattern(pattern, domain):
                    return True
            # If we have a whitelist but no match, deny by default
            return False
        
        # If no whitelist is active, and not in blacklist, allow
        return True

    def match_pattern(self, pattern, domain):
        # Support regex patterns or basic wildcard matching
        if pattern.startswith("regex:"):
            # print('matching regex patter')
            regex = pattern[6:]
            return re.search(regex, domain) is not None
        else:
            # Convert glob pattern to regex
            # pattern = pattern.replace(".", "\\.").replace("*", ".*")
            # print('checking using sth else: ', pattern, domain, domain==pattern)
            return domain==pattern
            # return re.match(f"^{pattern}$", domain) is not None
    
    def extract_domain(self, url):
        # Basic domain extraction
        url_obj = QUrl(url)
        return url_obj.host()
    
    def update_lists(self):
        response = requests.get(f"{os.getenv('SERVER_URL')}/settings/bw_filter", timeout=15)
        if response.status_code==200:
            data = response.json()
            self.whitelist = data.get('whitelist', {"domains": []})["domains"]
            self.blacklist = data.get('blacklist', {"domains": []})["domains"]

            # print('blacklist set to: ', self.blacklist, type(data.get('blacklist', {"domains": []})["domains"]))
            # print('whitelist set to: ', self.whitelist, type(data.get('whitelist', {"domains": []})["domains"]))
            return True
        else:
            print('fetch failed')
            return False