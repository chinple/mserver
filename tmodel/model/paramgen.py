# -*- coding: utf8 -*-
'''
Created on 2010-9-28

@author: chinple
'''
from libs.tvg import TValueGroup
from libs.objop import ObjOperation

class CombSpace:
    def __init__(self, *spaceDegree):
        self.__spaceDegree__ = spaceDegree
        spaceSize = 1
        for itemLen in spaceDegree:
            spaceSize *= itemLen
        self.__spaceSize__ = spaceSize
        self.__spaceDimension__ = len(self.__spaceDegree__)

        orderNumCombBase = [int(self.__spaceSize__ / self.__spaceDegree__[0]) if self.__spaceDimension__ > 0 and self.__spaceDegree__[0] > 0 else 1]
        for lenIndex in range(self.__spaceDimension__ - 1):
            orderNumCombBase.append(int(orderNumCombBase[lenIndex] / self.__spaceDegree__[lenIndex + 1]))
        self.__orderNumCombBase__ = orderNumCombBase

    def getOrderNum(self, combNum):
        orderNum = 0
        for spaceIndex in range(self.__spaceDimension__):
            orderNum += combNum[spaceIndex] * self.__orderNumCombBase__[spaceIndex]
        return orderNum

    def getCombNum(self, orderNum):
        combNum = [0] * self.__spaceDimension__
        for spaceIndex in range(self.__spaceDimension__):
            numBase = self.__orderNumCombBase__[spaceIndex]
            combItem = int(orderNum / numBase)
            orderNum -= combItem * numBase
            combNum[spaceIndex] = combItem
        return combNum

    def getAllNum(self, isOrderNum=True, isPureNum=False):
        if isOrderNum:
            return [orderNum for orderNum in range(self.__spaceSize__) if self.isPureOrderNum(orderNum)]\
                if isPureNum else range(self.__spaceSize__)
        else:
            return [self.getCombNum(orderNum) for orderNum in self.getAllNum(True, isPureNum)]

    def getTotalNum(self):
        return self.__spaceSize__

    def addOrderNum(self, orderNum, spaceIndex):
        orderNum += self.__orderNumCombBase__[spaceIndex]
        if orderNum < self.__spaceSize__:
            return orderNum

    def addCombNum(self, combNum, spaceIndex):
        while spaceIndex >= 0 and combNum[spaceIndex] + 1 >= self.__spaceDegree__[spaceIndex]:
            spaceIndex -= 1
        if spaceIndex >= 0:
            combNum[spaceIndex] += 1
            return combNum
    def sameDegree(self, combNum, spaceIndex):
        combNum = list(combNum)
        spaceIndex += 1
        while spaceIndex < self.__spaceDimension__:
            combNum[spaceIndex] = 0
            spaceIndex += 1
        return combNum
    def isPureOrderNum(self, orderNum):
        if orderNum <= 0:
            return True
        spaceIndex = 0
        while spaceIndex < self.__spaceDimension__:
            itemBaseNum = self.__orderNumCombBase__[spaceIndex]
            if orderNum >= itemBaseNum:
                return orderNum % itemBaseNum == 0
            spaceIndex += 1

    def getNextPureOrderNum(self, orderNum):
        baseNum = 1
        if orderNum > self.__orderNumCombBase__[0]:
            baseNum = self.__orderNumCombBase__[0]
        else:
            for cpIndex in range(self.__spaceDimension__ - 1):
                maxOrder = self.__orderNumCombBase__[cpIndex]
                minOrder = self.__orderNumCombBase__[cpIndex + 1]
                if orderNum == maxOrder:
                    baseNum = maxOrder
                    break
                elif orderNum >= minOrder and orderNum < maxOrder:
                    baseNum = minOrder
                    break
        return baseNum * (int(orderNum / baseNum) + 1)

    def isMatchOrderNum(self, orderNum, refComb):
        for spaceIndex in range(self.__spaceDimension__):
            numBase = self.__orderNumCombBase__[spaceIndex]
            combItem = int(orderNum / numBase)
            orderNum -= combItem * numBase
            if refComb[spaceIndex] > 0 and combItem == 0:
                return False
        return True

    def isSameOrderNum(self, orderNum, refComb, isPure=True):
        isMatch = True
        spaceIndex = 0
        while (isPure or isMatch) and spaceIndex < self.__spaceDimension__:
            baseNum = self.__orderNumCombBase__[spaceIndex]
            if isPure and orderNum >= baseNum:
                if orderNum % baseNum == 0:
                    isPure = True
                    break
                else:
                    isPure = False
            combItem = int(orderNum / baseNum)
            orderNum -= combItem * baseNum
            if isMatch and (combItem == 0) != (refComb[spaceIndex] == 0):
                isMatch = False
            spaceIndex += 1
        return isPure or isMatch

    def isSameCombNum(self, combNum, refComb):
        for spaceIndex in range(self.__spaceDimension__):
            if (combNum[spaceIndex] == 0) != (refComb[spaceIndex] == 0):
                return False
        return True

class GroupCombSpace:
    def __init__(self, *groupDegrees):
        self.combSps = []
        self.combSpIndex = []
        spDegree = []
        for group in groupDegrees:
            combSp = CombSpace(*group['degree'])
            self.combSps.append(combSp)
            spIndex = combSp.getAllNum(True, group['order'])
            self.combSpIndex.append(spIndex)
            spDegree.append(len(spIndex))
        self.spCombSp = CombSpace(*spDegree)
    def getTotalNum(self):
        return self.spCombSp.__spaceSize__
    def getNextPureOrderNum(self, orderNum):
        return self.spCombSp.getNextPureOrderNum(orderNum)

    def getCombNum(self, orderNum):
        return self.spCombSp.getCombNum(orderNum)
    def getGroupCombNum(self, groupIndex, orderNum):
        groupOrderNum = self.combSpIndex[groupIndex][orderNum]
        return self.combSps[groupIndex].getCombNum(groupOrderNum)

class ParamRender:
    def __init__(self, originParam, names, isList, isOrder, isRenderAll=False):
        self.originParam = originParam
        self.names = names
        self.isList = isList
        self.isOrder = isOrder
        self._initLeftNames(isRenderAll)

    def _initLeftNames(self, isRenderAll):
        self.leftNames = []
        if isRenderAll and not self.isList:
            for p in self.originParam.keys():
                if not self.names.__contains__(p):
                    self.leftNames.append(p)

    def getDegree(self):
        if self.isList:
            spDegree = [len(self.originParam)]
        else:
            spDegree = []
            for pKey in self.names:
                sparam = self.originParam[pKey]
                if hasattr(sparam, '__name__') and sparam.__name__ == '<lambda>':
                    self.tParam[pKey] = sparam()
                spDegree.append(len(self.originParam[pKey]))
        return {"degree":spDegree, "order":self.isOrder}

    def renderParam(self, indexes, param):
        if self.isList:
            rparam = self.originParam[indexes[0]]
            if param is None:
                param = rparam
            else:
                for p in rparam:
                    param[p] = rparam[p]
        else:
            for p in self.leftNames:
                param[p] = self.originParam[p]

            spIndex = 0
            for pName in self.names:
                param[pName] = self.originParam[pName][indexes[spIndex]]
                if indexes[spIndex] > 0 or spIndex == 0:
                    param.paramName = pName
                spIndex += 1

        return param

class CombineSingleParam:
    def __init__(self, tParam, whereCondition, group):

        self.tParam = TValueGroup(tParam)
        self.condition = ObjOperation.tryGetVal(whereCondition, "condition", None)
        self.combSp = self.__combParam__(tParam, whereCondition, group)

        self.totalParams = self.combSp.getTotalNum()
        self.curOrderNum = 0
        self.curParamIndex = 0

    def __combParam__(self, tParam, whereCondition, group):
        strategy = ObjOperation.tryGetVal(whereCondition, "strategy", 'add').strip().lower()
        self.isPureNum = strategy != 'product' and strategy != 'available'
        self.isList = strategy == 'datalist'

        self.paramRender = ParamRender(tParam, ObjOperation.tryGetVal(whereCondition, "combine", []), strategy == "datalist", strategy != "product")
        degree = self.paramRender.getDegree()
        return CombSpace(*degree['degree'])

    def nextParam(self):
        while self.curOrderNum < self.totalParams:
            nextParam = self._getNextParam()
            if self.condition is None or self.condition(nextParam) is not False:
                self.curParamIndex += 1
                return nextParam

    def toNextParamArg(self, paramIndex, switchCount=1):
        o = self.combSp.addOrderNum(self.curOrderNum - switchCount, paramIndex)
        self.curOrderNum = (self.totalParams + 1) if o is None else o 

    def _getNextParam(self):
        if self.isList:
            strategyParam = TValueGroup({})
        else:
            strategyParam = TValueGroup(self.tParam, True, isDeepClone=True)
        strategyParam.pIndex = self.curParamIndex
        strategyParam.paramName = None
        strategyParam.orderNum = self.curOrderNum

        self.__renderParam__(strategyParam)

        if self.isPureNum:
            self.curOrderNum = self.combSp.getNextPureOrderNum(self.curOrderNum)
        else:
            self.curOrderNum += 1

        return strategyParam

    def __renderParam__(self, strategyParam, isCombineGroup=True):
        combNum = self.combSp.getCombNum(self.curOrderNum)
        self.paramRender.renderParam(combNum, strategyParam)

class CombineWhereParam:
    def __init__(self, tParam, whereCondition, group):

        self.tParam = TValueGroup(tParam)
        self.condition = ObjOperation.tryGetVal(whereCondition, "condition", None)
        self.paramRender = []
        self.gcombSp = self.__groupParam__(tParam, whereCondition, group)

        self.totalParams = self.gcombSp.getTotalNum()
        self.curOrderNum = 0
        self.curParamIndex = 0

    def __groupParam__(self, tParam, whereCondition, group):
        strategy = ObjOperation.tryGetVal(whereCondition, "strategy", 'add').strip().lower()
        self.isPureNum = strategy != 'product'
        self.isList = strategy == 'datalist'

        group = ObjOperation.tryGetVal(whereCondition, "group", None)
        if group is None:
            groups = [{'combine':ObjOperation.tryGetVal(whereCondition, "combine", []),
                'strategy':strategy}]
        else:
            groups = []
            for g in group:
                if g.__contains__('combine'):
                    g['strategy'] = ObjOperation.tryGetVal(g, "strategy", strategy)
                    groups.append(g)

        gdegress = []   
        for g in groups:
            r = ParamRender(tParam, g['combine'], g['strategy'] == "datalist", g['strategy'] != "product")
            self.paramRender.append(r)
            gdegress.append(r.getDegree())
        return GroupCombSpace(*gdegress)

    def nextParam(self):
        while self.curOrderNum < self.totalParams:
            nextParam = self._getNextParam()
            if self.condition is None or self.condition(nextParam) is not False:
                self.curParamIndex += 1
                return nextParam

    def _getNextParam(self):
        if self.isList:
            strategyParam = TValueGroup({})
        else:
            strategyParam = TValueGroup(self.tParam, True, isDeepClone=True)
        strategyParam.pIndex = self.curParamIndex
        strategyParam.paramName = None
        strategyParam.orderNum = self.curOrderNum

        self.__renderParam__(strategyParam)

        if self.isPureNum:
            self.curOrderNum = self.gcombSp.getNextPureOrderNum(self.curOrderNum)
        else:
            self.curOrderNum += 1

        return strategyParam

    def __renderParam__(self, strategyParam, isCombineGroup=True):
        combNum = self.gcombSp.getCombNum(self.curOrderNum)
        isNeedRender = True
        for groupIndex in range(len(combNum)):
            groupCombNum = self.gcombSp.getGroupCombNum(groupIndex, combNum[groupIndex])
            if isCombineGroup or  combNum[groupIndex] > 0:
                self.paramRender[groupIndex].renderParam(groupCombNum, strategyParam)
                isNeedRender = False
        if isNeedRender:
            groupCombNum = self.gcombSp.getGroupCombNum(0, combNum[0])
            self.paramRender[0].renderParam(groupCombNum, strategyParam)

class CombineGroupParam(CombineWhereParam):
    def __init__(self, tParam, whereCondition, group):
        self.isNotGroup = group is None
        CombineWhereParam.__init__(self, tParam, whereCondition, group)

    def __groupParam__(self, tParam, whereCondition, group):
        if self.isNotGroup:
            return CombineWhereParam.__groupParam__(self, tParam, whereCondition, group)
        defCombine = ObjOperation.tryGetVal(whereCondition, "combine", [])
        defStrategy = ObjOperation.tryGetVal(whereCondition, "strategy", [])
        self.isPureNum = True
        self.isList = False

        gdegress = []
        for gp in group:
            if not ObjOperation.tryGetVal(gp, "active", True):
                continue
            combine = ObjOperation.tryGetVal(gp, "combine", defCombine)
            strategy = ObjOperation.tryGetVal(gp, "strategy", defStrategy)
            r = ParamRender(gp['param'], combine, strategy == "datalist", strategy != "product", True)
            self.paramRender.append(r)
            gdegress.append(r.getDegree())
        return GroupCombSpace(*gdegress)

    def __renderParam__(self, strategyParam):
        return CombineWhereParam.__renderParam__(self, strategyParam, self.isNotGroup)
