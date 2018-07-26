'''
Created on 2010-9-28

@author: chinple
'''
import logging
from logging.handlers import TimedRotatingFileHandler

class SysLogManager:
    def __init__(self):
        self.__logs = {}
        self.setProcessId()

    def getLog(self, logName, logType=None, level=logging.DEBUG,
            logFormat=None):
        # @logType, none, stdout, error or log file path
        if self.__logs.__contains__(logName):
            return self.__logs[logName]
        else:
            logger = logging.getLogger(logName)
            logger.setLevel(level)
            self.__logs[logName] = logger
            return self.resetHandler(logger, logType, logFormat)

    def removeHandler(self, logger, startHandler):
        for i in range(startHandler, len(logger.handlers)):
            logger.removeHandler(logger.handlers[i])

    def resetHandler(self, logger, logType, logFormat='%(asctime)s [%(filename)s:%(lineno)s] %(levelname)s %(message)s'):
        self.removeHandler(logger, 0)
        if logType == None or logType == "stdout" or logType == "error":
            self.addConsoleHandler(logger, logFormat, logType)
        else:
            self.addFileHandler(logger, logFormat, logType)
        return logger

    def setProcessId(self, pid=0):
        # support @multiprocessing @fork by setting different log file name
        self.pid = pid

    def addFileHandler(self, logger, logFormat, logPath):
        if self.pid > 0:
            try:
                i = logPath.index(".")
                logPath = "%s-%s%s" % (logPath[0:i], self.pid, logPath[i:])
            except:
                logPath = "%s-%s" % (logPath, self.pid)

        tfHandler = TimedRotatingFileHandler(logPath, 'MIDNIGHT')
        tfHandler.setFormatter(logging.Formatter(logFormat))
        logger.addHandler(tfHandler)

    def addConsoleHandler(self, logger, logFormat, consoleType):
        import sys
        console = logging.StreamHandler(sys.stderr if consoleType == 'error' else sys.stdout)
        console.setFormatter(logging.Formatter(logFormat))
        logger.addHandler(console)

logManager = SysLogManager()
slog = logManager.getLog("slog")
plog = logManager.getLog("plog")

def setLogfile(slogfile=None, plogfile=None):
    if slogfile is not None:
        logManager.resetHandler(slog, slogfile)
    if plogfile is not None:
        logManager.resetHandler(plog, plogfile)
