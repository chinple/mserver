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

def replaceIniconfig(toIniFile, fromIniFile):
    import codecs
    with codecs.open(fromIniFile, encoding="utf-8") as iniFile:
        while True:
            l = iniFile.readline()
            if l == '':
                break
            l = l.strip()
            try:
                c0 = l[0]
                if c0 == '#' or c0 == ";":continue
                i = l.index('=')
                n, v = l[0:i].strip(), l[i + 1:].strip()
                if n == "":continue
            except:continue
            v = v.replace("'", "''")
            cmd = "sed -i 's/%s.*=.*/%s=%s/g' %s" % (n, n, v, toIniFile)
            print cmd
            os.system(cmd)

# p = subprocess.Popen(["ssh -l root -p 36000 183.60.82.9 hostname"],
#     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
# print(p.stdout.read())
