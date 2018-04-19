# -*- coding: utf8 -*-
'''
Created on 2010-9-28

@author: chinple
'''
from libs.tvg import TValueGroup
from libs.objop import ObjOperation
from libs.syslog import slog
from tmodel.model.paramgen import CombineSingleParam

class TestModeling:
    # edge,condition,condEdge,path,condPath,all
    def __init__(self, tcObj, startStatus, strategy):
        self.startStatus = startStatus
        self.tlog = tcObj.tlog
        self.strategy = "product" if strategy == "all" else strategy 
        self.isAcceptHandler = tcObj.__isAccept__
        self.isContinueHandler = tcObj.__isContinue__
        self.getStepArgHandler = tcObj.__getArgList__
        self.isDebug = tcObj.__isDebug__()

        testSteps = TValueGroup({})
        for sFunName in [funName for funName in dir(tcObj) if not funName.startswith("__")]:
            sFun = eval("tcObj.%s" % sFunName)

            if(hasattr(sFun, '__name__') and sFun.__name__ == 'stepDecorator'):
                sFunStatus = sFun()
                testSteps[sFunName] = {'or':sFunStatus[0].split(','), 'to':sFunStatus[1],
                    'repeat':sFunStatus[2], 'cover':{}}

        self.testSteps = testSteps

    def getNextSteps(self, stepNames, currentStatus):
        steps = []
        for stepName in stepNames:
            if self.testSteps[stepName]['or'].__contains__(currentStatus):
                steps.append(stepName)
        return steps

    def getNextPath(self, refStep, testPath):

        currentStep = refStep
        while True:
            lastStep = self.testSteps[currentStep]
            nextIndex = lastStep['nextIndex'][lastStep['repeatCount']]
            if nextIndex < 0:
                break
            currentStep = lastStep['next'][nextIndex]

            if testPath.__contains__(currentStep):
                curStepInfo = self.testSteps[currentStep]
                repeatCount = curStepInfo['repeatCount']
                repeatCount += 1
                if curStepInfo['repeat'] > repeatCount:
                    curStepInfo['repeatCount'] = repeatCount
                    try:
                        curStepInfo['nextIndex'][repeatCount] = len(curStepInfo['next']) - 1
                    except:
                        curStepInfo['nextIndex'].append(len(curStepInfo['next']) - 1)
                    testPath.append(currentStep)
                else:  # repeat exceeds
                    repeatCount -= 1
                    curNextIndex = curStepInfo['nextIndex'][repeatCount]
                    if curNextIndex > 0:  # To find the long path
                        curStepInfo['nextIndex'][repeatCount] = curNextIndex - 1
                        currentStep = testPath[len(testPath) - 1]
                    else:
                        return curStepInfo['repeat']
            else:
                testPath.append(currentStep)
        return -1

    def generatePaths(self):
        argPathContainer = []
        stepNames = list(self.testSteps.keys())
        for stepName in stepNames:
            step = self.testSteps[stepName]
            step['next'] = self.getNextSteps(stepNames, step['to'])
            step['repeatCount'] = 0
            step['nextIndex'] = [len(step['next']) - 1]

        startStepNames = self.getNextSteps(stepNames, self.startStatus)
        startStepIndex = len(startStepNames) - 1

        startStepName = startStepNames[startStepIndex]
        testPath = [startStepNames[startStepIndex]]

        while True:
            repeatTimes = self.getNextPath(startStepName, testPath)
            if self.isDebug:
                slog.info("Repeat: %s\t%s", repeatTimes, testPath)
            self.__addPathToArgPathContainer(argPathContainer, testPath, repeatTimes)

            startStepName = None
            cpTestPath = []
            backIndex = len(testPath) - 1
            while backIndex >= 0:
                backStepName = testPath[backIndex]
                nextStep = self.testSteps[backStepName]
                nextIndexes = nextStep['nextIndex']
                repeatCount = nextStep['repeatCount']
                nextIndex = nextIndexes[repeatCount]

                if nextIndex > 0:
                    startStepName = backStepName
                    nextIndexes[repeatCount] = nextIndex - 1
                    stepNameIndex = 0
                    while stepNameIndex <= backIndex:  # Copy testPath
                        cpTestPath.append(testPath[stepNameIndex])
                        stepNameIndex += 1
                    break
                elif repeatCount > 0:
                    nextStep['repeatCount'] = repeatCount - 1
                backIndex -= 1
            if startStepName == None:
                startStepIndex -= 1
                if startStepIndex < 0:
                    break
                else:
                    startStepName = startStepNames[startStepIndex]
                    testPath = [startStepNames[startStepIndex]]
            else:
                testPath = cpTestPath
        return argPathContainer

    def __coverTestPath(self, testPath):
        sTo = None
        stepIndex = -1
        for testStepName in testPath:
            stepIndex += 1
            stepInfo = self.testSteps[testStepName]
            sFrom = stepInfo['or'][0] if sTo == None else sTo
            sTo = stepInfo['to']
            stepInfo['cover'][sFrom] = True

    def __prepareTestPath(self, testPath, pathParam, stepIndexList, stepIndexToCombIndex, isEdgeCover, isCondCover):
        sTo = None
        combIndex = -1
        stepIndex = -1
        noNewEdge = True
        for testStepName in testPath:
            stepIndex += 1
            stepInfo = self.testSteps[testStepName]
            sFrom = stepInfo['or'][0] if sTo == None else sTo
            sTo = stepInfo['to']
            stepArg = self.getStepArgHandler(sFrom, sTo)
            pathParam[stepIndex] = stepArg

            isArgList = type(stepArg) == list
            if isEdgeCover:
                cover = stepInfo['cover']
                if not ObjOperation.tryGetVal(cover, sFrom, False):
                    cover[sFrom] = False
                    noNewEdge = False
                elif isCondCover and isArgList:
                    pathParam[stepIndex] = ObjOperation.tryGetVal(stepArg, 0, stepArg)
                    continue
            if isArgList:
                combIndex += 1
                stepIndexToCombIndex[stepIndex] = combIndex
                stepIndexList.append(stepIndex)

        return noNewEdge, stepIndex, combIndex

    def __addPathToArgPathContainer(self, argPathContainer, testPath, repeatCount):
        pathParam = TValueGroup({})
        stepIndexList = []        
        stepIndexToCombIndex = {}
        isCondCover = self.strategy == "condition"
        isEdgeCover = self.strategy == "edge" or self.strategy == "condEdge" or isCondCover
        notCondCover = self.strategy == "path" or self.strategy == "edge" or self.strategy == 'available'

        noNewEdge, stepIndex, combIndex = self.__prepareTestPath(testPath, pathParam, stepIndexList, stepIndexToCombIndex, isEdgeCover, isCondCover)
        if isEdgeCover and noNewEdge:
            return

        pathCovered = False
        stepArg = CombineSingleParam(pathParam, {'combine':stepIndexList, 'strategy':self.strategy}, None)
        while True:
            pathArg = stepArg.nextParam()
            if pathArg == None:
                break
            acceptRes, acceptStepIndex = self.__isTestPathAccept(testPath, pathArg)
            if acceptRes <= 9:
                addTestPath = testPath
                if stepIndex > acceptStepIndex:
                    addTestPath = list(testPath)
                    delStepIndex = stepIndex
                    while delStepIndex > acceptStepIndex:
                        addTestPath.__delitem__(delStepIndex)
                        pathArg.__delitem__(delStepIndex)
                        delStepIndex -= 1
                pathCovered = True
                argPathContainer.append({'path':addTestPath, 'accept':acceptRes, 'arg':pathArg})
                if notCondCover:
                    break

            addCombIndex = ObjOperation.tryGetVal(stepIndexToCombIndex, acceptStepIndex, combIndex)
            if addCombIndex < combIndex:
                stepArg.toNextParamArg(addCombIndex)

        if isEdgeCover and pathCovered:
            self.__coverTestPath(testPath)

    def __isTestPathAccept(self, path, arg):
        acRes = 0
        sTo = None
        stepIndex = -1
        for testStepName in path:
            stepIndex += 1
            stepInfo = self.testSteps[testStepName]
            sFrom = stepInfo['or'][0] if sTo == None else sTo
            sTo = stepInfo['to']
            stepArg = arg[stepIndex]

            if self.isContinueHandler(sFrom, sTo, stepArg) == False:
                acRes = 10 
                break
            isAccept = self.isAcceptHandler(sFrom, sTo, stepArg)
            if isAccept:
                acRes = 1
                break
            elif isAccept == False:
                acRes = 11
        return (acRes, stepIndex)

    def launchTestPath(self, tcObj, sPath):
        sTo = None
        stepIndex = -1
        pathArg = sPath['arg']
        for testStepName in sPath['path']:
            stepIndex += 1
            stepInfo = self.testSteps[testStepName]
            sFrom = stepInfo['or'][0] if sTo == None else sTo
            sTo = stepInfo['to']
            stepArg = pathArg[stepIndex]
            self.tlog.step("[%s] %s to %s: %s" % (stepIndex, sFrom, sTo, stepArg))
            eval('tcObj.' + testStepName)(sFrom, sTo, stepArg)
