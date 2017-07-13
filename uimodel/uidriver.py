'''
Created on 2017-7-11

@author: xinxiu
'''
from uimodel import UIContainer, UICaseModel, UIToolBase
from libs.objop import ArgsOperation
from libs.refrect import DynamicLoader

class UIDriver:
    def __init__(self):
        self.ui = UIContainer()
        self.uicase = UICaseModel()

    def __getDefine(self):
        return (("r", "runMode", "run|show|debug", 'run'),
            ('f', "uisourcefile", "resource locator csv files", [], 'list'),
            ('c', "uitoolClass", "class extends UIToolBase", 'UIToolBase'),
            ("strategy", "strategy of choose ui ele", "random"),
            
            ("maxCases", "strategy of choose ui ele", 10, 'int'),
            ("maxStep", "strategy of choose ui ele", 200, 'int')
        )
    def setRunnerByArgs(self, isShowMsg, args):
        cArgs, parseMsg, isSuccess = ArgsOperation.parseArgs(list(args), [], None, *self.__getDefine())
        if isShowMsg:
            print(parseMsg)
        if not isSuccess:
            import sys
            sys.exit(-1)

        for f in cArgs.uisourcefile:
            self.ui.loadUI(f)

        for cls in DynamicLoader.getClassFromFile(None, True, cArgs.uitoolClass):
            try:
                isSubcls = issubclass(cls, UIToolBase)
            except:
                isSubcls = False
            if isSubcls and not cls == UIToolBase:
                uitool = cls()
                self.ui.setUI(uitool, cArgs.strategy)
                break

        self.maxCases = cArgs.maxCases
        self.maxStep = cArgs.maxStep
        self.isdebug = cArgs.runMode == "debug"

    def launch(self):
        self.uicase.study(self.ui, self.maxCases, self.maxStep, self.isdebug)

def running(*args):
    from libs.objop import StrOperation
    ui = UIDriver()

    if len(args) == 1:
        args = StrOperation.splitStr(args[0], " ", '"')
    ui.setRunnerByArgs(True, args)
    ui.launch()

if __name__ == "__main__":
    from uimodel import UIToolBase
    print UIToolBase
    running("-r run -f uilocator.csv --maxStep 10")
