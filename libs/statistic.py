'''
Created on 2010-11-8

@author: chinple
'''
import codecs
import time
from threading import Thread

class TimmerStatic(Thread):
    def __init__(self, stInterval=2, maxIntTime=3600, argMatchHandle=None, stArg=None, name="MTestStatic", saveTo=None):
        Thread.__init__(self, name=name)
        self.argMatchHandle = argMatchHandle
        self.resetStatistic(stInterval, maxIntTime, stArg)
        try:
            saveTo = codecs.open(saveTo, "a", "utf-8", buffering=0)
        except:saveTo = None
        self.saveTo = saveTo
        self.startTime = time.time()
        self.isRunning = True

        self.start()

    def resetStatistic(self, stInterval, maxIntTime, stArg):

        stInterval = int(stInterval)
        maxIntTime = int(maxIntTime)
        if hasattr(self, 'static'):
            addLen = maxIntTime - len(self.static)
            if addLen > 0:
                self.static = self.static + (addLen + 1) * [0, ]
            else:
                maxIntTime = self.maxIntTime
            if stInterval != self.stInterval:
                self._ClearStatic()
        else:
            self.static = (maxIntTime + 1) * [0, ]
            self.curIntTime = 0

        self.stInterval = stInterval
        self.stArg = stArg
        self.maxIntTime = maxIntTime

    def incStatic(self, incArg=None):
        if self.argMatchHandle == None or self.argMatchHandle(self.stArg, incArg):
            self.static[self.curIntTime] += 1

    def getStaticInfo(self):
        return [self.curIntTime, self.stInterval, self.maxIntTime, "" if self.stArg == None else self.stArg]

    def getStatic(self, startIntTime=None, endIntTime=None):
        if startIntTime == None:
            return self.static[self.curIntTime]
        else:
            return self.static[startIntTime:self.curIntTime if endIntTime == None else endIntTime]
    def _clearStatic_(self):
        if self.saveTo != None:
            self.saveTo.writelines("%s,%s,%s: %s\n" % (self.startTime, self.curIntTime, self.stInterval, self.static))
        self.startTime = time.time()
        for intTime in range(0, self.maxIntTime):
            self.static[intTime] = 0
        self.curIntTime = 0

    def stopStatic(self):
        self.isRunning = False
        if self.stInterval > 0:
            time.sleep(self.stInterval)

    def run(self):
        while self.isRunning:
            time.sleep(self.stInterval)
            self.curIntTime = self.curIntTime + 1
            if self.curIntTime >= self.maxIntTime:
                self._clearStatic_()
