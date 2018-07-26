'''
Created on 2011-2-21

@author: chinple
'''
from tmodel.model.vcode import CodeFactory
from tmodel.model.vaction import DynamicAction
from tmodel.runner.driver import BaseDriver
from tmodel.model.vadapter import AdapterFunDecorator

class TestViewDriver(BaseDriver):   

    def initDriver(self, **kwargs):
        BaseDriver.initDriver(self, **kwargs)
        self.tdriver.setDriver(self.endTest, self.endScenario, self.endModel)

        self.coder = CodeFactory(kwargs['runMode'])
        DynamicAction.actionFactory = self.coder

        AdapterFunDecorator.isFakeFun = True
        AdapterFunDecorator.setAttrHandler(self.tdriver.tassert, self.tdriver.tassert.__class__,
            adapterHandler=None, adapterReg='[A-z].*', adapterInfo={"calledName":"self.tassert"})
        AdapterFunDecorator.setAttrHandler(self.tdriver.tlog, self.tdriver.tlog.__class__,
            adapterHandler=None, adapterReg='[s|i|w].*', adapterInfo={"calledName":"self.tlog"})

    def endDriver(self):
        self.coder.endFactory()

    def endTest(self, caseName, sparam, pindex, searchKey, tcInfo, caseInfo):
        self.coder.endFun(caseName, sparam, pindex, searchKey, tcInfo, caseInfo)
    def endScenario(self, tcObj, caseName):
        pass
    def endModel(self, tcInfo):
        self.coder.endClass(tcInfo)
