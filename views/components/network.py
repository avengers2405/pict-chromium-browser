import re

import requests
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PyQt5.QtCore import QUrl
from controllers.errors import errorMsg
from . import internal_routes

class RequestInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self):
        super().__init__()
        # self.server_url = server_url
        # self.client_id = client_id
        # self.auth_token = auth_token
        self.whitelist = []
        self.blacklist = []
        # Track approved main domains to allow their subresources
        # self.approved_main_domains = set()
        self.update_lists()
    
    def interceptRequest(self, info):
        # print('called')
        url = info.requestUrl().toString()
        # try:
        #     if url.startswith("pict://"):
        #         print('found internal bwrowser path, should not have reached here, idk what to do')
        #         # info.redirect(QUrl(url))
        #         # return internal_routes.get_page(url) # doesnt return anything
        #     else:
        #         # print('not internal route: ', url)
        #         pass
        # except Exception as e:
        #     print('error in interceptRequest() occurred: ', e)

        domain = self.extract_domain(url)
        # print('domain recieved: ', domain)

        # Determine request type
        resource_type = info.resourceType()
        
        # Main frame navigations (user explicitly navigating to a page)
        if resource_type == QWebEngineUrlRequestInfo.ResourceTypeMainFrame:
            print('called by mainfraim')
            # Apply strict whitelist/blacklist rules
            if not self.is_url_allowed(domain):
                dlg = errorMsg("Access Denied: This website is not allowed by administrator")
                dlg.exec_()
                info.block(True)
                # info.redirect(QUrl("about:blank"))
            
        # else allow everything not initiated explictly
    
    def is_url_allowed(self, domain):
        # Extract the domain
        print('checking if allowed: ', domain)
        
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
            print('matching regex patter')
            regex = pattern[6:]
            return re.search(regex, domain) is not None
        else:
            # Convert glob pattern to regex
            # pattern = pattern.replace(".", "\\.").replace("*", ".*")
            print('checking using sth else: ', pattern, domain, domain==pattern)
            return domain==pattern
            # return re.match(f"^{pattern}$", domain) is not None
    
    def extract_domain(self, url):
        # Basic domain extraction
        url_obj = QUrl(url)
        return url_obj.host()
    
    def update_lists(self):
        response = requests.get("http://localhost:3001/settings/bw_filter", timeout=5)
        if response.status_code==200:
            data = response.json()
            self.whitelist = data.get('whitelist', {"domains": []})["domains"]
            self.blacklist = data.get('blacklist', {"domains": []})["domains"]

            print('blacklist set to: ', self.blacklist, type(data.get('blacklist', {"domains": []})["domains"]))
            print('whitelist set to: ', self.whitelist, type(data.get('whitelist', {"domains": []})["domains"]))
            return True
        else:
            print('fetch failed')
            return False