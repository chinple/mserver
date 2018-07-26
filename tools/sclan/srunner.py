# -*- coding: utf8 -*-
'''
Created on 2015 1.26
@author: chinple

Step defined arguments:
# step type
    sysLan = 'lib|cmd'
    sysCmd = ""

# step parameter combination
    sysStrategy = "single|condition|product"
    sysCombine = ""

# step schedule
    sysCondition = ""
    sysTime = 99999
    sysCritical = True
    sysFrom = ""
    sysTo = ""
    sysName = name

Step run directors:
    +10: repeat 10 times
    +p:  run all parameters
    +a:  async run step
    +i:  run indexed parameter
'''

import codecs
import os
from threading import Thread
import time

class StepManager:
    StepKeys = ["sysLan", "sysCmd",
        "sysStrategy", "sysCombine", "sysCondition", "sysTime", "sysCritical",
        "sysFrom", "sysTo"]
    def __init__(self, steps={}, params={}, cases={}):
        self.steps = steps
        self.params = params
        self.cases = cases

        self.refSteps = {}
        self.imports = {}
        self.__files__ = []
        self.SetRun()

    def SetRun(self, runType='default'):
        self.runType = runType

    def Run(self, schedule="run"):
        case = self.__ParseCase__(schedule)
        case.Run(self)
        case.Report()

    def Load(self, stepsPath, encoding):
        imports = self.__LoadFile__(stepsPath, encoding)
        importFiles = imports['file'] if imports.has_key('file') else ''
        while importFiles != "":
            newImports = ""
            for f in importFiles.split(","):
                if os.path.exists(f) and not self.__files__.__contains__(f):
                    self.__files__.append(f)
                    imports = StepManager(self.refSteps, self.params, self.cases).__LoadFile__(f, encoding)
                    newImports += imports['file'] if imports.has_key('file') else ''
            importFiles = newImports

    def __LoadFile__(self, stepsPath, encoding):
        if os.path.exists(stepsPath):
            self.__files__.append(stepsPath)
            with codecs.open(stepsPath, encoding=encoding) as stepsFile:
                StepParser(lambda:stepsFile.readline(), self.AddStepRun).Parse()
        else:
            ls = stepsPath.split("\n")
            il = {'i':0, 'l':len(ls)}
            def NextLine():
                lsIndex = il['i']
                il['i'] = lsIndex + 1
                if lsIndex < il['l']:
                    return ls[lsIndex] + "\n"
                else:
                    return ""
            StepParser(NextLine, self.AddStepRun).Parse()
        return self.imports

    def __ParseCase__(self, schedule):
        return StepScheduleParser(self, self.cases[schedule]).Parse()

    def AddKeyValue(self, keyVals, target):
        for arg in keyVals:
            n = arg[0]
            if target.__contains__(n):
                SRunLog.Warn("Parse: Drop duplicate key %s" , n)
            else:
                target[arg[0]] = arg[1]

    def AddStepRun(self, name, args):
        if name.lower() == "params":
            self.AddKeyValue(args, self.params)
        elif name.lower() == "cases":
            self.AddKeyValue(args, self.cases)
        elif name.lower() == "imports":
            self.AddKeyValue(args, self.imports)
        else:
            s = StepRun(name, args)
            self.steps[s.sysName.lower()] = s

    def FillParam(self, content):
        return content.format(**self.params)

    def GetStepRun(self, name):
        try:
            return self.steps[name.lower()]
        except:pass
        try:
            return self.refSteps[name.lower()]
        except:
            raise SRunException('No step "%s" found in %s' % (name, self.steps.keys()))

    def ToCode(self):
        codes = []
        nvFormat = lambda n, v:"  %s%s = %s" % (n, " "*(15 - len(n)), v)
        def AddStepCode(vals, name):
            if name != None:
                codes.append("\n[%s]" % name)
            if vals != None:
                for n in vals:
                    codes.append(nvFormat(n, vals[n]))
        AddStepCode(self.imports, "imports")
        AddStepCode(self.params, "params")
        AddStepCode(self.cases, "cases")

        for sn in self.steps:
            step = self.steps[sn]
            AddStepCode(None, step.sysName)
            for n in StepManager.StepKeys:
                v = step.__dict__[n]
                if v != "":
                    codes.append(nvFormat(n, v))
            codes.append("")
            for n in step.sysArgsKey:
                codes.append(nvFormat(n, step.sysArgs[n]))
        return "\n".join(codes)

class SRunException(Exception):
    pass

class SRunLog:
    @staticmethod
    def Info(log, *args):
        if len(args) == 0:
            print(log)
        else:
            print(log % args)
    @staticmethod
    def Warn(log, *args):
        if len(args) == 0:
            print(log)
        else:
            print(log % args)
    @staticmethod
    def Debug(log, *args):
        if len(args) == 0:
            print(log)
        else:
            print(log % args)
    @staticmethod
    def Code(log, *args):
        if len(args) == 0:
            print(log)
        else:
            print(log % args)

class StepParser:
    def __init__(self, nextLineHandle, stepAddHandle):
        self.nextLineHandle = nextLineHandle
        self._stepHandle_ = stepAddHandle
        self._InitStep_()
        self._InitEle_()

    def _InitStep_(self):
        self.stepName = None
        self.stepArgs = []
    def _InitEle_(self):
        self.eleName = None
        self.eleValue = ""

    def _AddStep_(self):
        if self.stepName and self.stepName != "":
            self._AddEle_()
            self._stepHandle_(self.stepName, self.stepArgs)
            self._InitStep_()
    def _AddEle_(self):
        if self.eleName:
            self.stepArgs.append((self.eleName, self.eleValue.strip()))
            self._InitEle_()
    def Parse(self):
        while True:
            cl = self.nextLineHandle()
            if cl == "":
                break
            lcl = cl.lstrip()
            lclLen = len(lcl)
            if(lclLen == 0):
                self.eleValue += cl
                continue
            if lcl[0] == '#':
                continue
            elif lcl[0] == '[':
                self._AddStep_()
                lcl = lcl.rstrip()
                self.stepName = lcl[1:len(lcl) - 1]
            else:
                isOldEle = True
                isNotSep = False
                for i in range(0, lclLen):
                    c = lcl[i]
                    if c == "=":
                        if isNotSep:
                            lcl = lcl.replace("\\=", "=")
                        else:
                            isOldEle = False
                            self._AddEle_()
                            self.eleName = lcl[0:i].rstrip()
                            self.eleValue = lcl[i + 1:]
                        break
                    elif c == '\\':
                        isNotSep = True
                    else:
                        isNotSep = False
                if isOldEle:
                    self.eleValue += lcl
        self._AddStep_()

class StepScheduleParser:
    def __init__(self, stepContainer, schedule):
        self.schedule = schedule
        self.scRunner = StepSchedule()
        self.stepContainer = stepContainer

    def _GetStepSchedule_(self, name):
        # check +10, +p, +a +i1
        try:
            argIndex = name.index("+")
            sarg = name[argIndex:].lower()
            runName = name[0:argIndex]
        except:
            runName = name
            sarg = ""

        stepRun = self.stepContainer.GetStepRun(runName)
        if sarg == "":
            return stepRun
        else:
            isSyncRun = sarg.__contains__("a")
            repeatMaxTimes = 0
            repeatAllParam = sarg.__contains__("p")
            paramIndex = 0
            sarg = sarg.replace("+", "").replace("s", "").replace("a", "").replace("p", "")
            try:
                if sarg.__contains__("i"):
                    paramIndex = int(sarg.split("i")[1])
                else:
                    repeatMaxTimes = int(sarg)
            except:
                raise SRunException("Bad director: %s" % name)

            stepSchedule = StepSchedule(isSyncRun, repeatMaxTimes, repeatAllParam, paramIndex)
            stepSchedule.AddSchedule(stepRun)
            return stepSchedule

    def _AddSchedule_(self, name):
        # check sub
        if name.__contains__(";"):
            self.scRunner.AddSchedule(StepScheduleParser(self.stepContainer, name).Parse())
            return
        # check async run
        name = name.split("|")
        if len(name) == 1:
            self.scRunner.AddSchedule(self._GetStepSchedule_(name[0]))
        else:
            scRunner = StepSchedule(False)
            for n in name:
                scRunner.AddSchedule(self._GetStepSchedule_(n))
            self.scRunner.AddSchedule(scRunner)

    def Parse(self):
        name = ""
        wrapCount = 0
        # debug info here
        for c in self.schedule.replace("->", ";"):
            # empty and tuple
            if c == ' ' or c == '\t'or c == '\n':
                continue
            if c == '(':
                if name == '|':
                    self.scRunner.isSyncRun = False
                    name = ""
                wrapCount += 1
                if wrapCount == 1:
                    continue
            if c == ')':
                wrapCount -= 1
                if wrapCount == 0 and len(name) > 0:
                    self._AddSchedule_(name)
                    name = ""
                    continue
            # name
            if wrapCount == 0 and c == ';':
                if name != "":
                    self._AddSchedule_(name)
                name = ""
            else:
                name += c
        if name != '':
            self._AddSchedule_(name)
        return self.scRunner

class StepSchedule:
    def __init__(self, isSyncRun=True, repeatMaxTimes=0, repeatAllParam=False, paramIndex=0):
        self._schedule_ = []
        # run step define: +10, +p, +a +i
        self.isSyncRun = isSyncRun
        self.repeatMaxTimes = repeatMaxTimes
        self.repeatAllParam = repeatAllParam
        self.paramIndex = paramIndex

        # run info
        self._stepResult_ = {}
        self.runCode = 0
        self.runTime = 0
        self.runBTime = 0

    def AddSchedule(self, s):
        self._schedule_.append(s)

    def GetRun(self, condition):
        s = []
        for s in self._schedule_:
            r = s.GetRun(condition)
            if r != None:
                s.append(r)
        if len(s) > 0:
            return s
    def __repr__(self):
        return str(self._schedule_)

    def AddScheduleResult(self, runId, runCode):
        if runCode != 0:
            self.runCode += 1

    def AddStepResult(self, runId, runCode, runEx, bt, rt):
        self._stepResult_[runId] = (runCode, runEx, bt, rt)
        self.AddScheduleResult(runId, runCode)

    def Report(self, lineSpace=""):
        def RoundRt(rt):
            return  round(rt * 100) / 100.
        scInfo = "%s%s%s%s" % ("S" if self.isSyncRun else "A", ("+%s" % self.repeatMaxTimes) if self.repeatMaxTimes > 0 else "",
            "+p" if self.repeatAllParam else "", "+i%s" % self.paramIndex if self.paramIndex else "")
        SRunLog.Info("%s(%s) %s, %s %ss", lineSpace, scInfo,
            self.runCode, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.runBTime)), RoundRt(self.runTime))
        subSpace = "    " + lineSpace
        for runId in range(len(self._schedule_)):
            s = self._schedule_[runId]
            if self._stepResult_.has_key(runId):
                runCode, runEx, bt, rt = self._stepResult_[runId]
                SRunLog.Info((subSpace + "[{sysName}] {0}, {2} {3}s: {1}").format(*(runCode, runEx,
                    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(bt)), RoundRt(rt)), **s.__dict__))
            else:
                s.Report(subSpace)
        return self.runCode

    def Run(self, stepContainer, runId=0, reporter=None):
        self.runBTime = time.time()
        self.__ScheduleRun__(stepContainer)
        self.runTime = time.time() - self.runBTime
        if reporter != None:
            reporter.AddScheduleResult(runId, self.runCode)

    def __ScheduleRun__(self, stepContainer):
        runId = 0
        if self.isSyncRun:
            for s in self._schedule_:
                s.Run(stepContainer, runId, self)
                runId += 1
        else:
            srs = []
            for s in self._schedule_:
                sr = Thread(target=s.Run, args=(stepContainer, runId, self))
                runId += 1
                sr.start()# demo start
                srs.append(sr)
            for sr in srs:
                sr.join()# wait timeout

class StepRun:
    def __init__(self, name, args):
        self.sysArgs = {}
        self.sysArgsKey = []

        # 类型定义
        self.sysLan = 'lib|cmd'
        self.sysCmd = ""
        # 参数定义
        self.sysStrategy = "single|condition|product"
        self.sysCombine = ""
        # 执行调度定义
        self.sysCondition = ""
        self.sysTime = 99999
        self.sysCritical = True
        self.sysFrom = ""
        self.sysTo = ""
        self.sysName = name

        for s in args:
            self._Set_(*s)

    def _Set_(self, k, v):
        if StepManager.StepKeys.__contains__(k):
            if v and v != "":
                self.__dict__[k] = v
        else:
            self.sysArgsKey.append(k)
            self.sysArgs[k] = v

    def GetRun(self, condition):
        return self
    def Run(self, stepContainer, runId, reporter):
        # define run type
        SRunLog.Debug("#[Step] %s running ... with %s", self.sysName, self.sysArgs)
        try:
            runHandle = eval("self.__Run%s__" % (self.sysLan[0].upper() + self.sysLan[1:]))
        except:
            runHandle = self.__RunCmd__
        bt = time.time()
        runCode = 0
        runEx = None
        try:
            runCode = runHandle(stepContainer)
        except Exception as ex:
            runCode = -1
            runEx = ex
        SRunLog.Debug("")
        reporter.AddStepResult(runId, runCode, runEx, bt, time.time() - bt)

    def __RunCmd__(self, stepContainer):
        args = ""
        for k in self.sysArgsKey:
            try:
                v = self.sysArgs[k]
                args += '--%s "%s"' % (k, stepContainer.FillParam(v))
            except Exception as ex:
                SRunLog.Warn("format %s: %s", k, ex)
        cmdStr = "%s %s" % (stepContainer.FillParam(self.sysCmd), args)
        SRunLog.Code(cmdStr)
        if stepContainer.runType != "code":
            return os.system(cmdStr)
    def __RunLib__(self, stepContainer):
        args = ""
        for k in self.sysArgsKey:
            try:
                v = self.sysArgs[k]
                args += '--%s "%s"' % (k, stepContainer.FillParam(v))
            except Exception as ex:
                SRunLog.Warn("format %s: %s", k, ex)
        cmdStr = "%s %s" % (stepContainer.FillParam(self.sysCmd), args)
        SRunLog.Code(cmdStr)
        if stepContainer.runType != "code":
            return os.system(cmdStr)

    def __repr__(self):
        return "%s " % self.sysName

if __name__ == "__main__":
    from optparse import OptionParser
    import sys
    def ParseArgs(args, mustArgs=[], jsonParser=None, *argFormat):
        parser = OptionParser()
        listArgs = []
        boolArgs = []
        intArgs = []
        propArgs = []
        argList = []
        for argf in argFormat:
            argIndex = 0
            soname = argf[0]
            if len(soname) == 1 and soname != '-':
                argIndex += 1
                soname = "-%s" % soname
            else:
                soname = ""
            oname = argf[argIndex]
            argIndex += 1
            ohelp = argf[argIndex]

            if oname.__contains__("-"):
                parser.set_usage(ohelp)
                continue

            argList.append(oname)
            argIndex += 1
            odef = argf[argIndex] if len(argf) > argIndex else ""
            argIndex += 1
            otype = argf[argIndex] if len(argf) > argIndex else None
            ohelp = "%s. %s%s" % (ohelp, (otype if otype != None else "string").upper(), (", default %s" % odef) if odef != "" else "")
            oaction = None
            if otype == "int" or otype == "float":
                intArgs.append(oname)
            elif otype == "list":
                listArgs.append(oname)
                otype = None
                oaction = "append"
            elif otype == "prop":
                propArgs.append(oname)
                otype = None
                oaction = "append"
            elif otype == "bool":
                boolArgs.append(oname)
                otype = None
                odef = "true" == odef or odef == True
                oaction = "store_true"
            parser.add_option(soname, "--%s" % oname, dest=oname, type=otype, action=oaction, help=ohelp, default=odef)
    
        if len(args) == 0:
            args.append("-h")

        isParsed = False
        if type(args) == dict:
            jsonVal = args
            isParsed = True
        elif jsonParser != None and len(args) > 0 and os.path.exists(args[0]):
            jsonVal = jsonParser(args[0])
            isParsed = True
        if isParsed:
            parseValue, leftArgs = parser.parse_args([])
            for oname in argList:
                try:
                    oval = jsonVal[oname]
                except:continue
                if listArgs.__contains__(oname):
                    if type(oval) != list:
                        oval = [oval]
                elif boolArgs.__contains__(oname):
                    oval = oval == True or oval == "true"
                elif intArgs.__contains__(oname):
                    if oval.__contains__("."):
                        oval = float(oval)
                    else:
                        oval = int(oval)
                parseValue.__dict__[oname] = oval
        else:
            parseValue, leftArgs = parser.parse_args(args)

        for oname in propArgs:
            pval = {}
            for propKeyVal in parseValue.__dict__[oname]:
                try:
                    pIndex = propKeyVal.index('=')
                    pval[propKeyVal[0:pIndex]] = propKeyVal[pIndex + 1:]
                except:pass
            parseValue.__dict__[oname] = pval

        isSuccess = True
        parseMsg = ""
        for mustArg in mustArgs:
            if  parseValue.__dict__[mustArg] == "":
                if parseMsg == "":
                    parseMsg = "\nMiss arguments: --%s" % mustArg
                else:
                    parseMsg += ", --%s" % mustArg
                isSuccess = False
    
        if not isSuccess:
            parseMsg = parser.format_help() + parseMsg
        elif len(leftArgs) > 0:
            parseMsg += "\nInvalid argument: %s" % leftArgs
        else:
            for oname in argList:
                oval = parseValue.__dict__[oname]
                if type(oval) == list:
                    for loval in oval:
                        parseMsg += ' --%s "%s"' % (oname, loval)
                elif type(oval) == dict:
                    for prop in oval:
                        parseMsg += ' --%s "%s=%s"' % (oname, prop, oval[prop])
                elif oval != "" and oval != False:
                    parseMsg += ' --%s "%s"' % (oname, oval)

        del parser, listArgs, boolArgs, intArgs, propArgs, argList
        return parseValue, parseMsg, isSuccess
    
    parseValue, parseMsg, isSuccess = ParseArgs(sys.argv, ["confPath"], None,
        ("c", "confPath", "config file path"),
        ("s", "caseName", "case name: key in [cases]", "run"),
        ("r", "runType", "such as default, debug, file(path of log file), code", "code"))
    if not isSuccess:
        print(parseMsg)
        sys.exit(1)

    s = StepManager()
    s.Load(parseValue.confPath, "utf8")
    s.SetRun(parseValue.runType)
    s.Run(parseValue.caseName)
    

