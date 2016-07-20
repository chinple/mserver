'''

@author: chinple
'''
import subprocess
import time
from libs.timmer import TimmerOperation
import os
from libs.syslog import slog

class CmdTaskHandle:
    def __init__(self, logFolder="."):
        self.logFolder = logFolder
        import platform
        self.isWindows = 'Windows' in platform.system() 
        self.cmdSep = " & " if self.isWindows else " ; "

    def update(self, task):
        pass

    def prepare(self, task):
        task['folder'] = "."
        task['cmd'] = ""
        task['log'] = False

        task['p'] = None
        task['pid'] = 0
        task['time'] = -1
        task['ordinal'] = 0
        task['result'] = 0

    def initRun(self, task):
        maxSleepTime = 86400
        pid = task['pid']
        if pid == None or pid == "" or pid == 0:
            return True
        if self.isWindows:
            pidCheck = 'tasklist | findstr "%s"' % pid
        else:
            pidCheck = "ps aux |grep %s|awk '{print $2}'|grep %s" % (pid, pid)

        while maxSleepTime > 0:
            maxSleepTime -= 2
            resp = subprocess.Popen(pidCheck, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
            resp = resp.decode().split("\n")
            if resp.__contains__(str(pid)):
                time.sleep(2)
            else:
                break

    def run(self, task):
        task['ordinal'] += 1
        logCmd = ('> "%s" 2>&1' % self.__getLog__(task)) if task['log'] else ""
        folder = task['folder']
        cmdStr = "%s%s %s" % ("" if folder == "" else ("cd %s%s" % (folder, self.cmdSep)), task['cmd'], logCmd)
        slog.info(cmdStr)
        p = subprocess.Popen(cmdStr, shell=True)
        task['p'] = p
        task['pid'] = p.pid
        self.Update(task)
        task['result'] = p.wait()

    def endRun(self, task):
        task['p'] = None
        task['pid'] = 0

    def __getLog__(self, task):
        logDir = "%s/%s" %(self.logFolder, task['key'])
        if not os.path.exists(logDir):
            os.makedirs(logDir)
        nowTimeStr = TimmerOperation.getFormatTime(task["now"], timeFormat="%Y%m%d-%H%M%S")
        logPathNow = ""
        while True:
            logPathNow = '%s/timmer_%s_%s.log' % (logDir, task['ordinal'], nowTimeStr)
            if os.path.exists(logPathNow):
                task['ordinal'] += 1
                continue
            else:
                break
        return logPathNow
