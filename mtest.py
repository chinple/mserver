# -*- coding: utf8 -*-
'''
Created on 2010-9-28

@author: chinple
'''

from tmodel.runner.driver import TestDriver
from libs.tvg import TValueGroup

driver = TestDriver()
tlog = driver.tc.tlog
tassert = driver.tc.tassert
tprop = driver.tc.tprop

# Test case example, see @SampleTestCase, 
# @model()
# class SampleTestCase(TestCaseBase):
#     @scenario(param={'letter':['a', 'b', 'c'],
#             'number':['1', '2', '3'], 'other':['x', 'y']},
#         where={'combine':"letter,number,other".split(",")})
#     def sampleTest(self, letter, number, other):
#         pass
# run in command:
#    python2.7 run.py test


def scenario(param={}, where={}, group=None, status=None, despFormat="", **searchKey):

    # mark method as test case, such as @scenario()
    def __ScenarioMiddleFun(testCaseFun):      

        def ScenarioDecorator(tcObj=None):
            return driver.runScenario(tcObj, testCaseFun, testCaseFun.__name__,
                param, where, group, status, despFormat, searchKey)

        return ScenarioDecorator

    return __ScenarioMiddleFun


def model(testModule="", testName=None, imports='', testOrder=None, **searchKey):

    # mark method as test class, such as @model()
    def __ModelMiddleFun(modelClass):

        def ModelDecorator():
            driver.addModelCls(modelClass, testModule, testName, imports, testOrder, searchKey)
            return modelClass()

        return ModelDecorator

    return __ModelMiddleFun


def adapter(adapterHandler=None, adapterReg='[A-z].*', enableadapter=True, **adapterInfo):

    def __adapterMiddleFun(adpCls):

        def adapterDecorator(*tupleArg, **jsonArg):
            obj = adpCls(*tupleArg, **jsonArg)
            if enableadapter:
                from tmodel.model.vadapter import AdapterFunDecorator
                AdapterFunDecorator.setAttrHandler(obj, adpCls, adapterHandler, adapterReg, adapterInfo) 
            return obj

        return adapterDecorator

    return __adapterMiddleFun


def testing(*args):
    import sys
    if sys.getdefaultencoding() != "utf-8":
        reload(sys)
        eval('sys.setdefaultencoding("utf-8")')

    from tmodel.runner.launcher import TestLoader
    if len(args) == 0:
        args = ("-f", sys.argv[0])
    elif len(args) == 1:
        from libs.objop import StrOperation
        args = list(StrOperation.splitStr(args[0], " ", '"')) + ["-f", sys.argv[0]]
    tcode = TestLoader(driver, list(args)).launch()
    sys.exit(0 if tcode is None else tcode)


class TestCaseBase(object):

    # test case base class, test executing order:
    # @setUp -> (generate test parameter and set self.param
    #           -> @beginTestCase
    #           -> call a test method with parameter in self.param
    #           -> @errorHandle if case failed
    #           -> @endTestCase )+ (repeat)
    # -> @tearDown
    def __init__(self):
        self.property = tprop
        self.tassert = tassert
        self.tlog = tlog
        self.param = TValueGroup({})

    def __repr__(self):
        return "self"

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def beginTestCase(self):
        pass

    def endTestCase(self):
        pass

    def errorHandle(self, errorException, caseInfo):
        pass

    def __deepcopy__(self, memo=None):
        return self


def step(sfrom, sto, repeat=0):

    # status modeling, see @StatusModelingSample
    def __stepMiddleFun(testCaseFun):      

        def stepDecorator(*args):
            if driver.tc.isModeling:
                return (sfrom, sto, repeat)
            else:
                from inspect import getargspec
                argLen = len(getargspec(testCaseFun)[0])
                if argLen == 1:
                    testCaseFun(args[0])
                else:
                    testCaseFun(*args)

        return stepDecorator

    return __stepMiddleFun


class TestModelBase(TestCaseBase):

    # status model base class
    def __isAccept__(self, sFrom, sTo, stepArg):
        pass

    def __isContinue__(self, sFrom, sTo, stepArg):
        pass

    def __getArgList__(self, sFrom, sTo):
        pass

    def __isDebug__(self):
        return False
