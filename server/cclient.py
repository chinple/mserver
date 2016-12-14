'''
Created on 2012-6-11

@author: chinple
'''
import re
from httplib import HTTPConnection, OK

class HttpRequestConnection(HTTPConnection):
    def putrequest(self, method, url, skip_host=0, skip_accept_encoding=1):
        return HTTPConnection.putrequest(self, method, url, skip_host, skip_accept_encoding)

class RequstException(Exception):pass

class HttpClient:
    def __init__(self, hostport, connTimeout=None, keepAlive=False):

        self.hostport = hostport        
        self.keepAlive = keepAlive

        self.setConn(connTimeout)
        self.setCookie()
        self.setLogInfo()

    def setConn(self, connTimeout):
        try:
            hosts = self.hostport.split(":")
            host = hosts[0]
            port = int(hosts[1])
        except:
            port = 80
        self._httpConn = HttpRequestConnection(host, port)
        if connTimeout is not None:
            self._httpConn.timeout = connTimeout
        self._httpConn.connect()

    def setCookie(self, cookie="", isAnalyzeCookie=False):
        self.cookie = cookie
        self.isAnalyzeCookie = isAnalyzeCookie

    def setLogInfo(self, logHandler=None, logHeader=False, logResp=False):
        self.logHandler = logHandler
        self.logHeader = logHeader
        self.logResp = logResp

    def __makeHeader__(self, headsInfo):
        headers = {"connection":"keep-alive" if self.keepAlive else 'close',
               "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
               "cookie":self.cookie
            }
        if headsInfo is not None:
            for h in headsInfo:
                headers[h] = headsInfo[h]
        return headers

    def __logRequest__(self, command, path, headers, body):
        if self.logHandler is not None:
            reqUrl = "%s:\t%s%s" % (command, self.hostport, path)
            reqHeaders = ("\n  %s" % headers) if self.logHeader else ""
            reqBody = ("\n  %s" % body) if body is not None else ""
            self.logHandler("%s%s%s\n" % (reqUrl, reqHeaders, reqBody))

    def __logResponse__(self, resp):
        if self.logHandler is not None and self.logResp:
            self.logHandler(resp)

    def sendRequest(self, path="/", body=None, command="GET", isReadResp=True, headers=None, isRespHeader=False):
        if isRespHeader:
            hs = {}
            for h, v in response.getheaders():
                hs[h] = v
            return hs, resp
def curl(url, body=None, isReadResp=True, logHandler=None, logHeader=False, logResp=False, isRespHeader=False, connTimeout=None, command=None, client=None, **headers):
        return client.sendRequest(path, body, command, isReadResp, headers, isRespHeader)
