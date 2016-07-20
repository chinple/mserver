# -*- coding: utf8 -*-
'''
Created on 2010-9-28

@author: chinple
'''
from libs.objop import ObjOperation

class CodeFactory:
    vmodes = {}
    def __init__(self, vmode):
        self.dactions = []
        self.paramKeyUsed = set()

        self.resetFileInfo()
        self.resetClassInfo()
        self.resetLanFormat()
        
        self.viewer = ObjOperation.tryGetVal(self.vmodes, vmode, ViewBase)(self.resetLanFormat)

    @staticmethod
    def addView(mode, vmodeCls):
        CodeFactory.vmodes[mode] = vmodeCls
    def addAction(self, daction):
        self.dactions.append(daction)
        return len(self.dactions)
    def endFun(self, caseName, sparam, pIndex, searchKey, tcInfo, caseInfo):
        
        self.viewer.resetTestInfo(caseName, pIndex, sparam, tcInfo, searchKey)

        className = self.viewer.testClassNamedView(tcInfo.Name)
        if not self.isCurClsName(className):
            classMeta = self.viewer.testClassMetaView()
    
            baseClass = ObjOperation.tryGetVal(tcInfo, "BaseClass", "")
            imports = ObjOperation.tryGetVal(tcInfo, "Imports", "")
    
            self.resetClassInfo(className, baseClass, classMeta, imports)

        funName = self.viewer.testCaseNamedView(None)
        funReturn = self.viewer.testCaseReturnView()
        funMeta = self.viewer.testCaseMetaView()
        funImpls = []
        for actCalled in self.dactions:
            funImpls += actCalled.getAction()
        self.addFun(funName, funReturn, funMeta, ("", funImpls))

        self.paramKeyUsed.clear()
        self.dactions = []

    def endClass(self, tcInfo):
        self.printCode()

    def endFactory(self):
        pass

    def isCurClsName(self, clsName):
        return self.className == clsName

    def resetFileInfo(self, filePath=None, nameSpace="", baseClass="TestCaseBase", isClassMatchFile=True):
        self.funs = {}
        self.funNames = []
        self.imports = ""

        self.filePath = filePath
        self.nameSpace = nameSpace
        self.baseClass = baseClass
        self.isClassMatchFile = isClassMatchFile

    def resetClassInfo(self, className="", baseClass="", classMeta="", imports=""):
        self.className = className

        self.classMeta = classMeta
        if not self.imports.__contains__(imports):
            self.imports += imports

    def resetLanFormat(self, beginBlock="{", endBlock="}",
            clsFormat="{meta}\npublic class {name} extends {base}{begin}", funFormat="{meta}\n    {ret} {name}({arg}){begin}",
            funMetaLan="    %s", funBodyLan="        %s", clsBodyLan="    %s",
            nameSpaceLan="package %s;", defImports=""):
        self.beginBlock = beginBlock
        self.endBlock = endBlock
        self.clsFormat = clsFormat
        self.funFormat = funFormat
        self.funMeta = funMetaLan
        self.funBody = funBodyLan
        self.clsBody = clsBodyLan

        self.nameSpaceLan = nameSpaceLan
        if defImports != "":
            self.imports = defImports

    def getPath(self):
        return "" if self.filePath == None else self.filePath

    def addFun(self, funName, funReturn, funMeta="", *funImpls):
        metaInfo = ""
        for meta in (funMeta if type(funMeta) == list else (funMeta,)):
            if meta == "":
                continue
            metaInfo += "\n"
            metaInfo += self.funMeta % meta
        self.funNames.append(funName)
        self.funs[funName] = (funReturn, metaInfo, funImpls)

    def printCode(self):
        from tmodel.model.xmlog import TestLogger
        coder = TestLogger(self.filePath)
        if self.nameSpace != "":
            coder.infoText(self.nameSpaceLan, self.nameSpace)
        if self.imports != "":
            coder.infoText(self.imports)

        coder.infoText(self.clsFormat.format(meta=self.classMeta , name=self.className, base=self.baseClass, begin=self.beginBlock))
        for funName in (tuple(self.funNames) if self.isClassMatchFile else self.funNames):
            funReturn, funMeta, funImpls = self.funs[funName]

            if self.isClassMatchFile:
                self.funNames.remove(funName)

            for argDesp, argImpl in funImpls:
                coder.infoText(self.funFormat.format(meta=funMeta, ret=funReturn, name=funName, arg=argDesp, begin=self.beginBlock))

                for impl in (argImpl if type(argImpl) == list else (argImpl,)):
                    coder.infoText(self.funBody, impl)
                coder.infoText(self.clsBody, self.endBlock)

        coder.infoText(self.endBlock)

class ViewBase:
    def __init__(self, lanFormat):
        lanFormat("", "", funFormat="  {name}, param = {meta}",
            clsFormat="{name}:", nameSpaceLan="%s")

    def resetTestInfo(self, caseName, pIndex, param, tcInfo, searchKey):
        self.caseName = caseName
        self.pIndex = pIndex
        self.param = param
        self.tcInfo = tcInfo
        self.testModule = tcInfo.Module
        self.searchKey = searchKey

    def testClassMetaView(self):
        return ""

    def testClassNamedView(self, testClassName):
        return testClassName

    def testCaseReturnView(self):
        return ""

    def testCaseMetaView(self):
        return "%s" % self.param

    def testCaseNamedView(self, actInfo):# general actInfo is None, it's for special test case generated
        return "%s%s" % (self.caseName, self.pIndex if self.pIndex > 0 else '')

    def objectInitView(self, clsName, callName):
        return '%s = %s()' % (callName, clsName)

    def actionCalledView(self, dAct):
        return '%s[S%s] %s%s' % ("\t" if dAct.IsCheck else "", dAct.callId, dAct.ActName, dAct.ActInput)

    def actionReturnView(self, actName, actInfo, callId):
        return 'rsp%s' % callId

    def endView(self):
        pass

class PythonMTestView(ViewBase):

    def __init__(self, lanFormat):
        lanFormat(":", "", "{meta}\ndef {name}({base}){begin}", "{meta}\n    def {name}(self){begin}")

    def testClassMetaView(self):
        return '@model()'

    def testCaseMetaView(self):
        return '@scenario(param=%s)' % self.param

    def testCaseNamedView(self, actInfo):
        return '%s%s' % (ViewBase.testCaseNamedView(self, actInfo), self.pIndex)

    def actionCalledView(self, dAct):
        retInfo = "%s = " % dAct.getReturnName() if dAct.isActive else ""
        callName = ObjOperation.tryGetVal(dAct.adpInfo, "calledName", "")
        if callName != "":
            callName = "%s.%s" % (callName, dAct.ActName)
        else:
            callName = dAct.ActName
        return '%s%s%s' % (retInfo, callName , dAct.ActInput)

CodeFactory.addView("mtest", PythonMTestView)
