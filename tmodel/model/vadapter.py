# -*- coding: utf8 -*-
'''
Created on 2010-9-28

@author: chinple
'''

import re
from tmodel.model.vaction import DynamicAction
class AdapterException(Exception):
    pass
class AdapterFunDecorator:
    isFakeFun = False
    @staticmethod
    def setAttrHandler(obj, adpCls, adapterHandler, adapterReg, adapterInfo):
        if (AdapterFunDecorator.isFakeFun or adapterHandler is not None) and not hasattr(adpCls, '__mtestAdapterInfo__'):
            tempInfo = {}
            for adpName in adapterInfo:
                if not tempInfo.__contains__(adpName):
                    tempInfo[adpName] = adapterInfo[adpName]
            tempInfo['_sys_h'] = adapterHandler
            tempInfo['_sys_r'] = adapterReg
            tempInfo['_sys_n'] = adpCls.__name__
            adpCls.__mtestAdapterInfo__ = tempInfo
            adpCls.__getattribute__ = AdapterFunDecorator.getAttrHandler

    @staticmethod
    def getAttrHandler(obj, name, *args, **kwargs):
        objFun = object.__getattribute__(obj, name)
        if type(objFun).__name__ == 'instancemethod' and re.match(obj.__mtestAdapterInfo__['_sys_r'], name) != None:
            return AdapterFunDecorator(obj, objFun).anyFunHandle
        return objFun

    def __init__(self, obj, objFun):
        self.obj = obj
        self.objFun = objFun

    def anyFunHandle(self, *tupleArg, **jsonArg):
        adpInfo = self.obj.__mtestAdapterInfo__
        if self.isFakeFun:
            result = DynamicAction(self.objFun, tupleArg, jsonArg, adpInfo).getDynamicResult("")
            return result
        h = adpInfo['_sys_h']
        if h is None:
            raise AdapterException("No handler")
        return h(self.obj, self.objFun, tupleArg, jsonArg, adpInfo)
