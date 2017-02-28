'''
Created on 2011-2-21

@author: chinple
'''
from inspect import getargspec
from libs.objop import ObjOperation
import sys
import copy
import time
from tmodel.model.casemodel import MTConst, TestCaseFactory
from tmodel.model.paramgen import CombineGroupParam
from libs.syslog import slog

class BaseDriver:
    def __init__(self, tdriver):
        self.tdriver = tdriver
    def initDriver(self, **kwargs):
        self.tdriver.initDriver(**kwargs)
    def runDriver(self, *modelCls):
        self.tdriver.runDriver(*modelCls)
    def endDriver(self):
        self.tdriver.endDriver()

class TestDriver:
    def __init__(self):
        self.tc = TestCaseFactory()
        self.tlog = self.tc.tlog
        self.tassert = self.tc.tassert
        self.setDriver()

    def setDriver(self, endTestHandler=None, endScenarioHandler=None, endModelHandler=None):
        self.endTestHandler = endTestHandler
        self.endScenarioHandler = endScenarioHandler
        self.endModelHandler = endModelHandler

    def initDriver(self, runMode, testrunConfig, logFilePath,
            tcPattern, outTcPattern, propConf, pergroup, rungroup, isbyname, **extConf):
        searchKey = rungroup[0] if len(rungroup) == 1 else None
        self.groupArgs = tcPattern, outTcPattern, searchKey, pergroup, rungroup, isbyname
        self.logFilePath = logFilePath
        self.tc.init(runMode, testrunConfig, logFilePath,
            tcPattern, outTcPattern, searchKey, propConf)

    def endDriver(self):
        pass

    def runDriver(self, *modelTypes):
        gd = GroupTestDriver(self)
        groups = gd.getRunGroups(modelTypes, *self.groupArgs)
        if len(groups) == 0:
            del gd, groups
            return self._rerunDriver(*modelTypes)
        else:
            return groups

    def groupRunDriver(self):
        pass

    def _rerunDriver(self, *modelTypes):
        runinfo = self.__runCases__(*modelTypes)
        if self.tc.isInMode("rerun", 1) and runinfo[MTConst.failed] > 0:
            reruncases = " |".join([cn.split(" ")[0] for cn in runinfo['cases'][MTConst.failed].keys()])
            slog.info("\nRerun %s cases: %s" % (runinfo[MTConst.failed], reruncases))
            self.tc.setRunCase(reruncases)
            self.tc.setRunLog(None if self.logFilePath == "" else ("%s.rerun" % self.logFilePath))
            runinfo = self.__runCases__(*modelTypes)
        return runinfo

    def __runCases__(self, *modelTypes):
        slog.info(time.strftime("%Y-%m-%d %H:%M:%S testing..."))
        for modelType in modelTypes:
            if self.tc.isInMode("run", 1):
                try:
                    tcObj = modelType()
                except Exception as ex:
                    slog.warn('Instance Class: %s with %s' % (modelType, ex))
                    continue
            else:
                tcObj = modelType()

            tcInfo, caseRunList = self.tc.getRunInfo(tcObj.__class__.__name__, tcObj)

            if len(caseRunList) == 0:
                continue

            for caseName in caseRunList:
                if eval("tcObj.%s()" % caseName) == False:
                    return False
                if self.endScenarioHandler != None:
                    self.endScenarioHandler(tcObj, caseName)

            if tcInfo.isTested:
                if self.tc.isInMode("run", 1):
                    try:
                        tcObj.tearDown()
                    except Exception as ex:
                        slog.warn('tearDown Should NOT Fail! %s: %s' % (ex, self.getMTestTraceBack()))
                else:
                    tcObj.tearDown()
            if self.endModelHandler != None:
                self.endModelHandler(tcInfo)

        self.tlog.close()
        return self.tc.report()

    def addModelCls(self, modelClass, testModule, testName, imports, testOrder, searchKey):
        tcInfo = self.tc.getTCInfo(modelClass.__name__)
        for caseFun in dir(modelClass):
            if not MTConst.sysFunReg.isMatch(caseFun):
                if not tcInfo.__contains__(caseFun):
                    tcInfo[caseFun] = {}
        tcInfo.module = testModule
        tcInfo.name = testName if testName != None else modelClass.__name__
        tcInfo.imports = imports
        tcInfo.orders = testOrder
        tcInfo.searchKey = searchKey

    def runScenario(self, tcObj, tcFun, caseName, param, where, group, status, despFormat, searchKey):  # Status is for status modeling
        isInfoExcept = self.tc.isInMode("debug")

        clsName = tcObj.__class__.__name__
        tcInfo = self.tc.getTCInfo(clsName)
        tsInfo = tcInfo[caseName]
        for sKey in tcInfo.searchKey:
            if not searchKey.__contains__(sKey):
                searchKey[sKey] = tcInfo.searchKey[sKey]

        if status != None:
            from tmodel.model.statusmodel import TestModeling
            self.tc.isModeling = True
            modelLauncher = TestModeling(tcObj, ObjOperation.tryGetVal(status, "start", "Start"),
                ObjOperation.tryGetVal(status, "coverage", "all"))
            self.tc.isModeling = False
            param["sPath"] = modelLauncher.generatePaths()

            try:
                where["combine"].append("sPath")
            except:
                where = copy.deepcopy(where)
                where["combine"] = ["sPath"]
            tcFun = modelLauncher.launchTestPath

        try:
            mparam = ObjOperation.tryGetVal(where, "handle", CombineGroupParam)(param, where, group)
        except Exception as ex:
            slog.warn("Fail to generate parameter, case %s\nerror: %s\nparam= %s\nwhere= %s\ngroupParam= %s" % (caseName, "%s %s" % (ex.__class__.__name__, ex), param, where, group))
            return not isInfoExcept
        while True:
            try:
                sparam = mparam.nextParam()
            except Exception as ex:
                sparam = None
                slog.warn("Fail to generate parameter, case %s\nerror: %s\nparam= %s\nwhere= %s\ngroupParam= %s" % (caseName, "%s %s" % (ex.__class__.__name__, ex), param, where, group))

            if sparam is None:
                break

            desp = self.tc.getTCDespcription(sparam, despFormat)
            caseInfo = self.tc.getCaseInfo(tsInfo, sparam.pIndex, desp, searchKey)
            caseFullName = self.tc.getTCFullName(caseName, sparam.pIndex, desp)

            if not self.tc.isInScope(caseFullName, searchKey):
                continue

            if self.tc.isInMode("show", -1):
                caseInfo['r'] = MTConst.passed
                if self.tc.isInMode("param"):
                    slog.info("%s\n%s\n", caseFullName, sparam)
                elif self.tc.isInMode("look"):
                    slog.info("%s\n%s\n%s\n", caseFullName, searchKey, sparam)
                elif self.tc.isInMode("scenario", -1):
                    if self.tc.isInMode("slook"):
                        slog.info("%s\n%s\n%s\n", caseFullName, searchKey, param)
                    tsInfo[0]['d'] = ""
                    return
                continue

            self.tassert.isWarned = False
            tcObj.param = sparam
            caseSimpleName = caseFullName.split(" ")[0]

            slog.info(MTConst.beginTestCaseInfo, caseFullName)
            self.tlog.beginTestCase(clsName, caseSimpleName, desp, sparam, searchKey)

            if  self.tc.isInMode("debug", 1, True):
                resCode, exeTime = self.runTest(tcObj, tcInfo, tcFun, desp, isInfoExcept)
                if isInfoExcept and (resCode == MTConst.failed or resCode >= 3):
                    return False

            if self.endTestHandler != None:
                self.endTestHandler(caseName, sparam, sparam.pIndex, searchKey, tcInfo, caseInfo)

            try:
                resInfo = self.tc.getResInfo(resCode)
            except:
                resCode = MTConst.failed
                resInfo = self.tc.getResInfo(resCode)

            caseInfo['t'] = exeTime
            caseInfo['r'] = resCode

            (slog.warn if resCode == MTConst.failed else slog.info)(MTConst.endTestCaseInfo, resInfo, caseSimpleName)
            self.tlog.endTestCase(caseSimpleName, resInfo, resCode, exeTime)

    def runTest(self, tempObj, tcInfo, tempFun, caseInfo, isInfoExcept):
        resCode = None
        try:
            startTime = time.time()
            if not tcInfo.isTested:
                tempObj.setUp()
                tcInfo.isTested = True

            tempObj.beginTestCase()
            self.debugTest(tempFun, tempObj, tempObj.param)
            tempObj.endTestCase()
            excuteTime = time.time() - startTime
            resCode = MTConst.warned if self.tassert.isWarned else MTConst.passed
        except Exception as ex:
            excuteTime = time.time() - startTime
            exInfo = self.getMTestTraceBack()
            self.tlog.error(exInfo)
            if isInfoExcept:
                slog.warn(exInfo)
            else:
                try:
                    resCode = tempObj.errorHandle(ex, caseInfo)
                except Exception as ex:
                    slog.warn("ErrorHandle Should NOT Fail! MSG:%s" , ex)
                try:
                    tempObj.endTestCase()
                except Exception as ex:
                    slog.warn("EndTestCase Should NOT Fail! MSG:%s" , ex)
            if not isinstance(resCode, int) or resCode <= 3:
                resCode = MTConst.failed
        return resCode, int(excuteTime * 100 + 0.5) / 100.0

    def debugTest(self, tempFun, tempObj, jparam, tparam=tuple()):
        jsonArgs = {}
        for arg in getargspec(tempFun).args:
            val = ObjOperation.tryGetVal(jparam, arg, None)
            if val != None:
                jsonArgs[arg] = val
        tempFun(tempObj, *tparam, **jsonArgs)

    def getMTestTraceBack(self):
        etype, evalue, tb = sys.exc_info()
        if etype == None:
            return ""

        tbInfo = '%s: %s\r\n' % (etype.__name__, evalue)
        while tb is not None:
            co = tb.tb_frame.f_code
            filename = co.co_filename
            if not MTConst.exceptReg.isMatch(filename):
                tbInfo += '  File "%s", line %s, in %s\r\n' % (filename, tb.tb_lineno, co.co_name)
            tb = tb.tb_next
        return tbInfo

class GroupTestDriver(BaseDriver):
    def _calcTestCases(self, modelTypes, tcPattern=None, outTcPattern=None, searchKey=None):
        self.tdriver.tc.setRunCase(tcPattern, outTcPattern, searchKey, "show", True)
        runinfo = self.tdriver.__runCases__(*modelTypes)
        return [cn.split(" ")[0] for cn in runinfo['cases'][MTConst.passed].keys()]

    def getRunGroups(self, modelTypes, tcPattern=None, outTcPattern=None, searchKey=None, pergroup=None, group=None, isbyname=False):
        groups = []
        if pergroup <= 1 and len(group) <= 1:
            return groups

        if pergroup > 1:
            cases = self._calcTestCases(modelTypes, tcPattern, outTcPattern, searchKey)
            curIndex = 0
            while curIndex < len(cases):
                groups.append(" |".join(cases[curIndex:curIndex + pergroup]))
                curIndex += pergroup
        elif len(group) > 1:
            expcases = []
            if outTcPattern is not None and outTcPattern != "":
                expcases.append(outTcPattern)
            for g in group:
                if isbyname:
                    cases = self._calcTestCases(modelTypes, g, " |".join(expcases), searchKey)
                else:
                    cases = self._calcTestCases(modelTypes, None , " |".join(expcases), g)
                if len(cases) > 0:
                    expcases += cases
                    groups.append(" |".join(cases))
        return groups

    def runInProcess(self, groups, loadGroupRun, mtArgs):
        import multiprocessing
        caseruninfo = multiprocessing.Queue()
        for i in range(len(groups)):
            multiprocessing.Process(target=loadGroupRun, name="launch-%s" % i, args=(groups[i], i, mtArgs, caseruninfo)).start()

        for i in range(len(groups)):
            self._addRuninfo(caseruninfo.get())

        self.tdriver.tc.setRunCase(runMode='run')
        self.tdriver.tc.setRunLog(self.tdriver.logFilePath)
        for gi in range(len(groups)):
            with open("group_%s.log" % gi) as glog:
                while True:
                    l = glog.readline()
                    if l == '':break
                    self.tdriver.tc.tlog.infoText(l[0:len(l) - 1])
        slog.info("="*60)
        return self.tdriver.tc.report()

    def _addRuninfo(self, tcInfos):
        self.tdriver.tc.mergeResult(tcInfos, (MTConst.failed, MTConst.passed))
