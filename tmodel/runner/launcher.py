'''
Created on 2011-2-21

@author: chinple
'''
from libs.objop import ArgsOperation
from libs.refrect import DynamicLoader
import sys
from tmodel.runner.vdriver import TestViewDriver
from libs.syslog import slog

def loadGroupRun(cases, gi, runargs, caseruninfo):
    from mtest import driver
    tl = TestLoader(driver, mtArgs=runargs)
    tl.logFilePath = ["group_%s.log" % gi]
    tl.tcPattern = cases
    tl.rungroup = []
    tl.pergroup = 0
    tl.sender, tl.receiver, tl.smtp, tl.smtpLogin = "", "", "", ""

    slog.info("Group %s running %s cases: %s" % (gi, cases.count("|") + 1, cases))
    tl.launch(True)
    caseruninfo.put(driver.tc.tcInfos)

class TestLoader:
    def __init__(self, driver, args=None, mtArgs=None):
        self.driver = driver
        if args is not None:
            mtArgs, parseMsg, isSuccess = ArgsOperation.parseArgs(args, [], None, *self.__getDefine())
            slog.info(parseMsg)
            if not isSuccess:
                sys.exit(-1)
        self.__defineArgs(mtArgs)

    def __defineArgs(self, mtArgs):
        self.mtArgs = mtArgs
        
        self.logFilePath = mtArgs.log

        self.testrunConfig = mtArgs.config
        self.runMode = mtArgs.mode
        self.tcPattern = mtArgs.__dict__['in']
        self.outTcPattern = mtArgs.__dict__['out']

        self.rerun = mtArgs.rerun
        self.rungroup = mtArgs.group
        self.pergroup = mtArgs.pergroup
        self.isbyname = mtArgs.isbyname
        self.grouptimeout = mtArgs.timeout

        self.codeFile = mtArgs.code
        self.baseClass = mtArgs.base
        self.nameSpaceName = mtArgs.namespace
        self.graphPath = mtArgs.graph

        self.curDir = mtArgs.dir
        self.propConf = mtArgs.prop

#        self.chost = mtArgs.chost
#        self.cport = mtArgs.cport

        self.smtp = mtArgs.smtp
        self.sender = mtArgs.sender
        self.receiver = mtArgs.receiver
        self.smtpLogin = mtArgs.smtpLogin

        self.product = mtArgs.product
        self.version = mtArgs.version
        self.environment = mtArgs.environment

        self.fileList = mtArgs.file
        self.ignoreImportExcept = False

    def launch(self, returnRuninfo=False):
        driver = self.driver
        if self.runMode.startswith("m"):
            driver = TestViewDriver(self.driver)

        driver.initDriver(**self.__dict__)
        runInfo = driver.runDriver(*self.__loadModels())
        if isinstance(runInfo, list):
            from tmodel.runner.driver import GroupTestDriver
            gt = GroupTestDriver(driver)
            runInfo = gt.runInProcess(runInfo, loadGroupRun, self.mtArgs)
        driver.endDriver()
        if isinstance(runInfo, dict):
            self.report(runInfo)
        if returnRuninfo:
            return runInfo
        try:
            return runInfo[2]
        except:pass

    def report(self, runInfo):
        from tmodel.runner.logsummary import SummaryReport
        sr = SummaryReport()
        sr.analyzeLogs(self.product, self.version, self.environment, runInfo)
        if self.smtp.strip() != "":
            sr.sendEmail(self.smtp, self.smtpLogin, self.sender, self.receiver)

    def __loadModels(self):
        return DynamicLoader.getClassFromFile("ModelDecorator", self.ignoreImportExcept, *self.fileList)

    def __getDefine(self):
        return  (('-', '''%prog [options]
    %prog argumentJsonFile
The file content must be the following:
    ["--file", "Test1.py", "--file", "Test2.py", "--mode", "run"]
or,
    {"file":["Test1.py", "Test2.py"], "mode":"rerun"}
or xml,
    <RunArgs>
       <Property name="file" value="Test1.py" /> <Property name="file" value="Test2.py" /> <Property name="mode" value="run" />
    </RunArgs>

Example:
    %prog --file Test1.py --file Test2.py --mode rerun
    %prog RunArgs.json'''),

    ("f", "file", "fileList", [], "list"),
    ("r", "mode", "runMode: run, rerun, param, look, show, scenario, slook", "show"),
    ("d", "dir", "folderPath, cwd to folderPath before executing test cases"),
    ("l", "log", "test log file", [], 'list'),

    ("c", "config", "test run config file", "mtest.ini"),
    ("p", "prop", "propName=PropValue, configure mtest.ini by CMD arguments", [], "prop"),

    ("i", "in", "tcPattern"),
    ("o", "out", "outTcPattern"),

    ("rerun", "rerunTimes: rerun failed cases rerunTimes", 1, "int"),
    ("k", "group", "run test cases in groups by key word(testtype=p1)", [], "list"),
    ("pergroup", "pergroupNum, run pergroupNum test cases in many groups when not using group", 0, "int"),
    ("isbyname", "isbyname: true means group represent test case name reg otherwise search key word reg", "false", 'bool'),
    ("timeout", "grouptimeout, set timeout(seconds) for every group when run cases in groups by asynchronous thread", 0, "int"),

    ("code", "codeFile"), ("graph", "graphPath"),
    ("base", "baseClass", "TestCaseBase"),
    ("namespace", "namespace", "mtestGeneratedCode"),
    
    ("smtp", "smtpAddress, such as mail.163.com:465"),
    ("sender", "mail sender"),
    ("receiver", "mail receiver, such as a@qq.com;b@163.com"),
    ("smtpLogin", "such as:account/password, base64encoding"),
    ("logServer", "log server of ctool"),

    ("product", "product information, such as product 1.0"),
    ("version", "product version, such as version 1.0"),
    ("environment", "environment, test environment information"))
