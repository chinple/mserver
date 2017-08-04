'''
Created on 2012-3-21

@author: chinple
'''
import os

import socket
from BaseHTTPServer import BaseHTTPRequestHandler
import re
from inspect import getargspec
from urlparse import parse_qsl
import urllib
import time
from json.decoder import JSONDecoder
from json.encoder import JSONEncoder

def tryGet(obj, key, defValue):
    try:
        return obj[key]
    except:
        return defValue

class __ObjEncoder__(JSONEncoder):
    def default(self, obj):
        return str(obj)

_jsd, _jsn = JSONDecoder(), __ObjEncoder__()

def parseRequestParam(paramStr):
    try:
        try:
            return _jsd.decode(paramStr)
        except:
            reqParam = {}
            for name, value in parse_qsl(paramStr):
                reqParam[name] = urllib.unquote(value)
            return reqParam
    except:
        return {}

def decodeHttpBody(headers, body):
    if "gzip" == tryGet(headers, "content-encoding", ""):
        import StringIO
        import gzip
        gzipper = gzip.GzipFile(fileobj=StringIO.StringIO(body))
        body = gzipper.read()
    try:
        return body.decode(headers["Content-Type"].split("charset=")[1])
    except:
        return body

class CServerHandler(BaseHTTPRequestHandler):
    mainpage = None
    webroot = None
    uploadFolder = "."
    rHandler = None  # router handler, set by @createHttpServer
    sessionCookie = None
    session = None
    redirectPath = None
    maxBodySize = 104857600

    def __init__(self, *tupleArg, **jsonArg):
        self.server_version = "CSERVER 1.0"
        BaseHTTPRequestHandler.__init__(self, *tupleArg, **jsonArg)

    def finish(self):
        try:
            BaseHTTPRequestHandler.finish(self)
        except socket.error as ex:
            self.__handle_close_error(ex)

    def __handle_close_error(self, ex):
        self.close_connection = 1
        try:
            self.log_error("Close %s for %s", self.requestline, ex)
        except:
            self.log_error("Close %s for %s", self, ex)
        
    def handle_one_request(self):
        try:
            BaseHTTPRequestHandler.handle_one_request(self)
        except socket.error as ex:
            self.__handle_close_error(ex)

    def do_POST(self):
        self.__handleNoException(True)

    def do_DELETE(self):
        self.__handleNoException(True)

    def do_PUT(self):
        self.__handleNoException(True)

    def do_PATCH(self):
        self.__handleNoException(True)

    def do_GET(self):
        self.__handleNoException(False)

    def __handleNoException(self, isPost):
        reqPath, reqParam = self.path, None
        if not isPost:
            try:
                paramIndex = self.path.index("?")
                reqPath, reqParam = self.path[0:paramIndex], self.path[paramIndex + 1:]
            except:pass

        try:
            self.rHandler.__handleRequest__(self, reqPath, reqParam, isPost)
        except Exception as ex:
            self.sendResponse(ex, None, 555)

    def readPostBody(self):
        try:
            bodySize = int(self.headers['Content-Length'])
        except:  # empty body
            return
        if bodySize > self.maxBodySize:
            raise Exception("Body exceed 1M bytes for: %s" % self.path)
        if bodySize > 0:
            return self.rfile.read(bodySize)    

    def sendHeaderCode(self, respCode):
        if respCode is None:
            respCode = 200

#         self.log_request(respCode)
        if self.request_version != 'HTTP/0.9':
            self.wfile.write("%s %d %s\r\n" % 
                             (self.protocol_version, respCode, ""))
        self.send_header('Server', self.version_string())
        self.send_header('Date', self.date_time_string())

    def sendSimpleHeaders(self, respCode, contentType, contentLength, headers=None):

        self.sendHeaderCode(respCode)
        if self.sessionCookie is not None:
            self.send_header("Set-Cookie", self.sessionCookie)
            self.sessionCookie = None
        if self.redirectPath is not None:
            self.send_header("Location", self.redirectPath)
            self.redirectPath = None
        self.send_header("Content-Type", "text/plain" if contentType is None else contentType)
        self.send_header("Content-Length", contentLength)
        if headers is not None:
            for h in headers:
                self.send_header(h, headers[h])
        self.end_headers()

    def sendByteBody(self, rb):
        rbLen = len(rb)
        maxWriteLen = 1024
        startLen = 0
        endLen = maxWriteLen if rbLen > maxWriteLen else rbLen
        while 1:
            self.wfile.write(rb[startLen: endLen])
            startLen = endLen
            if startLen < rbLen:
                endLen += maxWriteLen
            else:
                break

    def sendByteResponse(self, bresp, contentType=None, respCode=None, headers=None):
        self.sendSimpleHeaders(respCode, contentType, len(bresp), headers)
        self.sendByteBody(bresp)

    def sendResponse(self, resp, contentType=None, respCode=None):
        self.sendByteResponse(bytes(str(resp)), contentType, respCode)

    def sendFileResponse(self, path, filesize, contentType=None, start=None, limit=None, respCode=None, mode="rb"):
        if start is None:
            start = 0
        if limit is None or limit <= 0:
            limit = filesize - start
        elif (filesize - start) < limit:
            limit = filesize - start
        else:
            start = filesize - limit

        self.sendSimpleHeaders(respCode, contentType, limit)
        with open(path, mode) as f:
            if start > 0:
                f.seek(start)
            s = 0
            while s < limit:
                l = f.read(1024 if limit - s > 1024 else (limit - s))
                if l == b'':
                    return
                s += 1024
                self.wfile.write(l)

    def close(self):
        self.close_connection = 1

class RouterHandler:
    # router handler to route Http request to the registered handler
    def __init__(self, defHandler):
        self.handlers = {}
        self.defHandler = defHandler

    def addHandler(self, preUrl, handle):
        if preUrl[0] == "/":
            preUrl = preUrl[1:]
        if handle is not None:
            if preUrl == "":
                self.defHandler = handle
            else:
                self.handlers[preUrl.lower()] = handle

    def getHandler(self, reqPath):
        reqKey, path = reqPath[1:], ""
        for i in xrange(len(reqKey)):
            if reqKey[i] == '/':
                reqKey, path = reqKey[0:i], reqKey[i:]
                break
        try:
            return self.handlers[reqKey.lower()], path
        except:
            return self.defHandler, reqPath

    def __handleRequest__(self, reqObj, reqPath, reqParam, isPost):
        h, reqPath = self.getHandler(reqPath)
        redirect = h.__handleRequest__(reqObj, reqPath, reqParam, isPost)
        if redirect is not None:  # handle request second time
            h2, reqPath = self.getHandler(redirect)
            if h2 != h:
                h2.__handleRequest__(reqObj, reqPath, reqParam, isPost)

class SessionHandlerBase:
    def __isNotInSession__(self, reqObj, reqPath, reqParam, isPost):
        pass

class SessionRouterHandler(RouterHandler):
    def __init__(self, defHandler):
        RouterHandler.__init__(self, defHandler)
        self.sessionHandler = None

    def addHandler(self, preUrl, handle):
        if isinstance(handle, SessionHandlerBase):
            self.sessionHandler = handle
            self.sessionHandler.sessionUrl = preUrl
            return
        return RouterHandler.addHandler(self, preUrl, handle)

    def __handleRequest__(self, reqObj, reqPath, reqParam, isPost):
        if self.sessionHandler is not None:
            if self.sessionHandler.__isNotInSession__(reqObj, reqPath, reqParam, isPost):
                return
        return RouterHandler.__handleRequest__(self, reqObj, reqPath, reqParam, isPost)

class FileHandler:
    def __init__(self):
        self.ctypes = {}
        self.__initCtypes()

    def __initCtypes(self):
        self.addContentType("text/%s", 'xml', "log", "css", 'xsl', 'ini', 'in', 'txt', 'py', 'cpp', 'java', 'md')
        self.addContentType("text/html", 'htm', 'html')
        self.addContentType("application/x-javascript", 'js')
        self.addContentType("application/x-compressed", 'rar', 'zip')
        self.addContentType('application/msword', 'docx', 'doc')
        self.addContentType('application/x-ppt', 'pptx', 'ppt')
        self.addContentType('application/vnd.ms-excel', 'xls', 'csv')
        self.addContentType("image/jpeg", 'jpg', 'bmp', 'jpeg', 'png')

    def __handleRequest__(self, reqObj, reqPath, reqParam, isPost):
        if reqObj.webroot is not None:
            if reqObj.mainpage is not None and reqPath == "/":
                reqPath = reqObj.mainpage
            path = reqObj.webroot + reqPath
            if os.path.exists(path):
                if os.path.isdir(path):
                    return "/file" + reqPath
                else:
                    if reqParam is None:
                        start, limit = None, None
                    else:
                        fp = parseRequestParam(reqParam)
                        start, limit = int(tryGet(fp, "start", 0)), int(tryGet(fp, "limit", 1048576))
                    reqObj.sendFileResponse(path, os.path.getsize(path), self.__getContentType(path), start, limit)
                    return

    def addContentType(self, ctype, *typeNames):
        for typeName in typeNames:
            self.ctypes[typeName] = ctype

    def __getContentType(self, path):
        fileType = "plain"
        fileMatch = re.match(".*\.([^/]+)", path)
        if fileMatch != None:
            fileType = fileMatch.groups()[0].lower().strip()
        try:
            return self.ctypes[fileType].replace("%s", fileType)
        except:
            return "application/%s" % fileType

class FolderHandler:
    def __handleRequest__(self, reqObj, reqPath, reqParam, isPost):
        f = reqObj.webroot + reqPath
        if os.path.exists(f):
            if os.path.isdir(f):
                ftype = tryGet(parseRequestParam(reqParam), "type", 0)
                if ftype == "json":
                    reqObj.sendResponse(_jsn.encode(os.listdir(f)))
                elif ftype == "stat":
                    files = []
                    for a in os.listdir(f):
                        p = "%s/%s" % (f, a)
                        files.append([a, os.path.isdir(p), os.path.getsize(p)])
                    reqObj.sendResponse(_jsn.encode(files))
                else:
                    files = []
                    files.append('<a href="{1}/{0}">{0}<a>'.format("..", reqPath))
                    for f in sorted(os.listdir(f)):
                        files.append('<a href="{1}/{0}">{0}<a>'.format(f, reqPath).replace("//", "/"))
                    reqObj.sendResponse("<br>".join(files), "text/html")
            else:
                return "/__file__%s" % reqPath

class FileUploadHandler:
    def __handleRequest__(self, reqObj, reqPath, reqParam, isPost):
        if reqParam is None:
            try:
                reqParam = reqPath.split("?")[1]
            except:pass
        reqParam = parseRequestParam(reqParam)
        filePath = self.__saveStreamToFile(reqObj, reqParam)
        reqObj.sendResponse(filePath)

    def __saveStreamToFile(self, reqObj, reqParam):
        bodySize = int(reqObj.headers['Content-Length'])

        dataSep, dataEnd, upResult, fileHandler = None, None, [], None
        while bodySize > 0:
            l = reqObj.rfile.readline()
            bodySize -= len(l)
            if dataSep is None or dataSep == l or dataEnd == l:
                dataSep, dataEnd = l, "%s--\r\n" % l.strip()
                if fileHandler is not None:
                    fileHandler.close()
                li, fileHandler = 0, None
            elif li == 1:
                fp, fn = self.__getUploadFilePath__(reqObj.uploadFolder, l, reqParam)
                if fp is None:
                    if fn is not None:
                        upResult.append("drop %s" % fn)
                    break
                else:
                    fileHandler = open(fp, "wb")
                    upResult.append(fn)
            elif fileHandler is not None and li > 3:
                fileHandler.writelines(l)
            li += 1
        return ",".join(upResult)

    def __getUploadFilePath__(self, uploadFolder, fileInfo, reqParam):
        fileName = tryGet(reqParam, 'filename' , None)
        if fileName is None:
            lg = re.match(r'.*filename="(.*)"', fileInfo)
            if lg is not None:
                fileName = lg.groups()[0]
                fileName = fileName[fileName.rfind("/") + 1:]

        filePath = None
        if fileName is not None:
            folder = tryGet(reqParam, 'folder' , "")
            if folder == "":
                folder = uploadFolder
            else:
                folder = "%s/%s" % (uploadFolder, folder)
                if not os.path.exists(folder):os.mkdir(folder)

            filePath = "%s/%s" % (folder, fileName)
            override = tryGet(reqParam, 'override' , "drop")
            if os.path.exists(filePath):
                if override != "override":
                    filePath = None
                if override == "rename":
                    try:
                        fi = fileName.index(".")
                    except:
                        fi = len(fileName)
                    fileName = "%s%s%s" % (fileName[0:fi], time.strftime("-%Y%m%d-%H%M"), fileName[fi:])
                    filePath = "%s/%s" % (uploadFolder, fileName)

        return filePath, fileName

class RedirectException(Exception):pass
class ReturnFileException(Exception):
    def __init__(self, filecontent, contentType="text/txt", filename=None):
        self.message = filecontent
        self.contentType = contentType
        self.filename = filename

class ObjHandler:
    def __init__(self):
        self.objs = {}

    def loadClasses(self, clsInfos, rHandler):
        for moduleCls, handleUrl, moduleInfo in clsInfos:
            obj = self.__addObj(moduleCls, moduleInfo)
            if handleUrl is not None and obj is not None and \
                    rHandler is not None and not rHandler.handlers.__contains__(handleUrl):
                rHandler.addHandler(handleUrl, obj)

        # set rely and setup
        for objName in self.objs:
            obj = self.objs[objName]
            if obj['info'].__contains__('imports'):
                for key in obj['info']['imports'].split(","):
                    try:
                        refobjName, prop = key.split(".")
                        refprop = self.objs[refobjName]['obj'].__dict__[prop]
                    except:
                        raise Exception("No prop found: %s" % key)
                    obj['obj'].__dict__[prop] = refprop

            if hasattr(obj['obj'], '__setup__'):
                getattr(obj['obj'], '__setup__')()

    def __addObj(self, objCls, moduleInfo):
        objName = objCls.__name__
        if not self.objs.__contains__(objName):
            objInfo = { 'obj':objCls(), 'api':{}, 'info':moduleInfo}
            self.objs[objName] = objInfo
            self.__defineApi(objInfo['obj'], objInfo)
            return objInfo['obj']

    def __defineApi(self, moduleObj, objInfo):
        for actName in dir(moduleObj):
            if re.match("[A-z].*", actName) and not actName.__contains__("_"):
                api = eval("moduleObj.%s" % actName)
                try:
                    argspec = getargspec(api)[0]
                except:
                    continue
                if len(argspec) > 0 and argspec[0] == "self":
                    argspec = tuple(argspec[1:])
                    objInfo['api'][actName] = argspec

    def __parseInfoparam(self, reqPath):
        apiFilter = None
        apiLan = "String"
        for f in reqPath.split("/"):
            if f != "":
                if f == "param":
                    apiLan = "Param"
                elif f == "js":
                    apiLan = "Js"
                elif f == 'ajax':
                    apiLan = 'Ajax'
                elif apiFilter is None:
                    apiFilter = f
        return apiFilter, apiLan

    def _infoString(self, apiLan, apiLevel, infos, moduleName=None, apiName=None, minfo=None):
        if apiLevel == 1:
            return []
        elif apiLevel == 2:
            infos.append("%s/" % moduleName)
        elif apiLevel == 3:
            infos.append("\t%s(%s)" % (apiName, ", ".join(minfo['api'][apiName])))
        else:
            return "\n".join(infos)

    def _infoParam(self, apiLan, apiLevel, infos, moduleName=None, apiName=None, minfo=None):
        if apiLevel == 1:
            return {}
        elif apiLevel == 2:
            infos[moduleName] = {}
        elif apiLevel == 3:
            argNames = minfo['api'][apiName]
            defArgs = getargspec(eval("minfo['obj'].%s" % apiName))[3]
            try:
                startIndex = len(defArgs) - len(argNames)
            except:
                startIndex = -99

            args = []
            apiinfo = minfo['info']
            for argName in argNames:
                defV = defArgs[startIndex] if startIndex >= 0 else None
                startIndex += 1
                propDesp = tryGet(apiinfo, argName, {})
                argInfo = {"n":argName, "v":defV, "d":tryGet(propDesp, "d", None),
                    "t":tryGet(propDesp, "t", None), "s":tryGet(propDesp, "s", None),
                    "c":tryGet(propDesp, "c", False), "i":tryGet(propDesp, "i", False)}
                args.append(argInfo)

            apiinfo = tryGet(apiinfo, apiName, {})
            infos[moduleName][apiName] = {"args":args, "desp":tryGet(apiinfo, 'desp', None), "in":tryGet(apiinfo, 'in', None),
            "resp":tryGet(apiinfo, 'resp', None), "out":tryGet(apiinfo, 'out', None), "check":tryGet(apiinfo, 'check', None)}
        else:
            return infos

    def _infoJs(self, apiLan, apiLevel, infos, moduleName=None, apiName=None, minfo=None):
        if apiLevel == 1:
            return []
        elif apiLevel == 2:
            infos.append("%s = {};" % moduleName)
        elif apiLevel == 3:
            argName = ",".join(minfo['api'][apiName])
            funName = "%s.%s = function(%s)" % (moduleName, apiName, argName)
            funDefine = " return cerviceRequest('/cservice/%s/%s', '%s'.split(','), [%s]);" % (moduleName, apiName, argName, argName)
            infos.append("%s{%s};" % (funName, funDefine))
        else:
            return "\n".join(infos)

    def _infoAjax(self, apiLan, apiLevel, infos, moduleName=None, apiName=None, minfo=None):
        if apiLevel == 1:
            return []
        elif apiLevel == 2:
            infos.append("%s = {};" % moduleName)
        elif apiLevel == 3:
            argName = ":,".join(minfo['api'][apiName])
            funName = "%s.%s = function(params, sucCallback, errCallback)" % (moduleName, apiName)
            funDefine = "\n//%s\n return cserviceAjax('/cservice/%s/%s', params, sucCallback, errCallback);" % (argName, moduleName, apiName)
            infos.append("%s{%s};" % (funName, funDefine))
        else:
            return "\n".join(infos)

    def _infoObjs(self, reqPath):
        apiFilter, apiLan = self.__parseInfoparam(reqPath)

        infoHandler = eval("self._info%s" % apiLan)
        infos = infoHandler(apiLan, 1, None)
        for m in self.objs:
            if apiFilter is not None and not m.startswith(apiFilter):
                continue
            infoHandler(apiLan, 2, infos, m)
            minfo = self.objs[m]
            for n in minfo['api']:
                infoHandler(apiLan, 3, infos, m, n, minfo)
        info = infoHandler(apiLan, 4, infos)
        return info if isinstance(info, str) else _jsn.encode(info)

    def __callObjFun__(self, reqPath, reqParam, session, path):
    # return code, result
        try:
            apiModule, apiName = reqPath[1:].split("/")
        except:
            return 1, "Bad module"

        try:
            minfo = self.objs[apiModule]
            api = eval("obj.%s" % apiName, minfo)
        except:
            return 2, "No module"

        try:
            args = minfo['api'][apiName]
            if len(args) == 0:
                r = api()
            else:
                param = parseRequestParam(reqParam)
                if session is None:
                    r = api(**param)
                else:
                    if args.__contains__('__session__'): param['__session__'] = session
                    if args.__contains__('__path__'): param['__path__'] = path
                    r = api(**param)
            return 0, r
        except RedirectException as ex:
            return 302, ex.message
        except ReturnFileException as ex:
            return 4, ex
        except Exception as ex:
            return 3, str(ex)

    def __handleRequest__(self, reqObj, reqPath, reqParam, isPost):
        if isPost:
            reqParam = decodeHttpBody(reqObj.headers, reqObj.readPostBody())
        if reqParam is None:
            reqObj.sendResponse(self._infoObjs(reqPath))
        else:
            ret = self.__callObjFun__(reqPath, reqParam, reqObj.session, reqObj.path)
            if ret[0] == 302:
                reqObj.redirectPath = ret[1]
                reqObj.sendResponse("", None, 302)
            elif ret[0] == 4:
                fex = ret[1]
                headers = None if fex.filename is None else {'content-disposition':"attachment;filename=%s" % fex.filename}
                reqObj.sendByteResponse(bytes(str(fex.message)), fex.contentType, headers=headers)
            else:
                reqObj.sendResponse(_jsn.encode(ret))

class CserviceProxyBase(ObjHandler):
    def __init__(self, objs):
        self.objs = objs
