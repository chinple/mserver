'''
Created on 2011-7-4

@author: chinple
'''
from threading import Thread
import time
import math
import thread
from libs.objop import ArgsOperation
from libs.syslog import slog
from libs.ini import IniConfigure
import os
from libs.parser import toJsonObj
import sys
from tmodel.model.astat import ApiStatistic


class ThreadRunner(Thread):

    def __init__(self, manager, thid, interval):
        Thread.__init__(self, name="s%s" % thid)
        self.manager = manager
        self.thid = thid

        self.degree = 0
        self.interval = interval
        self.isContinue = True

    def run(self):
        while self.isContinue:
            self.manager.runHandler(self.thid, self.degree)
            self.degree += 1
            if self.interval > 0:time.sleep(self.interval)


class StatisticRunner:
    
    def __init__(self, stsHandler, sreport, intervalTps):
        self.stsHandler = stsHandler
        self.sreport = sreport
        self.isRunning = 1

        self.tpsLock = thread.allocate_lock()
        self.sucTps = self.sreport.getStaticTps()
        self.failTps = self.sreport.getStaticTps()
        self.intervalTps = intervalTps
        self.allLatency = [0] * intervalTps
        
        self.threadsCount = 0
        self.showIntTime = 0

        self.curIntTime = 0
        self.resetIntTime = 0
        self.curLatencyIndex = 0
        self.curMaxTps = 0
        self.isDebug = 0

    def runHandler(self, *args, **vargs):
        startTime = time.time()
        e, ret = None, None
        try:
            ret = self.stsHandler(*args, **vargs)
        except Exception as ex:
            e = ex
            if self.isDebug:
                import traceback
                print(traceback.format_exc())
        finally:
            endTime = time.time()
            runTime = endTime - startTime
            sr = self._statisticRunInfo(endTime, runTime, e is None)
            if e: slog.warn("\tPFAIL %s" % ex)
            return sr, ret

    def _statisticRunInfo(self, curTime, runTime, isSuccess):
        intTime, tpsIndex = self.sreport.getStaticTime(curTime)

        self.tpsLock.acquire()
        letencyIndex = self.curLatencyIndex
        self.curLatencyIndex = letencyIndex + 1
        if isSuccess:
            self.sucTps[tpsIndex] += 1
        else:
            self.failTps[tpsIndex] += 1

        isTimeChange = False
        if intTime > self.curIntTime:
            self.curIntTime += 1
            isTimeChange = True
        self.tpsLock.release()

        self.allLatency[letencyIndex % self.intervalTps] = runTime

        if isTimeChange:
            if self.resetIntTime < self.curIntTime:
                self.resetIntTime = self.curIntTime + self.sreport.resetStatistic(tpsIndex, self.sucTps, self.failTps)
            if self.threadsCount > 0: self.notifyTimeChanged(intTime, tpsIndex)

        return isSuccess

    def notifyTimeChanged(self, intTime, tpsIndex):
        curTps = self.sucTps[tpsIndex - 1]
        if curTps > self.curMaxTps:
            self.curMaxTps = curTps

    def reportStatus(self):
        if self.showIntTime < self.curIntTime:
            intervalTps = len(self.allLatency)
            tpsIndex = self.sreport.getStaticIndex(self.showIntTime)
            self.sreport.addTpsLatency(self.stsHandler.__name__, self.showIntTime, self.threadsCount,
                self.sucTps[tpsIndex], self.failTps[tpsIndex], self.curMaxTps, intervalTps, self.allLatency)
            self.showIntTime += 1

            self.curLatencyIndex = 0
            for i in xrange(intervalTps):
                self.allLatency[i] = 0


class ThreadStatisticRunner(StatisticRunner):
    
    def __init__(self, sreport, stsHandler, startThreads, maxThreads, step, expTps, interval):
        StatisticRunner.__init__(self, stsHandler, sreport, sreport.getAbsTps(expTps))

        self.startThreads = startThreads
        self.maxThreads = maxThreads
        self.step = step
    
        self.threadsLock = thread.allocate_lock()
        self.threads = []

        self.overloadThreads = 0
        self.threadsCount = 0
        self.showIntTime = 0
        self.interval = float(interval)

    def increase(self, threads):
        thi = self.threadsCount
        self.threadsLock.acquire()
        try:
            while threads > 0 and self.maxThreads > self.threadsCount:
                threads -= 1
                th = ThreadRunner(self, self.threadsCount, self.interval)
                self.threads.append(th)
                self.threadsCount += 1
        finally:
            self.threadsLock.release()
        for i in range(thi, len(self.threads)):
            self.threads[i].start()

    def stop(self):
        self.isRunning = 0
        for t in self.threads:
            t.isContinue = False

    def getAliveRunner(self):
        c = 0
        for t in self.threads:
            if t.isAlive(): c += 1
        return c

    def notifyTimeChanged(self, intTime, tpsIndex):
        StatisticRunner.notifyTimeChanged(self, intTime, tpsIndex)

        isContinue, isAddThreads = self.sreport.judgeStatus(self, intTime, tpsIndex)
        if not isContinue:
            self.stop()
        if isAddThreads:
            self.increase(self.step)

    def __str__(self):
        return "{0}: tps {1}, threads {2}->{3}/{4}".format(self.stsHandler.__name__,
            self.intervalTps / 2, self.startThreads, self.maxThreads, self.step)


class StressReporter:

    def __init__(self):
        self.launchTime = time.time()
        self.staticSize = 60
        self.setReporter(60)

    def setReporter(self, maxTime, isKeepRunning=False):
        self.maxTime = maxTime
        self.isKeepRunning = isKeepRunning

    def getStaticTps(self):
        return [0] * self.staticSize

    def getStaticTime(self, startTime):
        intTime = int(startTime - self.launchTime) / 2
        return intTime, intTime % self.staticSize

    def getStaticIndex(self, intTime):
        return intTime % self.staticSize

    def resetStatistic(self, curIndex, t1, t2):
        if curIndex > 10 and curIndex < 20:
            isPreHalf = False
        elif curIndex > 40 and curIndex < 50:
            isPreHalf = True
        else:
            return 5

        clearRange = xrange(0, 30)if isPreHalf else xrange(30, 60)
        for i in clearRange:
            t1[i] = 0
            t2[i] = 0
        return 10

    def getAbsTps(self, tps):
        return tps * 2

    def _calcTps(self, tps):
        return tps / 2

    def _percentile(self, values, percent):
        l = len(values)
        if l == 0:
            return 0
        k = (l - 1) * percent / 100.
        i = int(k)
        if i == k:
            v = values[i]
        else:
            v = (values[i] + values[i + 1]) / 2.
        return int(v * 100) / 100.
    
    def addTpsLatency(self, name, showIntTime, threadsCount, sucTps, failTps,
            maxTps, intervalTps, allLatency):
        values = [a for a in allLatency if a > 0]
        values.sort()
        
        if threadsCount == 0:
            f = "{1}    {0}: {3}/{4}(max {5}),\t30={7}s 50={8}s 75={9}s 90={10}s 99={11}s"
        else:
            f = "{1}  {0}: {3}/{4}(max {5}),\t30={7}s 50={8}s 75={9}s 90={10}s 99={11}s,\t{2} threads"
        print(f.
            format(name, showIntTime, threadsCount,
            self._calcTps(sucTps), self._calcTps(failTps), self._calcTps(maxTps), self._calcTps(intervalTps),
            self._percentile(values, 30), self._percentile(values, 50), self._percentile(values, 75),
            self._percentile(values, 90), self._percentile(values, 99)))

    def judgeStatus(self, manager, intTime, tpsIndex):

        isContinue, isAddThreads = True, False
        if intTime >= self.maxTime:
            isContinue = False
        elif tpsIndex >= 4:  # Judge Stable and Increase Stress
            sucA = manager.sucTps[tpsIndex - 1]
            sucB = manager.sucTps[tpsIndex - 2]
            sucC = manager.sucTps[tpsIndex - 3]

            stsStatus = self.__stableStrategy__(sucA, sucB, sucC, manager.intervalTps, manager.step,
                manager.curMaxTps, manager.threadsCount, manager.overloadThreads)
            if stsStatus == 0:
                isContinue = False
            elif stsStatus == 1:
                isAddThreads = True

        return self.isKeepRunning or isContinue, isAddThreads

    def __stableStrategy__(self, sucA, sucB, sucC, intervalTps, step, curMaxTps, threadsCount, overloadThreads):
        staticInterval = sucA / threadsCount * step

        status = 9
        if sucA >= intervalTps and sucB >= intervalTps and sucC >= intervalTps:  # stop for exceed tps
            status = 0
        elif overloadThreads > staticInterval:  # continue for not add
            status = 2
        elif math.sqrt(math.pow(sucA - sucB , 2) + math.pow(sucB - sucC, 2)) < staticInterval:  # stable status
            if abs(sucA - curMaxTps) < staticInterval:
                status = 1  # increase 
            else:
                status = 3  # continue for not add
        return status


class StressScheduler:

    def __init__(self):
        self.pprop = IniConfigure()
        self.sreport = StressReporter()
        self.pstat = ApiStatistic()
        self.managers = {}
        self.ignoreImportExcept = True
        self.setRunnerByArgs(False, ["-r", "show"])

    def setRunnerByArgs(self, isShowMsg, args):
        cArgs, parseMsg, isSuccess = ArgsOperation.parseArgs(list(args), [], toJsonObj, *self.__getDefine())
        if isShowMsg:
            print(parseMsg)
        if not isSuccess:
            sys.exit(-1)
        self.pprop.load(cArgs.config)

        propConf = cArgs.prop
        for sec in propConf:
            if not self.pprop.sections.__contains__(sec): self.pprop.sections[sec] = propConf[sec]
            else:
                for p in propConf[sec]: self.pprop.sections[sec][p] = propConf[sec][p]

        self.mode = cArgs.mode
        self.inPattern = cArgs.__dict__['in']
        self.apiIntervalTps = cArgs.apiIntervalTps
        self.perfArgs = (cArgs.startThreads, cArgs.maxThreads, cArgs.step, cArgs.expTps) if cArgs.isResetPerf else None
        self.sreport.setReporter(cArgs.maxTime, cArgs.isKeepRunning)
        if cArgs.url != "":
            self.__checkCurl(cArgs)
        from libs.refrect import DynamicLoader
        DynamicLoader.getClassFromFile("stressScenario", self.ignoreImportExcept, True, *cArgs.file)

    def __checkCurl(self, cArgs):
        url, body = cArgs.url, cArgs.body
        from server.cclient import curl
        stsHandler = lambda thid, degree: curl(url.replace("{thid}", str(thid)).replace("{degree}", str(degree)),
            body.replace("{thid}", str(thid)).replace("{degree}", str(degree)) if (body and body != "") else None)
        if self.mode == "debug":
            print(stsHandler(0, 0))
        self.addScenario(stsHandler, cArgs.startThreads, cArgs.maxThreads, cArgs.step, cArgs.expTps)

    def __getDefine(self):
        return (("r", "mode", "run|show|debug", 'run'),
            ("t", "file", "files", [], 'list'),
            ("i", "in", "in pattern", ''),
            ("c", "config", "test run config file", "mtest.ini"),
            ("p", "prop", "section.name=value, configure mtest.ini by CMD arguments", [], "prop"),
            
            ("apiIntervalTps", "", 200, 'int'),
            ("maxTime", "", 30, 'int'),
            ("isKeepRunning", "", False, 'bool'),
            
            ("url", "curl URL for stress test, such as http://127.0.0.1/", ''),
            ("body", "post body", ""),

            ("isResetPerf", "reset perf args if true", False, 'bool'),
            ("startThreads", "startThreads of curl stress test", 2, 'int'),
            ("maxThreads", "maxThreads of curl stress test", 30, 'int'),
            ("step", "step of curl stress test", 2, 'int'),
            ("expTps", "expected TPS", 1024, 'int')
        )
        
    def __isInscope__(self, name):
        import re
        return self.inPattern == "" or re.match(self.inPattern, name) is not None

    def getApiRunner(self, stsHandler):
        name = stsHandler.__name__
        try:
            r = self.managers[name]
        except:
            r = StatisticRunner(stsHandler, self.sreport, self.apiIntervalTps)
            self.managers[name] = r
        return r

    def addScenario(self, stsHandler, startThreads, maxThreads, step, expTps, interval):
        if self.perfArgs is not None:
            startThreads , maxThreads , step, expTps = self.perfArgs
        self.managers[stsHandler.__name__] = (ThreadStatisticRunner(self.sreport, stsHandler,
            startThreads , maxThreads , step, expTps, interval))

    def launch(self):
        try:
            self._planch()
        finally:
            self.pstat.finishApi()
            sys.exit(0)

    def _planch(self):
        isRunning = 0
        for m in self.managers.values():
            if self.__isInscope__(m.stsHandler.__name__):
                print(m)
                if self.mode == "debug":
                    m.isDebug = 1
                    print("%s\t%s\n" % ("Passed" if m.runHandler(1, 1)[0] else "Failed", m.stsHandler.__name__))
                elif self.mode != "show":
                    m.increase(m.startThreads)
                    isRunning = 1
                    continue
            m.stop()

        stopwait = 0
        while isRunning and stopwait < 10:
            isRunning, ac = 0, 0
            for m in self.managers.values():
                ac += m.getAliveRunner()
                isRunning = isRunning or m.isRunning
                m.reportStatus()
                time.sleep(0.3)
                if os.path.exists("stop.perf"):
                    print "Stop test for stop.perf"
                    os.system("rm -rf stop.perf")
                    m.stop()
            if not isRunning and ac > 0:
                stopwait += 0.3
                isRunning = 1
        if stopwait > 10: print "Force stop testing"
