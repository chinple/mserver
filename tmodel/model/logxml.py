# -*- coding: utf8 -*-
'''
Created on 2010-9-28

@author: chinple
'''
import codecs
import time
from sys import stderr, stdout
from libs.xml import XmlDataGenerator
from libs.syslog import slog

class TestLoggerFactory(object):
    def __init__(self):
        self._loggers = []

    def init(self, logFilePath, isXmlLog=False, xsl="", lineEnd="\r\n"):
        for logger in self._loggers:
            if logFilePath != logger.getLoggerPath():
                logger.init(logFilePath, isXmlLog, xsl, lineEnd)

    def registerLogger(self, logCls, logFilePath="", isXmlLog=False):
        logger = logCls()
        logger.init(logFilePath, isXmlLog)
        self._loggers.append(logger)

    def getLoggerPath(self):
        logFiles = ""
        for logger in self._loggers:
            loggerPath = logger.getLoggerPath()
            if loggerPath != "" and loggerPath != None:
                logFiles += (", " if logFiles != "" else "") + loggerPath
        return logFiles

    def beginTestCase(self, testModule, testName, testInfo, testParam, searchKey):
        for logger in self._loggers:
            logger.beginTestCase(testModule, testName, testInfo, testParam, searchKey)

    def endTestCase(self, caseName, result, rescode, executetime):
        for logger in self._loggers:
            logger.endTestCase(caseName, result, rescode, executetime)

    def step(self, log):
        for logger in self._loggers:
            logger.step(log)

    def info(self, log):
        for logger in self._loggers:
            logger.info(log)

    def success(self, log):
        for logger in self._loggers:
            logger.success(log)

    def warn(self, log):
        for logger in self._loggers:
            logger.warn(log)

    def error(self, log):
        for logger in self._loggers:
            logger.error(log)

    def infoText(self, formator, *args):
        for logger in self._loggers:
            logger.infoText(formator, *args)

    def warnText(self, formator, *args):
        for logger in self._loggers:
            logger.warnText(formator, *args)

    def close(self):
        for logger in self._loggers:
            logger.close()

class TestLogger:
    def __init__(self, logFilePath=None, isXmlLog=False, isAppend=False):
        self.__isInHandler = False
        self.init(logFilePath, isXmlLog, isAppend=isAppend)

    def init(self, logFilePath, isXmlLog=False, xsl="", lineEnd="\r\n", isAppend=False):

        self.__end = lineEnd
        if self.__isInHandler:
            return

        self.__filePath = logFilePath
        self.__logFile = None

        self.__logLine = stdout.writelines
        self.__errorLine = stderr.writelines
        tempTypeStr = logFilePath.__class__.__name__
        if tempTypeStr == 'str' or tempTypeStr == 'unicode':
            if len(logFilePath) > 0:
                self.__logFile = codecs.open(logFilePath, "a" if isAppend else "w", "utf-8", buffering=0)
                self.__logLine = self.__logFile.writelines
                self.__errorLine = self.__logLine
        elif logFilePath != None:
            self.__isInHandler = True
            self.__logLine = logFilePath
            self.__errorLine = self.__logLine

        self.__isXmlLog = isXmlLog
        if isXmlLog:
            self.__xlog = XmlDataGenerator([
      {'name':'TestLog', 'findex':-1}
    , {'name':'TestCase', 'findex':0}
    , {'name':'step', 'findex':1}
    , {'name':'input', 'findex':2, 'must':False, 'alias':['Validate']}
    , {'name':'Info', 'findex':3, 'must':False, 'alias':['Success', 'Warn', 'error']}
    , {'name':'Result', 'findex':1, 'must':False, 'cls':0}
], None if isXmlLog else self.infoText, xsl)

    def __log(self, levelIndex, eleName, content, **eleAttrs):
        try:
            if content != None:
                content = "%s %s" % (time.strftime("[%Y-%m-%d %H:%M:%S]"), content)
            if self.__isXmlLog:
                self.__xlog.AddElement(eleName, content, **eleAttrs)
            else:
                eleAttrDesp = ""
                for eleAttr in eleAttrs.keys():
                    eleAttrDesp = eleAttrDesp + " [%s] %s" % (eleAttr, eleAttrs[eleAttr])
                self.__logLine("%s<%s> %s%s\r\n" % ("\r\n" if levelIndex == 0 else (levelIndex * 2 * " "),
                    eleName, content if content != None else '', eleAttrDesp))
        except Exception as ex:
            slog.warn("Logging: %s" % ex)

    def getloggerpath(self):
        try:
            return self.__filePath
        except:
            return ""

    def beginTestCase(self, testModule, testName, testInfo, testParam, searchKey):
        self.__log(0, "TestCase", None, casename=testName, param=testParam, description=testInfo)

    def endTestCase(self, caseName, result, rescode, executetime):
        self.__log(1, "Result", None, casename=caseName, result=result, rescode=str(rescode), time=str(executetime))

    def step(self, log):
        self.__log(1, "Step", None, description=log)

    def info(self, log):
        self.__log(3, "Info", log)

    def success(self, log):
        self.__log(3, "Success", log)

    def warn(self, log):
        self.__log(3, "Warn", log)

    def error(self, log):
        self.__log(3, "Error", log)

    def infoText(self, formator, *args):
        if formator != None:
            self.__logLine(formator % args if len(args) > 0 else formator)
            self.__logLine(self.__end)

    def warnText(self, formator, *args):
        if formator != None:
            self.__errorLine(formator % args if len(args) > 0 else formator)
            self.__errorLine(self.__end)

    def close(self):
        if self.__isXmlLog:
            self.__logLine(str(self.__xlog))
        if self.__logFile != None:
            self.__logFile.close()
            self.__logLine = stdout.writelines
