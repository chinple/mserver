from server.chandle import ObjHandler
import multiprocessing
from multiprocessing import Manager
from libs.syslog import slog
import traceback
import thread

class ProcessObjHandler(ObjHandler):
    def __init__(self, ws):
        ObjHandler.__init__(self)
        assert ws is not None
        self.ws = ws

    def __callObjFun__(self, reqPath, reqParam):
        try:
            return self.ws.callObjFunInworker(reqPath, reqParam)
        except WorkerManager.WorkerFullException as ex:
            slog.warn(str(ex))
        except:
            slog.error(str(traceback.format_exc()))
        # If worker is full or exception, deal request in main process
        return ObjHandler.__callObjFun__(self, reqPath, reqParam)

class WorkerScheduler:
    def __init__(self, objClasses, workerSize, lockSize):
        self.workers = []
        self.objClasses, self.workerSize, self.lockSize , self.manager = objClasses, workerSize, lockSize, Manager()
        self._curWorkerId = 0
        while workerSize > 0:
            workerSize -= 1
            self.addWorker()

    def addWorker(self):
        wm = WorkerManager("wm-%s" % len(self.workers), self.objClasses, self.manager, self.lockSize)
        self.workers.append(wm)

    def callObjFunInworker(self, reqPath, reqParam):
        wid = self._curWorkerId % self.workerSize
        self._curWorkerId += 1
        return self.workers[wid].callObjFun(reqPath, reqParam)

    def shutdownWorkers(self):
        for wm in self.workers:
            wm.worker.terminate()

class WorkerManager:
    class WorkerFullException(Exception):
        pass
    def __init__(self, workerName, objClasses, manager, lockSize):
        # lock size determine the TPS of a process
        # lock mode means if sub process down then no response returned until all lock used, see @callObjFun
        self.workerName = workerName
        self.resultContainer = manager.dict()

        self.lockSize = lockSize
        self._locker = thread.allocate_lock()
        self._lockList = []
        self._lockIds = set()
        self._addCallLock()

        pparam, self.pcall = multiprocessing.Pipe(duplex=True)

        self.worker = multiprocessing.Process(target=workerRun, name=workerName,
            args=(objClasses, self.resultContainer, pparam, self._lockList))
        self.worker.daemon = True
        self.worker.start()

    def _listenPreturn(self):
        while 1:
            callId = self.presult.recv()
            self._lockList[callId].release()

    def _addCallLock(self):
        slog.info("Add lock: %s %s" % (self.workerName, len(self._lockList)))
        self._locker.acquire()
        callId = len(self._lockList)
        try:
            for lockId in range(callId, min(self.lockSize, callId + self.lockSize)):
#                 self._lockList.append(thread.allocate_lock())
                self._lockList.append(multiprocessing.Lock())
                self._lockIds.add(lockId)
        finally:
            self._locker.release()

    def _getCallLock(self):
        try:
            callId = self._lockIds.pop()
#             slog.info("Lock: %s %s" % (self.workerName, self._lockIds))
            return callId, self._lockList[callId]
        except:
            if len(self._lockList) < self.lockSize:
                self._addCallLock()
                return self._getCallLock()
            raise WorkerManager.WorkerFullException("Worker full %s for all lock %s busy" \
                % (self.workerName, len(self._lockList)))

    def callObjFun(self, reqPath, reqParam):
        callId, lock = self._getCallLock()

        lock.acquire()
        try:
            self.resultContainer[callId] = reqPath, reqParam
            self.pcall.send(callId)
            lock.acquire()  # this lock released in another process means the call returned. See @workerRun
            return self.resultContainer[callId]
        finally:
            self.resultContainer.__delitem__(callId)
            lock.release()
            self._lockIds.add(callId)

def wokerCall(callId, resultContainer, pparam, lockList, objHandler):
    reqPath, reqParam = resultContainer[callId]
    resultContainer.__delitem__(callId)
    try:
        resultContainer[callId] = objHandler.__callObjFun__(reqPath, reqParam)
    except Exception as ex:
        resultContainer[callId] = "Fail to call in process: %s" % ex
        slog.error(traceback.format_exc())
    finally:
        lockList[callId].release()

def workerRun(objClasses, resultContainer, pparam, lockList):
    objHandler = ObjHandler()
    objHandler.loadClasses(objClasses, None)
    from multiprocessing.pool import ThreadPool
    thpool = ThreadPool(len(lockList))
    while 1:
        callId = pparam.recv()
        thpool.apply_async(func=wokerCall, args=(callId, resultContainer, pparam, lockList, objHandler))
