import socket
from httplib import HTTPConnection
import time
from libs.syslog import slog, logManager
from server.chandle import CServerHandler, decodeHttpBody, tryGet

def _tryExecute(fun, args, defRet=None):
    try:
        return fun(*args)
    except:
        return defRet

class ProxyHttpHandle:
    localHosts = "%s-%s" % (socket.gethostbyname_ex(socket.gethostname())[0], time.time())

    def __init__(self, poolSize=512):
        self.hostIp = {}
        self.pathIp = None
        self.isMock = True
        self.isDebugMode = CServerHandler.isDebugMode
        self.reloadProxyConfig()
        from multiprocessing.pool import ThreadPool
        self.logPool = ThreadPool(poolSize)

    class NoHostException(Exception):
        pass

    def __getPathProxy__(self, path):
        for p in self.pathIp:
            if path.startswith(p['p']):
                return p

    def __getProxyInfo__(self, headers, address, path):
        ip, port, host = "", 80, ""
        if tryGet(headers, "cfrom", None) != self.localHosts:
            try:  # get by host
                ip = headers["host"].lower()
                ps = ip.split(":")
                if len(ps) == 2:
                    ip, port = ps[0], int(ps[1])
                ps = self.hostIp[ip]
                ip, port, host = ps['ip'], ps['port'], ps['host']
            except:  # get by path
                ps = self.__getPathProxy__(path) if self.pathIp else None
                if ps is None:
                    if self.isDebugMode: slog.warn("Not found proxy: %s \t%s" % (ip, path))
                else:
                    ip, port, host = ps['ip'], ps['port'], ps['host']
        if ip == "":
            if self.isDebugMode: slog.error("No proxy hosts: %s" % headers)
            raise ProxyHttpHandle.NoHostException()
        return ip, port, host

    def __getProxyHeader(self, headers, host):
        pHeaders = {"cfrom":self.localHosts, 'origin':headers['host']}
        for h in headers:
            try:
                v = headers[h]
                if v is not None:
                    if host is not None and h.lower() == "host":
                        v = host
                    pHeaders[h] = v
            except:pass
        return pHeaders

    def __sendProxyRequest(self, reqObj, bbody):
        p = reqObj.path
        ip, port, host = self.__getProxyInfo__(reqObj.headers, reqObj.client_address, p)

        httpServ = HTTPConnection(ip, port)
        httpServ.connect()
        preqHeader = self.__getProxyHeader(reqObj.headers, host)
        httpServ.request(reqObj.command, p, bbody, preqHeader)
        return preqHeader, httpServ.getresponse()

    def __sendResponse(self, reqObj , status, respHeader, body):
        CServerHandler.sendHeaderCode(reqObj, status)
        for rh in respHeader:
            hn = rh[0]
            if hn.lower() == 'transfer-encoding':
                continue
            reqObj.send_header(hn, rh[1])
        reqObj.end_headers()

        reqObj.sendByteBody(body)
        reqObj.wfile.flush()
        reqObj.close()

    def __handleRequest__(self, reqObj, reqPath, reqParam, isPost):
        if isPost:
            reqParam = reqObj.readPostBody()

        isMock, reqAddress, respTime = False, reqObj.client_address, time.time()
        if self.isMock and _tryExecute(self.__isMockRquest__, (reqPath, reqParam, reqObj.headers, reqObj.client_address), False):
            respStatus, wait, resp = self.__getMockResponse__(reqPath, reqParam, reqObj.headers)
            if wait > 0:
                time.sleep(wait)
            isMock, reqHeader, respBody = True, reqObj.headers, bytes(resp)
            respHeader = [("Content-Length", len(respBody)), ("Content-Type", "text/plan;charset=utf-8")]
        else:
            try:
                reqHeader, respObj = self.__sendProxyRequest(reqObj, reqParam if isPost else None)
                respStatus, respHeader, respBody = respObj.status, respObj.getheaders(), respObj.read()
            except ProxyHttpHandle.NoHostException:
                return "/__file__%s" % reqPath
            except Exception as  ex:
                reqHeader, respStatus, respHeader, respBody = reqObj.headers, 555, {}, str(ex)
                slog.error("Fail to proxy %s: %s, %s: %s" % (type(ex), ex, reqPath, reqObj.headers))

        try:
            reqTime = time.time() - respTime
            self.__sendResponse(reqObj, respStatus, respHeader, respBody)
        finally:
            respTime = time.time() - respTime - reqTime
            self.logPool.apply_async(self.__analyzeSession__,
                args=(isMock, reqObj.command, reqPath, reqParam, respBody, reqTime, respTime, respStatus, reqAddress, dict(reqHeader), dict(respHeader)))

    def setMock(self, isMock=""):
        self.isMock = str(isMock).lower() == "true"

    def reloadProxyConfig(self, proxyConfig="localhost=127.0.0.1"):
        # host = toIp toHost:toPort
        try:
            proxyConfig = open(proxyConfig).read()
        except:pass
        for l in proxyConfig.split("\n"):
            l = l.strip()
            if l == "" or l[0] == "#":
                continue
            try:
                toIp, toPort = l.split(":")
                toIp, toPort = toIp.strip(), int(toPort.strip())
            except:
                toIp, toPort = l, 80

            try:
                i = toIp.index("=")
                host, toIp = toIp[0:i].strip(), toIp[i + 1:].strip()
            except:
                host = None

            try:
                i = toIp.index(" ")
                toIp, toHost = toIp[0:i].strip(), toIp[i + 1:].strip()
            except:
                toHost = toIp
            
            if toIp != "" and toHost != "":
                if host == None or host == "":
                    host = toHost
                slog.info("%s\t\t= %s  %s%s" % (host, toIp, toHost, "" if toPort == 80 else (":%s" % toPort)))
                self.__addProxy(host, toIp, toPort, toHost)
        return self.hostIp

    def __addProxy(self, host, toIp, toPort, toHost):
        h = host.lower()
        if h[0] == "/":
            if self.pathIp is None:
                self.pathIp = []
            nph = {"p":h, "ip":toIp, "port":toPort, 'host':toHost}
            for pi in range(len(self.pathIp)):
                ph = self.pathIp[pi]
                if h.startswith(ph['p']):
                    if ph['p'] == h:self.pathIp[pi] = nph
                    else:self.pathIp.insert(pi, nph)
                    return
            self.pathIp.append(nph)
        else:
            self.hostIp[h] = {"ip":toIp, "port":toPort, 'host':toHost}

    def __getSimpleSession__(self, isLogResp, isMock, command,
                reqPath, reqParam, respBody, reqTime, respTime, respStatus,
            reqAddress, reqHeader, respHeader, logRespSize=-1, logAllUrl=""):
        resp = "..."
        if isLogResp:
            try:
                resp = decodeHttpBody(respHeader, respBody)
            except:
                resp = respBody
            if logRespSize > 0 and len(resp) > logRespSize:
                if not logAllUrl.__contains__(reqPath):
                    resp = resp[0:logRespSize] + " ..."

        host, ip = reqHeader['host'], reqAddress[0]
        return "%s %s %s%s%s\n\t%s\n==>[%.3f, %.3f] %s\n" % (ip, command, "MOCK " if isMock else "",
            host, reqPath, reqParam, reqTime, respTime, resp)

    def __analyzeSession__(self, isMock, command, reqPath, reqParam, respBody, reqTime, respTime, respStatus,
            reqAddress, reqHeader, respHeader):
        slog.info(self.__getSimpleSession__(True, isMock, command, reqPath, reqParam, respBody, reqTime, respTime, respStatus, reqAddress, reqHeader, respHeader))

    def __isMockRquest__(self, reqPath, reqParam, reqHeader, reqAddress):
        return False

    def __getMockResponse__(self, reqPath, reqParam, reqHeader):
        return 200, 0, ""

class LogHttpHandle(ProxyHttpHandle):
    '''
# Configuration setting
[proxyLog]
logFolder  = .
logNameHasOrigin = false
fromIps    =  127.0.0.1,127.0.0.2
pathStartswith = /ajax,/interface
pathEndswith   = 
    '''
    def __init__(self):
        ProxyHttpHandle.__init__(self)
        from cserver import cprop
        self.__setFromIpLogPath__(cprop.getVal("proxyLog", "logFolder", "."), cprop.getVal("proxyLog", "fromIps", "."),
            cprop.getVal("proxyLog", "pathStartswith", "."), cprop.getVal("proxyLog", "pathEndswith", "."), cprop.getBool("proxyLog", "logNameHasOrigin", 'true'),
            cprop.getInt("proxyLog", "logRespSize", 1024), cprop.getVal("proxyLog", "logAllUrl", ''))
    # log by ip
    def __setFromIpLogPath__(self, logFolder, fromIps, pathStartswith, pathEndswith, logNameHasOrigin, logRespSize, logAllUrl):
        self.logFolder = logFolder
        self.pathStartswith = pathStartswith.split(",")
        self.pathEndswith = pathEndswith.split(",")
        self.logNameHasOrigin = logNameHasOrigin
        self.logRespSize = int(logRespSize)
        self.logAllUrl = logAllUrl

        ips = []
        for ip in fromIps.split(","):
            if ip.strip() != "":
                ips.append(ip.strip())
        self.fromIps = None if len(ips) == 0 else ips
        for ip in ips:
            ip = ip.strip()
            if ip == "":continue
            import os
            os.system("mkdir -p %s/%s" % (logFolder, ip))

    def resetProxyLogrule(self, pathStartswith="", pathEndswith="", logRespSize=1024, logAllUrl=""):
        if pathStartswith.strip() != "":
            self.pathStartswith = pathStartswith.split(",")
        if pathEndswith.strip() != "":
            self.pathEndswith = pathEndswith.split(",")
        self.logRespSize = int(logRespSize)
        self.logAllUrl = logAllUrl
        return self.pathStartswith, self.pathEndswith

    def __isLogResponse__(self, reqPath, reqParam, respBody):
        for p in self.pathStartswith:
            if reqPath.startswith(p):
                return True
        for p in self.pathEndswith:
            if reqPath.endswith(p):
                return True
        return False

    def __getHostLog__(self, hostInfo):
        return logManager.getLog(hostInfo, "%s/%s.log" % (self.logFolder, hostInfo), logFormat='[%(asctime)s] %(message)s')

    def __analyzeSession__(self, isMock, command, reqPath, reqParam, respBody, reqTime, respTime, respStatus,
            reqAddress, reqHeader, respHeader):
        host, ip = reqHeader['host'], reqAddress[0]
        if self.fromIps is not None and self.fromIps.__contains__(ip):
            hostInfo = "%s/%s" % (ip, host)
        elif self.logNameHasOrigin:
            origin = tryGet(reqHeader, "origin", "").replace("http://", "")
            hostInfo = host if origin == "" else ("%s_%s" % (origin, host))
        else:
            hostInfo = host

        isLogResp = self.__isLogResponse__(reqPath, reqParam, respBody)
        reqInfo = self.__getSimpleSession__(isLogResp, isMock, command, reqPath, reqParam, respBody, reqTime,
            respTime, respStatus, reqAddress, reqHeader, respHeader, self.logRespSize, self.logAllUrl)
        self.__getHostLog__(hostInfo).info(reqInfo)
