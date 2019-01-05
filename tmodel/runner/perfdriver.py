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
from libs.refrect import DynamicLoader
from mtest import tprop


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
        isSuccess, ret = True, None
        try:
            ret = self.stsHandler(*args, **vargs)
        except Exception as ex:
            slog.warn("FAIL %s" % ex)
            isSuccess = False
            if self.isDebug:
                import traceback
                print(traceback.format_exc())
        endTime = time.time()
        runTime = endTime - startTime

        return self._statisticRunInfo(endTime, runTime, isSuccess), ret

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
        self.threadsLock.acquire()
        while threads > 0 and self.maxThreads > (self.threadsCount + 1):
            threads -= 1
            th = ThreadRunner(self, self.threadsCount, self.interval)
            self.threads.append(th)
            self.threadsCount += 1
            th.start()
        self.threadsLock.release()

    def stop(self):
        self.isRunning = 0
        for t in self.threads:
            t.isContinue = False

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
        self.sreport = StressReporter()
        self.managers = {}
        self.setRunnerByArgs(False, ["-r", "show"])

    def setRunnerByArgs(self, isShowMsg, args):
        cArgs, parseMsg, isSuccess = ArgsOperation.parseArgs(list(args), [], None, *self.__getDefine())
        if isShowMsg:
            print(parseMsg)
        if not isSuccess:
            import sys
            sys.exit(-1)
        tprop.load(cArgs.config)

        self.runMode = cArgs.runMode
        self.inPattern = cArgs.inPattern
        self.apiIntervalTps = cArgs.apiIntervalTps
        self.perfArgs = (cArgs.startThreads, cArgs.maxThreads, cArgs.step, cArgs.expTps) if cArgs.isResetPerf else None
        self.sreport.setReporter(cArgs.maxTime, cArgs.isKeepRunning)
        if cArgs.url != "":
            self.__checkCurl(cArgs)

        DynamicLoader.getClassFromFile("stressScenario", False, *cArgs.stubFiles)

    def __checkCurl(self, cArgs):
        url, body = cArgs.url, cArgs.body
        from server.cclient import curl
        stsHandler = lambda thid, degree: curl(url.replace("{thid}", str(thid)).replace("{degree}", str(degree)),
            body.replace("{thid}", str(thid)).replace("{degree}", str(degree)) if (body and body != "") else None)
        if self.runMode == "debug":
            print(stsHandler(0, 0))
        self.addScenario(stsHandler, cArgs.startThreads, cArgs.maxThreads, cArgs.step, cArgs.expTps)

    def __getDefine(self):
        return (("r", "runMode", "run|show|debug", 'run'),
            ("t", "stubFiles", "files", [], 'list'),
            ("i", "inPattern", "in pattern", ''),
            ("c", "config", "test run config file", "mtest.ini"),
            
            ("apiIntervalTps", "", 200, 'int'),
            ("maxTime", "", 9999999, 'int'),
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
        isRunning = 0
        for m in self.managers.values():
            if self.__isInscope__(m.stsHandler.__name__):
                print(m)
                if self.runMode == "debug":
                    m.isDebug = 1
                    print("%s\t%s\n" % ("Passed" if m.runHandler(1, 1)[0] else "Failed", m.stsHandler.__name__))
                elif self.runMode != "show":
                    m.increase(m.startThreads)
                    isRunning = 1
                    continue
            m.stop()

        while isRunning:
            isRunning = 0
            for m in self.managers.values():
                isRunning = isRunning or m.isRunning
                m.reportStatus()
                time.sleep(0.3)
