'''
Created on 2010-11-8

@author: chinple
'''
import time
import os
import subprocess

class CmdExecuter:
    def __init__(self, cmd, popenUsed=True, isStaticTime=False, isAsync=False):
        self.cmdstr = cmd

        cmdres = ""
        cmderr = ""
        returncode = 0
        if isStaticTime:
            cmdTime = time.time()
        if popenUsed or isAsync:
            proc = subprocess.Popen(self.cmdstr, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if not isAsync:
                cmdres, cmderr = proc.communicate()
#                proc.wait()
#                cmdres = os._wrap_close(io.TextIOWrapper(proc.stdout), proc).read()
#                cmderr = os._wrap_close(io.TextIOWrapper(proc.stderr), proc).read()
                returncode = proc.returncode
        else:
            returncode = os.system(self.cmdstr)
            
        if isStaticTime:
            self.cmdTime = time.time() - cmdTime
        self.retcode = returncode
        self.cmdres = cmdres
        self.cmderr = cmderr

    def __str__(self, isRspOnly=True):
        if isRspOnly:
            return self.cmdres
        return "> %s\n%s\n%s%s" % (self.cmdstr, self.retcode, self.cmdres, self.cmderr)



# p = subprocess.Popen(["ssh -l root -p 36000 183.60.82.9 hostname"],
#     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
# print(p.stdout.read())
