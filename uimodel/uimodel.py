'''
Created on 2017-7-11

@author: xinxiu
'''
from random import randint
from libs.parser import JsonParser
import time
from libs.syslog import slog

class UIToolBase:
    def click(self, path, locator):
        slog.info("click %s: %s" % (path, locator))
    def input(self, path, locator, value):
        slog.info("input %s: %s" % (path, locator))
    def getCurrentPage(self, pages):
        names = pages.keys()
        return names[randint(0, len(names) - 1)]
    def pauseUI(self):
        slog.info("pause ui")
    def startUI(self):
        slog.info("start ui")
    def openUI(self):
        slog.info("open ui")
    def closeUI(self):
        slog.info("close ui")

# pageName, eleName, elelocator, uitype, isendui, uiweight
class UIContainer:
    def __init__(self):
        self.uipages = {}

    def loadUI(self, uicsv):
        for e in JsonParser().csvToDict(uicsv):
            self.addUIEle(**e)

    def setUI(self, uitool, strategy="default"):
        self.uitool = uitool
        self.strategy = strategy

    def getUIPage(self, pageName, pagelocator=None):
        if self.uipages.__contains__(pageName):
            page = self.uipages[pageName]
        else:
            page = {'l':pagelocator, 'e':{}}
            self.uipages[pageName] = page
        return page

    def addUIEle(self, pageName, eleName, elelocator, uitype, uivalue=None, isendui=False, uiweight=1, **eleProps):
        # uitype: click input select page
        page = self.getUIPage(pageName, elelocator)
        if uitype == "page":
            page['l'] = elelocator
        else:
            page['e'][eleName] = {'l':elelocator, 'p':uitype, 'v':uivalue, 'e':isendui, 'w':uiweight, 't':0}  # t trigger times

    def getRandomUIEle(self, pageName, ispath=True):
        page = self.getUIPage(pageName)
        eles = page['e'].keys()
        eleName = eles[randint(0, len(eles) - 1)]
        return "%s.%s" % (pageName, eleName) if ispath else eleName
    
    def getCurrentPage(self):
        return self.uitool.getCurrentPage(self.uipages)
    
    def triggerUIEle(self, uipath):
        pageName, eleName = uipath.split(".")
        ele = self.getUIPage(pageName)['e'][eleName]
        if ele['t'] == 'input':
            self.uitool.input(uipath, ele['l'], ele['v'])
        else:
            self.uitool.click(uipath, ele['l'])

    def restartUI(self):
        self.uitool.pauseUI()
        self.uitool.startUI()

    def openUI(self):
        if len(self.uipages) == 0:raise UINotReadyException("No page elements, please load from csv")
        self.uitool.openUI()

    def closeUI(self):
        self.uitool.closeUI()

class UICrashException(Exception):pass
class UINotExistException(Exception):pass
class UINotReadyException(Exception):pass

class UICaseModel:
    results = "Started Success Fail Crash NotExist".split()

    def __init__(self):
        self.cases = {}

    def study(self, ui, maxCases, maxStep, isdebug):
        ui.openUI()
        try:
            c = 0
            while c < maxCases:
                c += 1
                caseid = self.startACase(ui, maxStep, isdebug)
                slog.info(self.formatACase(caseid))
        finally:
            ui.closeUI()
            self.sumCase()

    def startACase(self, ui, maxStep, isdebug):
        caseid = self._createCase()
        triggerid = 0
        while triggerid < maxStep:
            triggerid += 1
            if isdebug:
                self._triggerUIStep(caseid, ui)
                continue
            try:
                self._triggerUIStep(caseid, ui)
            except UICrashException:
                self.setTrigger(caseid, triggerid, -1, 3)
            except UINotExistException:
                self.setTrigger(caseid, triggerid, -1, 4)
        ui.restartUI()
        return caseid

    def sumCase(self):
        s = list([0] * len(self.results))
        for c in self.cases:
            case = self.cases[c]
            s[case[len(case) - 1]['r']] += 1
        for i in range(len(s)):
            slog.info("%s:\t%s" % (self.results[i], s[i]))

    def _createCase(self):
        case = []
        caseid = len(self.cases)
        self.cases[caseid] = case
        return caseid

    def _triggerUIStep(self, caseid, ui):
        pageName = ui.getCurrentPage()
        if pageName is None:raise UINotReadyException("current page is None")
        uipath = ui.getRandomUIEle(pageName)
        triggerid = self.addTrigger(caseid, uipath)
        try:
            tritime = time.time()
            triresult = 2
            ui.triggerUIEle(uipath)
            triresult = 1
        finally:
            tritime = time.time() - tritime
            self.setTrigger(caseid, triggerid, tritime, triresult)

    def formatACase(self, caseid):
        case = []
        for c in self.cases[caseid]:
            case.append("{p}({0} {t})".format(self.results[c['r']], **c))
        return "-> ".join(case)

    def addTrigger(self, caseid, uipath, tritime=0, triresult=0):
        triggerid = len(self.cases[caseid])
        self.cases[caseid].append({'p':uipath, 't':tritime, "r":triresult})
        return triggerid

    def setTrigger(self, caseid, triggerid, tritime=0, triresult=0):
        trigger = self.cases[caseid][triggerid]
        if tritime > 0:
            trigger['t'] = tritime
        trigger["r"] = triresult

if __name__ == "__main__":
    uic = UIContainer()
    uic.loadUI("uilocator.csv")
    print uic.getRandomUIEle("mainpage")
