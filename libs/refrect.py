'''
Created on 2010-11-8

@author: chinple
'''
import codecs
import sys
import os
from libs.objop import StrOperation, FileOperation

class DictObjOperation:
    def __init__(self, dictObj, storeName, isListOrder=False):
        self.dictObj = dictObj
        self.storeName = os.path.abspath(os.curdir + "/" + storeName)
        self.propInfo = {}
        self.propOrder = [] if isListOrder else None

    def initDict(self, name, valType, initValue=None, propDesp=None):
        self.propInfo[name] = valType
        if self.propOrder != None:
            if propDesp != None:
                self.propOrder.append("# %s" % propDesp)
            if not self.propOrder.__contains__(name):
                self.propOrder.append(name)
        if initValue != None:
            self.SetDict(name, initValue, True)

    def getDict(self, isAll=True):
        dictObj = {}
        for objName in self.dictObj:
            objVal = self.dictObj[objName]
            t = type(objVal)
            if t == str or t == bool or t == int or (isAll and t == dict):
                dictObj[objName] = objVal
        return dictObj

    def setDict(self, name, val, isAdd=False):
        if isAdd or self.dictObj.__contains__(name):
            try:
                valType = self.propInfo[name]
                if valType != None:
                    try:
                        val = valType(val)
                    except:
                        return False
                self.dictObj[name] = val
                return True
            except:pass
        return False

    def toIniStr(self, isOrder=True):
        iniPropStr = ""
        for prop in (self.propOrder if isOrder and self.propOrder != None else self.propInfo.keys()):
            if prop.startswith("#"):
                iniPropStr += "\n%s\n" % prop
            elif prop != "":
                iniPropStr += "%s = %s\n" % (prop, self.dictObj[prop])
        return iniPropStr

    def fromIniStr(self, iniConfig, isInit=False):
        for keyValLine in iniConfig.split("\n"):
            try:
                kvs = StrOperation.splitStr(keyValLine, True)
                name, value = kvs[0], kvs[1]
                if isInit:
                    self.InitDict(name, None, value)
                elif value != "" and name[0] != "#":
                    self.SetDict(name, value)
            except:
                keyValLine = keyValLine.strip()
                if self.propOrder != None and not self.propOrder.__contains__(keyValLine):
                    self.propOrder.append(keyValLine)

    def store(self):
        try:
            with codecs.open(self.storeName, mode='w', encoding="utf-8") as fileHandle:
                fileHandle.write(str(self.GetDict()))
            return True
        except:
            return False

    def recover(self, ignore=""):
        try:
            with codecs.open(self.storeName, mode='r', encoding="utf-8") as fileHandle:
                nameVal = eval(fileHandle.read())
            names = self.dictObj.keys()
            for objName in nameVal:
                if names.__contains__(objName) and not ignore.__contains__(objName):
                    self.dictObj[objName] = nameVal[objName]
            return True
        except:
            return False

class DynamicLoader:

    @staticmethod
    def addSysPath(refDir=""):
        refDir = os.path.abspath(refDir)
        if os.path.isfile(refDir):
            refDir = FileOperation.splitPathName(refDir)[0]
        if os.path.isdir(refDir) and not refDir in sys.path:
            sys.path.insert(0, refDir)

    @staticmethod
    def importClassFromModule(module, importToList, className=None):
        if "module" != type(module).__name__:
            __import__(module)
            module = sys.modules[module]
        for clsName in dir(module):
            obj = getattr(module, clsName)
            if hasattr(obj, "__name__") and not importToList.__contains__(obj):
                if className == None:
                    importToList.append(obj)
                elif obj.__name__ == className:
                    importToList.append(obj)

    @staticmethod
    def getClassFromFile(className=None, ignoreImportExcept=True, *paths):
        for dirPath in paths:
            DynamicLoader.addSysPath(dirPath)

        csList = []
        for filePath in paths:
            if filePath.endswith(".py") or filePath.endswith(".pyc"):
                module = FileOperation.splitPathName(filePath)[1].split(".")[0]
                if ignoreImportExcept:
                    try:
                        DynamicLoader.importClassFromModule(module, csList, className)
                    except:pass
                else:
                    DynamicLoader.importClassFromModule(module, csList, className)
        return csList
