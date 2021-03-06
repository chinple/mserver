'''
Created on 2016-8-29

@author: chinple
'''
from server.cproxy import LogHttpHandle
from cserver import cloudModule
from server.chandle import parseRequestParam, tryGet

@cloudModule(handleUrl="/", proxyConfig={"t":'textarea'})
class LogHttpProxy(LogHttpHandle):
    urlmockdata = None
    def addUrlMock(self, url, param, resp, status=200, wait=0, isdelete='false'):
        if self.urlmockdata is None: self.urlmockdata = {}
        if isdelete == "true":
            try:
                self.urlmockdata.__delitem__(url)
            except:pass
        else:
            self.urlmockdata[url] = {'p':parseRequestParam(param), 'd':resp, 's':int(status), 'w':float(wait)}
        return self.urlmockdata.keys()

    def _getMockkey(self, reqPath, reqParam):
        reqPath = reqPath.split("?")[0]
        if self.urlmockdata.__contains__(reqPath):
            param = parseRequestParam(reqParam)
            urlmock = self.urlmockdata[reqPath]
            uparam = urlmock['p']
            isMatch = True
            for p in uparam.keys():
                if not (param.__contains__(p) and uparam[p] == param[p]):
                    isMatch = False
                    break
            if isMatch: return urlmock

    def __isMockRquest__(self, reqPath, reqParam, reqHeader, reqAddress):
        if self.urlmockdata is None:return False
        return self._getMockkey(reqPath, reqParam) is not None

    def __getMockResponse__(self, reqPath, reqParam, reqHeader):
        urlmmock = self._getMockkey(reqPath, reqParam)
        return tryGet(urlmmock, 's', 200), tryGet(urlmmock, 'w', 0), urlmmock['d']

    def __analyzeSession__(self, isMock, command, reqPath, reqParam, respBody, reqTime, respTime, respStatus,
            reqAddress, reqHeader, respHeader):
        self.__getHostLog__("requestheader").info("%s %s" % (reqPath, reqHeader))
        try:
            LogHttpHandle.__analyzeSession__(self, isMock, command, reqPath, reqParam, respBody,
                reqTime, respTime, respStatus, reqAddress, reqHeader, respHeader)
        except Exception as ex:
            try:
                LogHttpHandle.__analyzeSession__(self, isMock, command, reqPath, reqParam, "... %s" % (ex),
                    reqTime, respTime, respStatus, reqAddress, reqHeader, respHeader)
            except Exception as ex:
                self.__getHostLog__("logerror").info("%s %s" % (reqPath, ex))
