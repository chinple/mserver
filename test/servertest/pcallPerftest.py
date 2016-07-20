'''

@author: chinple
'''
from cperf import stressScenario, running
from test.servertest.pserverTest import SampleServerApi
from server.chandle import ObjHandler

workerSize = 0
sleepTime = 0
lockSize = 1024
cservice = None
def initCservice():
    global cservice
    objClasses = [(SampleServerApi, None, {})]
    
    if workerSize <= 0:
        cservice = ObjHandler()
        cservice.loadClasses(objClasses, None)
    else:
        from server.objhandle import ProcessObjHandler, WorkerScheduler
        ws = WorkerScheduler(objClasses, workerSize, lockSize)
        cservice = ProcessObjHandler(ws)
        cservice.loadClasses(objClasses, None)

@stressScenario(startThreads=100, maxThreads=100, expTps=10000)
def SampleTest(thid, degree):
    cservice.__callObjFun__("/SampleServerApi/sleepSeconds", {"t":sleepTime})

if __name__ == '__main__':
    initCservice()
    running("-r run --isKeepRunning")
