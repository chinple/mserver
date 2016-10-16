'''
Created on 2016-10-14

@author: chinple
'''
import time
import base64
from server.chandle import SessionHandlerBase

class LocalSessionContainer:
    def __init__(self, domain=None, expireTime=86400):
        self.domain = domain
        self.expireTime = expireTime
        self.sessionContainers = {}
        
    def getsessionById(self, sessionid):
        session = self.sessionContainers[sessionid]
        if time.time() - session['t'] >= self.expireTime:
            self.sessionContainers.__delitem__(sessionid)
        else:
            return session
 
    def __genrateSessionNameValue(self):
        return base64.encodestring("%s" % time.time()).strip().replace('=', '')

    def hasSession(self, sessionid):
        return self.sessionContainers.__contains__(sessionid)

    def initSession(self, sessionid):
        self.sessionContainers[sessionid] = {'t':time.time(), 'id':sessionid}

    def genrateSession(self, sessionName, path='/', expires=None):
        sessionid = self.__genrateSessionNameValue()
        self.initSession(sessionid)

        sessionCookie = ['%s=%s' % (sessionName, sessionid)]
        if expires is not None:
            sessionCookie.append('Expires=%s' % expires)
        if path is not None:
            sessionCookie.append('Path=%s' % path)
        if self.domain is not None:
            sessionCookie.append('Domain=.%s; HttpOnly' % self.domain)

        return sessionid, "; ".join(sessionCookie)
    
    def removeSession(self, sessionid):
        try:
            self.sessionContainers.__delitem__(sessionid)
        except:pass
        return True

class LocalMemSessionHandler(SessionHandlerBase):
    def __init__(self):
        self.lsc = LocalSessionContainer()
        self.isReuseCookie = True
        self.sessionName = 'cserverid'
        self.ignorePath = ['/cservice/js']
        self.redirectPath = None
    
    def __ignoreMethod__(self, methodName):
        self.ignorePath.append('/cservice/%s/%s' % (self.__class__.__name__, methodName))
    
    def __isNotInSession__(self, reqObj, reqPath, reqParam, isPost):
        # true need close the request
        cookie = reqObj.headers.getheader('Cookie', None)
        sessionid = self._analyzeSession(self.sessionName, cookie)
        if self.__isInvalidSession__(sessionid):
            sessionid = self.__generateSessionCookie(reqObj, reqPath, reqParam)
        return not self._authSession(sessionid, reqObj, reqPath, reqParam)

    def _analyzeSession(self, sessionName, cookie):
        if cookie is None:
            return
        i = cookie.find(sessionName + "=")
        if i >= 0:
            sessionid = cookie[len(sessionName) + 1:]
            j = sessionid.find(";")
            if j > 0:
                sessionid = sessionid[0:j]
            return sessionid

    def __generateSessionCookie(self, reqObj, reqPath, reqParam):
        sessionid, sessionCookie = self.lsc.genrateSession(self.sessionName)
        reqObj.sessionCookie = sessionCookie
        return sessionid

    def __isInvalidSession__(self, sessionid):
        if sessionid is not None:
            if self.lsc.hasSession(sessionid):
                return False
            elif self.isReuseCookie:
                self.lsc.initSession(sessionid)
                return False
        return True

    def _authSession(self, sessionid, reqObj, reqPath, reqParam):
        session = self.lsc.getsessionById(sessionid)
        reqObj.session = session
        if session is None:
            return False
        elif reqPath.startswith(self.sessionUrl) and not self.ignorePath.__contains__(reqPath):
            if self.__checkSessionAuthStatus__(session, reqObj, reqPath, reqParam):
                return True
            else:
                self.__handleUnauthStatus__(session, reqObj, reqPath, reqParam)
                return False
        return True

    def __checkSessionAuthStatus__(self, session, reqObj, reqPath, reqParam):
        return True
    
    def __handleUnauthStatus__(self, session, reqObj, reqPath, reqParam):
        if self.redirectPath:
            reqObj.redirectPath = self.redirectPath
            reqObj.sendResponse("", None, 302)
        else:
            reqObj.sendResponse("UnAuthorized", None, 500)

    def __invalidateSession__(self, sessionid):
        return self.lsc.removeSession(sessionid)
