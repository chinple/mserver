'''
Created on 2015-7-10

@author: chinple
'''

from mtest import model, TestCaseBase, scenario
import time
from server.objhandle import WorkerScheduler, WorkerManager
from threading import Thread
from libs.syslog import slog

class SampleServerApi:
    def emptyCall(self):
        return "emptyCall"
    def callWithArgs(self, callId, method="post"):
        return "callId: %s" % callId
    def sleepSeconds(self, t):
        if t > 0:
            slog.info("Sleep: %s" % t)
        time.sleep(t)
        return "Sleep: %s" % t

@model()
class ObjHandler(TestCaseBase):

    def setUp(self):
        objClasses, workerSize, = [(SampleServerApi, None, {})], 1
        self.lockSize = 3
        self.ws = WorkerScheduler(objClasses, workerSize, self.lockSize)
    def tearDown(self):
        self.ws.shutdownWorkers()
    
    @scenario()
    def callAlways(self):
        for i in range(5):
            self.tlog.info(self.ws.callObjFunInworker("/SampleServerApi/emptyCall", {}))
            self.tlog.info(self.ws.callObjFunInworker("/SampleServerApi/callWithArgs", {"callId":i}))
        time.sleep(1)

    @scenario()
    def fullCallTest(self):
        self.tlog.step("Busy lock")
        for i in range(self.lockSize):
            Thread(target=lambda:self.ws.callObjFunInworker("/SampleServerApi/sleepSeconds", {"t":2})).start()

        try:
            self.tlog.info(self.ws.callObjFunInworker("/SampleServerApi/callWithArgs", {"callId":1}))
            isSuccess = False
        except WorkerManager.WorkerFullException as ex:
            self.tlog.info(str(ex))
            isSuccess = True
        self.tassert.isTrue(isSuccess, "Check success")

        self.tlog.step("Lock released")
        time.sleep(3)
        self.tlog.info(self.ws.callObjFunInworker("/SampleServerApi/callWithArgs", {"callId":1}))

if __name__ == "__main__":
    from mtest import testing
    testing("-r run ")
