'''
Created on 2012-3-21

@author: chinple
'''
from server.cdriver import ServerDriver
sdriver = ServerDriver()
cprop = sdriver.cprop

def cloudModule(handleUrl=None, **moduleInfo):
    def __cloudMiddleFun(moduleCls):
        sdriver.addService(moduleCls, handleUrl, moduleInfo)
        return moduleCls
    return __cloudMiddleFun

def cserviceProxy(handleUrl=None):
    def __cserviceMiddleFun(cserviceCls):
        sdriver.addServiceProxy(cserviceCls, handleUrl)
        return cserviceCls
    return __cserviceMiddleFun

def servering(*args):
    from libs.objop import StrOperation
    import sys
    
    if len(args) == 0:
        args = ("-t", sys.argv[0])
    elif len(args) == 1:
        args = ["-t", sys.argv[0]] + StrOperation.splitStr(args[0], " ", '"')
    sdriver.setDriverByArgs(args)
    sdriver.startService()
