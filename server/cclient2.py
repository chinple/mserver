'''

@author: chinple
'''


def splitUrl(url):
    url = url.replace("http://", "").replace("https://", "")
    try:
        i = url.index("/")
        hosts, path = url[0:i], url[i:]
    except:
        hosts, path = url, ""
    return hosts, path


def httpscurl(url, body, command=None, headers={}, isRespHeader=False, certFile=None):
    import httplib
    import socket
    import ssl
    httpsConn = None    
    if command is None: command = "GET" if body is None else "POST"
    hosts, path = splitUrl(url)
    try:
        httpsConn = httplib.HTTPSConnection(hosts)
        sock = socket.create_connection((httpsConn.host, httpsConn.port))
        try:
            httpsConn.sock = ssl.wrap_socket(sock, ca_certs=certFile, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv23)
        except ssl.SSLError:
            try:
                httpsConn.sock = ssl.wrap_socket(sock, ca_certs=certFile, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_TLSv1_2)
            except ssl.SSLError:
                try:
                    httpsConn.sock = ssl.wrap_socket(sock, ca_certs=certFile, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_TLSv1)
                except ssl.SSLError:
                    try:
                        httpsConn.sock = ssl.wrap_socket(sock, ca_certs=certFile, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv3)
                    except Exception as ex:
                        raise Exception("ssl version %s: %s" % (ex, url))      
    
        httpsConn.request(command, path, body, headers)
        res = httpsConn.getresponse()
    
        resHeaders = {}
        for k, v in res.getheaders():
            resHeaders[k] = v
        body = res.read()

        if isRespHeader:
            return resHeaders, body
        else:
            return body
    finally:
        if httpsConn:
            httpsConn.close


class CurlCmdWrapper:

    def __init__(self, cmdexe, curlPath='/usr/bin/curl'):
        self.curlPath = curlPath
        self.cmdexe = cmdexe

    def makeFormValue(self, name, value, filetype=None):
        if isinstance(value, dict) or isinstance(value, list):
            from libs.parser import toJsonStr
            value = toJsonStr(value)
        return '%s=%s%s' % (name, value, '' if filetype is None else (';type=%s' % filetype))

    def __makeArgs(self, name, value):
        if (value is None or value == ''):return ''
        return " %s '%s'" % (name, str(value).replace("'", "''"))

    def _makeCurlCmd(self, url, curlBody, command, headers, headerFile, isFormRequest, sslVersion):

        header, body, fargs = "", "", ""

        # body
        if isFormRequest:
            for fn in curlBody:
                body += self.__makeArgs("--form", curlBody[fn])
        elif curlBody != '':
            body = self.__makeArgs("-d", curlBody)

        # header
        if headers is not None:
            for h in headers.keys():
                header += self.__makeArgs("-H" , "%s:%s" % (h, headers[h]))
        header += self.__makeArgs("-D", headerFile)

        return "{curl} {request} {ssl} '{url}' {body} {fargs} {header}".format(curl=self.curlPath,
            request=self.__makeArgs('--request', command), ssl=('-k -%s' % sslVersion) if sslVersion > 0 else "",
            url=url, body=body, fargs=fargs, header=header)

    def _parseHeaderFile(self, headerFile):
        header = {}
        for l in open(headerFile, 'r').read().split('\r\n'):
            try:
                i = l.index(":")
                header[l[0:i].strip().lower()] = l[i + 1:].strip()
            except:pass
        import os
        os.system("rm -rf %s" % headerFile)
        return header
        
    def curlByCmd(self, url, body=None, command=None, isFormRequest=False, headers=None, isRespHeader=False, isLogResp=True, logHandler=None, sslVersion=-1):
        import time
        from libs.parser import toJsonObj
        from random import randint
        headerFile = ("header-%s-%s.txt" % (time.time(), randint(10, 1000))) if isRespHeader else None
        curlcmd = self._makeCurlCmd(url, body, command, headers, headerFile, isFormRequest, sslVersion)
        if logHandler:
            logHandler(curlcmd)

        resp = self.cmdexe(curlcmd)
        if isLogResp and logHandler:
            logHandler(resp)
        try:
            resp = toJsonObj(str(resp))
        except:pass

        if isRespHeader:
            return self._parseHeaderFile(headerFile), resp
        else:
            return resp
