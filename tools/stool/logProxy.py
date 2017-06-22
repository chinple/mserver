'''
Created on 2016-8-29

@author: chinple
'''
from server.cproxy import LogHttpHandle
from cserver import cloudModule

@cloudModule(handleUrl="/")
class LogHttpProxy(LogHttpHandle):
    def __analyzeSession__(self, isMock, isPost, reqPath, reqParam, respBody,
            reqTime, respTime, respStatus, reqAddress, reqHeader, respHeader):
        self.getHostLog("requestHeader").info(str(dict(reqHeader)))
        LogHttpHandle.__analyzeSession__(self, isMock, isPost, reqPath, reqParam, respBody, reqTime, respTime, respStatus, reqAddress, reqHeader, respHeader)

if __name__ == "__main__":
    from cserver import servering
    servering(" ")
