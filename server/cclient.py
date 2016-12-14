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

        headers = self.__makeHeader__(headers)

        if command == "GET":
            if body != "" and body is not None:
                path = path + "?" + body
            body = None
        elif isinstance(body, str):
            body = body.encode()

        self.__logRequest__(command, path, headers, body)
        self._httpConn.request(command, path, body, headers)
        response = self._httpConn.getresponse()

        if self.isAnalyzeCookie:
            self.cookie = self.__getCookie__(response.getheaders(), "Set-Cookie")
        if isReadResp:
            if response.status == OK:
                resp = self.__readResponse__(response)
            elif response.status == 302:
                resp = "%s %s" % (response.status, response.getheader("Location", ""))
            else:
                resp = self.__readResponse__(response)
        else:
            resp = "AsyncRequest: %s" % response.status

        self.__logResponse__(resp)
        if int(response.status / 100) != 2:
            raise RequstException("Fail(%s) to request %s%s: %s" % (response.status, self.hostport, path, resp))
        if isRespHeader:
            hs = {}
            for h, v in response.getheaders():
                hs[h] = v
            return hs, resp
        return resp

    def __getCookie__(self, headers, cookieName):
        cookies = ""
        for head in headers:
            if head[0] == cookieName:
                cprop = re.match("([A-z]+=[^=]+; )", head[1])
                if cprop != None:
                    cookies += cprop.groups()[0]
        return cookies

    def __readResponse__(self, response):
        resp = response.read()
        try:
            respDecodes = [response.getheader("Content-Type", "").split("charset=")[1]]
        except:
            respDecodes = ["utf-8", "gbk"]
        for respDecode in respDecodes:
            try:
                return resp.decode(respDecode)
            except:pass
        return resp

    def close(self):
        self._httpConn.close()

def curl(url, body=None, isReadResp=True, logHandler=None, logHeader=False, logResp=False, isRespHeader=False, connTimeout=None, command=None, client=None, **headers):
    url = url.replace("http://", "")
    try:
        i = url.index("/")
        hosts, path = url[0:i], url[i:]
    except:
        hosts, path = url, ""
    if client is None:
        client = HttpClient(hosts, connTimeout)
        client.setLogInfo(logHandler, logHeader, logResp)
    if command is None:
        command = "GET" if body is None else "POST"
    try:
        return client.sendRequest(path, body, command, isReadResp, headers, isRespHeader)
    finally:
        client.close()

def curlCservice(hosts, infPath, isGetInfo=False, isCheckResp=False, logHandler=None, curlHeader={}, **args):
    from libs.parser import toJsonStr, toJsonObj
    if isGetInfo:
        resp = curl("%s/cservice/%s" % (hosts, infPath), logHandler=logHandler, **curlHeader)
        try:
            return toJsonObj(resp)
        except:
            return resp

    resp = curl("%s/cservice/%s" % (hosts, infPath), toJsonStr(args), logHandler=logHandler, **curlHeader)
    resp = toJsonObj(resp)
    if isCheckResp:
        if resp[0] != 0:
            raise Exception("Fail to response: %s" % resp[1])
        return resp[1]
    else:
        return resp

def _jsonToUrlValue(value, urlValues, key=""):
    t = type(value)
    def formatKey(k1, k2):
        if k1 == "":
            return k2
        else:
            return "%s[%s]" % (k1, k2)

    if t == list:
        for k in range(len(value)):
            _jsonToUrlValue(value[k], urlValues, formatKey(key , k))
    elif t == dict:
        for k in value:
            _jsonToUrlValue(value[k], urlValues, formatKey(key , k))
    else:
        if value is not None:
            if key != "":
                urlValues.append("%s=%s" % (key, value))
            else:
                urlValues.append(str(value))

def jsonToUrlValue(jsonObj):
    urlValues = []
    _jsonToUrlValue(jsonObj, urlValues)
    return "&".join(urlValues)
