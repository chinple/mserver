# -*- coding: utf8 -*-
'''
Created on 2010-9-28

@author: chinple
'''

import copy
from inspect import getargspec
from libs.objop import ObjOperation, ArgsOperation

def anyValue():
    pass

class DynamicAction:
    actionFactory = None
    def __init__(self, actFun, tupleArg, jsonArg, adpInfo, isCheck=False):
            
        self.ActName , self.ArgNames , self.ActInput = self.__defineInput(actFun, tupleArg, jsonArg, adpInfo)

        self.adpInfo = adpInfo
        self.DespFormat = ""
        self.retDResult = []
        self.isActive = False
        self.IsCheck = isCheck
        self.callId = self.actionFactory.addAction(self)

    def __defineInput(self, actFun, tupleArg, jsonArg, adpInfo):
        actName = ObjOperation.tryGetVal(adpInfo, actFun.__name__, actFun.__name__)
        argspec = getargspec(actFun)
        argNames = argspec.args
        argDefaults = argspec.defaults
        if tupleArg is None:
            cpInput = None
        else:
            cpInput = []
            actInput = ArgsOperation.getTupleArgs(jsonArg, argNames, tupleArg, argDefaults)
            
            for inputArg in actInput:
                try:
                    cpInput.append(copy.deepcopy(inputArg))
                except:
                    cpInput.append(inputArg)
            cpInput = tuple(cpInput)
        return actName, argNames, cpInput

    def getDynamicResult(self, dpath, isDupCheck=True):
        if isDupCheck:
            for dparam in self.retDResult:
                if dparam.dpath == dpath:
                    return dparam

        dparam = DynamicResult(self, dpath)
        self.retDResult.append(dparam)

        return dparam

# code generation
    def getReturnName(self):
        return self.actionFactory.viewer.actionReturnView(self.ActName, self.adpInfo, self.callId)

    def getAction(self):
        
        caller = self.actionFactory.viewer.actionCalledView(self)
        result = [caller]

        if not self.adpInfo.__contains__("calledName"):
            clsName = self.adpInfo['_sys_n']
            self.adpInfo["calledName"] = ObjOperation.tryGetVal(self.adpInfo, "obj", clsName[0].lower() + clsName[1:])
            result.insert(0, self.actionFactory.viewer.objectInitView(clsName, self.adpInfo["calledName"]))

        return result

class DynamicResult:

    def __init__(self, daction, path=""):
        self.daction = daction         
        self.dpath = path
        self.suggestValue(anyValue)

    def suggestValue(self, svalue):
        if type(svalue) == DynamicResult:
            svalue.daction.isActive = True
        self.svalue = svalue

    def __getDValue(self, dpath, isProp):
        if isProp:
            try:
                return self.__dict__[dpath]
            except:pass
        self.daction.isActive = True

        if type(dpath) == int:
            locatorFormat = "%s[%s]"
        elif isProp:
            locatorFormat = "%s.%s"
        else:
            locatorFormat = '%s["%s"]'
        path = locatorFormat % (self.dpath, dpath)

        return self.daction.getDynamicResult(path)

    def __getitem__(self, dpath):
        return self.__getDValue(dpath, False)

    def __getattribute__(self, dpath):
        if dpath.__contains__("_"):
            return object.__getattribute__(self, dpath)
        return self.__getDValue(dpath, True)

# generation
    def __str__(self):
        return "%s%s" % (self.daction.getReturnName(), self.dpath)

    def __repr__(self):
        return str(self)

    def __deepcopy__(self, memo=None):
        return self


