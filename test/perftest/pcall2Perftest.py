# '''
# 
# @author: chinple
# '''
# from cperf import stressScenario, running
# from test.servertest.pserverTest import SampleServerApi
# # from server.objhandle2 import ConnWorkerManager, ConnWorkerScheduler
# 
# workerSize = 5
# sleepTime = 0
# lockSize = 1024
# cservice = None
# address = ('127.0.0.1', 9494)
# def initCservice():
#     global cservice
#     objClasses = [(SampleServerApi, None, {})]
#     
#     cservice = ConnWorkerScheduler(objClasses, workerSize, lockSize)
# 
# @stressScenario(startThreads=100, maxThreads=100, expTps=10000)
# def SampleTest(thid, degree):
#     cservice.callObjFunInworker("/SampleServerApi/sleepSeconds", {"t":sleepTime})
# 
# if __name__ == '__main__':
#     initCservice()
#     running("-r run --isKeepRunning")
