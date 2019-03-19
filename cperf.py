'''
Created on 2015-11-25

@author: chinple
'''
from tmodel.runner.perfdriver import StressScheduler

_sc = StressScheduler()

pprop = _sc.pprop
pstat = _sc.pstat


def stressScenario(startThreads=3, maxThreads=10, step=1, expTps=50, interval=0):

    def __stressMiddleFun(stsHandler):      
        _sc.addScenario(stsHandler, startThreads, maxThreads, step, expTps, interval)

    return __stressMiddleFun


def apiStatisticHandler(obj, objFun, tupleArg, jsonArg, adpInfo):
    rh = _sc.getApiRunner(objFun)
    return rh.runHandler(*tupleArg, **jsonArg)[1]


def running(*args):
    import sys
    
    if len(args) == 0:
        args = ("-t", sys.argv[0])
    elif len(args) == 1:
        from libs.objop import StrOperation
        args = list(StrOperation.splitStr(args[0], " ", '"')) + ["-t", sys.argv[0]]
    _sc.setRunnerByArgs(True, args)
    _sc.launch()
