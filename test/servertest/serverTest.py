'''
Created on 2015-7-10

@author: chinple
'''
from cserver import cloudModule, servering, cserviceProxy
# from server.cproxy import HttpHandle
import time
from server.chandle import CserviceProxyBase
from server.csession import LocalMemSessionHandler

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

@cloudModule(handleUrl='/cservice')
class AuthorizSessionHandler(LocalMemSessionHandler):
    def __init__(self):
        LocalMemSessionHandler.__init__(self)
        self.redirectPath = '/testlog.log'
        self.__ignoreMethod__('checkLogin')

    def checkLogin(self, name, password, session):
        session[name] = password
        session['authorized'] = True
        return session

    def logout(self, session):
        return self.__invalidateSession__(session['id'])

    def __checkSessionAuthStatus__(self, session, reqObj, reqPath, reqParam):
        return session.__contains__('authorized')
    

@cloudModule()
class SampleServerApi:
    sessionCallCount = 0
    def emptyCall(self):
        return "emptyCall"

    def callWithArgs(self, callId, method="post"):
        return "callId: %s" % callId

    def callWithSession(self, session):
        session[self.sessionCallCount] = self.sessionCallCount
        self.sessionCallCount += 1
        return session

    def sleepSeconds(self, t):
        t = int(t)
        if t > 0:
            time.sleep(t)
        return "Sleep: %s" % t

if __name__ == "__main__":
    # --workerSize 5
    servering(" -p 8081 --processes 1 -f .")
