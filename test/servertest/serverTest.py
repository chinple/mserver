'''
Created on 2015-7-10

@author: chinple
'''
from cserver import cloudModule, servering, cserviceProxy
# from server.cproxy import HttpHandle
import time
from server.chandle import CserviceProxyBase

# @cloudModule(handleUrl="/ajax")
# class HttpMock(HttpHandle):
# 
#     def __analyzeSession__(self, isPost, reqPath, reqParam, respBody, reqTime, respTime, respStatus, reqHeader, respHeader):
#         print(reqPath, isPost, reqParam, respBody, reqTime, respTime, respStatus, reqHeader, respHeader)

@cserviceProxy(handleUrl="/interface")
class InterfaceService(CserviceProxyBase):
    pass

@cserviceProxy(handleUrl="/api")
class ApiService(CserviceProxyBase):
    pass

@cloudModule()
class SampleServerApi:
    def emptyCall(self):
        return "emptyCall"
    def callWithArgs(self, callId, method="post"):
        return "callId: %s" % callId
    def sleepSeconds(self, t):
        t = int(t)
        if t > 0:
            time.sleep(t)
        return "Sleep: %s" % t

if __name__ == "__main__":
    # --workerSize 5
    servering(" -p 8081 --processes 1 -f D:\\ --uploadFolder D:/tmp")
