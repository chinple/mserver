# -*- coding: utf8 -*-
'''
Created on 2015-8-19

@author: chinple
'''

from cserver import cloudModule
from server.chandle import parseRequestParam
from libs.objop import ObjOperation, StrOperation
from libs.tvg import TValueGroup
from server.cclient import curl, jsonToUrlValue
from libs.parser import toJsonObj
from libs.syslog import plog, slog
from tools.stool.syscmdcurl import CurlCmdWrapper

class HttpToolBase:
    def __replaceArgStr(self, argStr, argRplace):
        try:
            argIndex = 0
            for arg in StrOperation.splitStr(argRplace, ",", "'"):
                argStr = argStr.replace("{%s}" % argIndex, arg)
                argIndex += 1
        except:pass
        return argStr

    def __splitUrl(self, url):
        url = url.replace("http://", "").replace("https://", "")
        try:
            i = url.index("/")
            hosts, path = url[0:i], url[i:]
        except:
            hosts, path = url, ""
        return hosts, path

    def convertUrlParamToJson(self, urlParam, tupeKey="goodsList"):
        pjson = {}
        params = parseRequestParam(urlParam)
        for k in params:
            v = params[k]
            tjson = pjson
            try:
                i = k.index("[")
                key, k = k[0:i], k[i + 1:]
            except:
                pjson[k] = v
                continue

            keys = [key] + k.replace("][", ",").replace("[", "").replace("]", "").split(",")
            for i in range(len(keys)):
                key = keys[i]
                if i < len(keys) - 1:
                    try:
                        tjson = tjson[key]
                    except:
                        if type(tjson) == list:
                            key = int(key)
                            while len(tjson) <= key:
                                tjson.append({})
                            tjson = tjson[key]
                        else:
                            tjson[key] = [] if tupeKey.__contains__(key) else {}
                            tjson = tjson[key]
                else:
                    tjson[key] = v
        return pjson

    def convertJsonToUrlParam(self, jsonStr):
        return jsonToUrlValue(toJsonObj(jsonStr))

    def diffJson(self, jsonStr, jsonStr2):
        return "%s\n%s" % ObjOperation.jsonEqual(TValueGroup(jsonStr).__prop__, TValueGroup(jsonStr2).__prop__)

    def diffUrlParam(self, urlParam, urlParam2, tupeKey="goodsInfoArray"):
        p1 = self.urlParamToJson(urlParam, tupeKey)
        p2 = self.urlParamToJson(urlParam2, tupeKey)
        resp = "%s%s" % ObjOperation.jsonEqual(p1, p2)
        return resp

    def sendHttpRequest(self, url, command="POST", body="", bodyArgs="", hostPort=""):
        if bodyArgs != "":  
            body = self.__replaceArgStr(body, bodyArgs)
        h = {}
        if hostPort != "":
            hosts, path = self.__splitUrl(url)
            h['Host'] = hosts.split(":")[0]
            url = hostPort + path
        resp = curl(url, body, command=command, logHandler=plog.info, ** h)

        try:
            return toJsonObj(resp)
        except:
            return resp

    def sendHttpsRequst(self, url, body, command=None, headers={}, isRespHeader=False, certFile=None):
        import httplib
        import socket
        import ssl
        httpsConn = None    
        certFile = None

        hosts, path = self.__splitUrl(url)
        try:
            httpsConn = httplib.HTTPSConnection(hosts)
            sock = socket.create_connection((httpsConn.host, httpsConn.port))
            try:
                httpsConn.sock = ssl.wrap_socket(sock, ca_certs=certFile, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv23)
            except ssl.SSLError:
                try:
                    httpsConn.sock = ssl.wrap_socket(sock, ca_certs=certFile, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv2)
                except ssl.SSLError:
                    try:
                        httpsConn.sock = ssl.wrap_socket(sock, ca_certs=certFile, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_TLSv1)
                    except ssl.SSLError:
                        try:
                            httpsConn.sock = ssl.wrap_socket(sock, ca_certs=certFile, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv3)
                        except Exception as ex:
                            slog.info("ssl version %s: %s" % (ex, url))      

            httpsConn.request(command, path, body, headers)
            res = httpsConn.getresponse()

            resHeaders = {}
            for k, v in res.getheaders():
                resHeaders[k] = v
            body = res.read()
            try:
                body = toJsonObj(body)
            except:pass
            if isRespHeader:
                return resHeaders, body
            else:
                return body
        finally:
            if httpsConn:
                httpsConn.close

    curlcmd = CurlCmdWrapper()
    def curlHttpRequest(self, url, body, command , headers, isRespHeader, sslVersion= -1):
        headers = toJsonObj(headers)
        command = command.upper()
        isRespHeader = str(isRespHeader).lower() == "true"
        isFormRequest = command.__contains__("FORM")
        if isFormRequest:
            command, body = command.replace("FORM", ''), toJsonObj(body)
            for f in body.keys():
                value = body[f]
                body[f] = self.curlcmd.makeFormValue(f, value, filetype=None)
        return self.curlcmd.curlByCmd(url, body, command, isFormRequest, headers, isRespHeader, isLogResp=False, logHandler=slog.info,
            sslVersion=int(sslVersion))

@cloudModule(urlParam={"t":'textarea'}, param={"t":'textarea'}, svnPath={"t":'textarea'}, urlParam2={"t":'textarea'}, jsonStr={"t":'textarea'}, jsonStr2={"t":'textarea'},
    body={"t":'textarea'},
    urlParamToJson={'desp':"convert url parameter to json"}, jsonToUrlParam={'desp':'convert json to url parameter'})
class HttpToolServer(HttpToolBase):
    pass

if __name__ == "__main__":
    from cserver import servering
    servering(" -p 8080 -n http-tool-test")

