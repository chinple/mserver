'''
Created on 2012-3-21

@author: chinple
'''
from server.cdriver import ServerDriver
sdriver = ServerDriver()
cprop = sdriver.cprop

# Server api example, see @SampleServerApi:
#
# @cloudModule()
# class SampleServerApi:
#     def emptyCall(self):
#         return "emptyCall"
#     def callWithArgs(self, callId, method="post"):
#         return "callId: %s" % callId
# can be called by http request:
#     host/cservice/SampleServerApi/callWithArgs?callId=1
# run in command:
#    python2.7 run.py server

def cloudModule(handleUrl=None, **moduleInfo):
    # @cloudModule, mark a class as a service see @SampleServerApi
    # imports prop from other obj imports="A.b", after created call method: __setup__
    # proxyConfig={"t":'textarea'}
    def __cloudMiddleFun(moduleCls):
        sdriver.addService(moduleCls, handleUrl, moduleInfo)
        return moduleCls
    return __cloudMiddleFun

def cserviceProxy(handleUrl=None):
    # @cserviceProxy, service proxy handler, route request /api/ to service example:
# @cserviceProxy(handleUrl="/api")
# class ApiService(CserviceProxyBase):
#     pass

    def __cserviceMiddleFun(cserviceCls):
        sdriver.addServiceProxy(cserviceCls, handleUrl)
        return cserviceCls
    return __cserviceMiddleFun

def servering(*args):
    import sys
    if sys.getdefaultencoding() != "utf-8":
        reload(sys)
        eval('sys.setdefaultencoding("utf-8")')
    from libs.objop import StrOperation
    
    if len(args) == 0:
        args = ("-t", sys.argv[0])
    elif len(args) == 1:
        args = ["-t", sys.argv[0]] + StrOperation.splitStr(args[0], " ", '"')
    sdriver.setDriverByArgs(args)
    sdriver.startService()
