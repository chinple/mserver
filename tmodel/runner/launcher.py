'''
Created on 2011-2-21

@author: chinple
'''
from libs.objop import ArgsOperation
from mtest import tlog
from libs.refrect import DynamicLoader
import sys
from tmodel.runner.vdriver import TestViewDriver

class TestLoader:
    def __init__(self, driver, args):
        self.driver = driver
        mtArgs, parseMsg, isSuccess = ArgsOperation.parseArgs(args, [], None, *self.__getDefine())
        tlog.infoText(parseMsg)
        if not isSuccess:
            sys.exit(-1)
        self.__defineArgs(mtArgs)

    def __defineArgs(self, mtArgs):
        
        self.logFilePath = mtArgs.log
        self.isXmlLog = mtArgs.isxmllog

        self.testrunConfig = mtArgs.config
        self.runMode = mtArgs.mode
        self.tcPattern = mtArgs.__dict__['in']
        self.outTcPattern = mtArgs.__dict__['out']
        self.searchKey = mtArgs.searchKey

        self.rerun = mtArgs.rerun
        self.runGroup = mtArgs.group
        self.perGroup = mtArgs.pergroup
        self.isAsyncRun = mtArgs.isasync
        self.isDupInGroup = mtArgs.isdup
        self.isGroupByName = mtArgs.isbyname
        self.groupTimeout = mtArgs.timeout

        self.codeFile = mtArgs.code
        self.baseClass = mtArgs.base
        self.nameSpaceName = mtArgs.namespace
        self.graphPath = mtArgs.graph

        self.curDir = mtArgs.dir
        self.propConf = mtArgs.prop

        self.chost = mtArgs.chost
        self.cport = mtArgs.cport

        self.smtp = mtArgs.smtp
        self.sender = mtArgs.sender
        self.receiver = mtArgs.receiver

        self.login = mtArgs.login
    
        self.ftpserver = mtArgs.ftpserver
        self.httpserver = mtArgs.httpserver
        self.product = mtArgs.product
        self.environment = mtArgs.environment

        self.fileList = mtArgs.file
        self.ignoreImportExcept = False

    def launch(self):
        driver = self.driver
        if self.runMode.startswith("m"):
            driver = TestViewDriver(self.driver)

        driver.initDriver(**self.__dict__)
        driver.runDriver(*self.__loadModels())
        driver.endDriver()
    
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

    ("c", "config", "test run config file", "mtest.ini"),
    ("p", "prop", "propName=PropValue, configure mtest.ini by CMD arguments", [], "prop"),

    ("l", "log", "test log file", "testlog.log"),
    ("x", "isxmllog", "isxmllog: is using xml-formatted log", "false", "bool"),
    
    ("i", "in", "tcPattern"),
    ("o", "out", "outTcPattern"),
    ("k", "searchKey", "searchKey"),

    ("rerun", "rerunTimes: rerun failed cases rerunTimes", 1, "int"),
    ("group", "runGroupReg: run test cases in many groups", [], "list"),
    ("pergroup", "perGroupNum, run perGroupNum test cases in many groups when not using group", 0, "int"),
    ("isasync", "isAsyncRun: true means run cases in groups by asynchronous thread otherwise synchronous thread", "true", "bool"),
    ("isdup", "isDupInGroup: true means allow duplicate cases in groups otherwise every case only run a time in all groups", "false", "bool"),
    ("isbyname", "isGroupByName: true means /group represent test case name reg otherwise search key word reg", "true"),
    ("timeout", "groupTimeout, set timeout(seconds) for every group when run cases in groups by asynchronous thread", 0, "int"),
    
    ("code", "codeFile"), ("graph", "graphPath"),
    ("base", "baseClass", "TestCaseBase"),
    ("namespace", "namespace", "mtestGeneratedCode"),

    ("chost", "ServerHost"),
    ("cport", "ServerPort", 80, "int"),
    
    ("smtp", "smtpAddress, such as mail.aliyun.com:465"),
    ("sender", "mail sender"),
    ("receiver", "receiver: report mail receiver", [], "list"),
    
    ("login", "account and password, such as /login:ftp=account,password;smtp=account,password;"),
    ("ftpserver", "ftpserver, such as ftp://hostname/ftpPath/"),
    ("httpserver", "httpserver, such as http://hostname/Logs/ftpPath/"),
    ("product", "product information, such as version 1.0"),
    ("environment", "environment, test environment information"))
