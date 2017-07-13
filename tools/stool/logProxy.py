'''
Created on 2016-8-29

@author: chinple
'''
from server.cproxy import LogHttpHandle
from cserver import cloudModule
from server.chandle import parseRequestParam

@cloudModule(handleUrl="/")
class LogHttpProxy(LogHttpHandle):
    urlmockdata = None
    def addUrlMock(self, url, param, resp, isdelete='false'):
        if self.urlmockdata is None: self.urlmockdata = {}
        if isdelete == "true":
            self.urlmockdata.__delitem__(url)
        else:
            self.urlmockdata[url] = {'p':parseRequestParam(param), 'd':resp}
        return self.urlmockdata.keys()

    def _getMockkey(self, reqPath, reqParam):
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
        return urlmmock['d']

    def __analyzeSession__(self, isMock, isPost, reqPath, reqParam, respBody,
            reqTime, respTime, respStatus, reqAddress, reqHeader, respHeader):
        self.getHostLog("requestHeader").info(str(dict(reqHeader)))
        LogHttpHandle.__analyzeSession__(self, isMock, isPost, reqPath, reqParam, respBody, reqTime, respTime, respStatus, reqAddress, reqHeader, respHeader)

if __name__ == "__main__":
    from cserver import servering
    servering(" ")
