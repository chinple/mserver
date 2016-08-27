# -*- coding: utf8 -*-
'''
Created on 2015-8-19

@author: chinple
'''

from cserver import cloudModule
import time
import os
from server.cclient import curlCservice
from libs.objop import ObjOperation
from libs.syslog import plog

pkFolder = '/data/test/builds/uploads'

pkHost = "127.0.0.1"
pkHostName = "package.itd.com"

gitHost = "git.code.com"
gitBash = "git clone"

svnBash = 'export LC_CTYPE="zh_CN.UTF-8";svn export %s %s --username=%s --password=%s --no-auth-cache --trust-server-cert --non-interactive'
svnUser, svnPasswd = "user", "password"

moduleFile = "module.js"

@cloudModule(urlParam={"t":'textarea'}, param={"t":'textarea'}, svnPath={"t":'textarea'}, urlParam2={"t":'textarea'}, jsonStr={"t":'textarea'}, jsonStr2={"t":'textarea'},
    body={"t":'textarea'},
    urlParamToJson={'desp':"convert url parameter to json"}, jsonToUrlParam={'desp':'convert json to url parameter'})
class PackageTool:
    moduleConfig = None

    def packageCode(self, module, branch='trunk', svnPath="", codeIp=""):

        config = ObjOperation.tryGetVal(self.getModuleInfo(), module, {})
        packageName = "%s-%s-%s" % (module , branch, time.strftime("%Y%m%d-%H%M"))
        pkFile = '%s/%s.tar' % (pkFolder, packageName)
        if os.path.exists(pkFile):
            return 0, packageName

        # package code
        path = ObjOperation.tryGetVal(config, branch, svnPath)
        if path == "":
            path = ObjOperation.tryGetVal(config, "trunk", svnPath)
        resp = curlCservice(pkHost, "PackageTool/packageToLocalFolder", isCheckResp=True, curlHeader={"host":pkHostName},
            path=path, module=module, branch=branch,
            packageName=packageName, toFolder=ObjOperation.tryGetVal(config, "deployFolder", module))
        plog.info(resp)

        # down load code
        downloadPkCmd = 'wget %s/file/%s_tar  --header="Host: %s" -q -O %s > /dev/null' % (pkHost, packageName, pkHostName, pkFile)
        os.system(downloadPkCmd)

        try:
            resp = curlCservice(pkHost, "PackageTool/deletePackage", isCheckResp=True, curlHeader={"host":pkHostName},
                packageName=packageName)
        except Exception as ex:
            return ex

        # check package
        if os.path.exists(pkFile):
            fsize = os.path.getsize(pkFile)
            if fsize < 20480:
                os.system("rm -rf %s" % pkFile)
        else:
            fsize = -1
        return fsize, packageName

    def addModule(self, moduleName, codeTrunk, deployFolder, deployBase='/data/release', config='', sh='',
            fileDeploy="false", existDeploy="true"):
        if moduleName != "":
            self.moduleConfig[moduleName] = { 'trunk':codeTrunk,
                'deployFolder':deployFolder, 'deployBase':deployBase, 'config':config, 'sh':sh,
                'fileDeploy':fileDeploy, 'existDeploy':existDeploy}
            open(moduleFile, "w").write(str(self.moduleConfig))
        return self.moduleConfig

    def deleteModule(self, moduleName):
        self.moduleConfig.__delitem__(moduleName)
        return self.moduleConfig

    def getModuleInfo(self, isRefresh=False):
        if self.moduleConfig is None or str(isRefresh).lower() != "false":
            self.moduleConfig = eval(open(moduleFile).read())
        return self.moduleConfig

    def deletePackage(self, packageName):
        delPackage = "rm -rf %s/%s_tar" % (pkFolder, packageName)
        return os.system(delPackage)

    def packageToLocalFolder(self, path="", packageName="", toFolder="", module="", branch="", isInFolder=True):
        tempFile = "%s/%s" % (pkFolder, toFolder)
        packageFile = "%s/%s_tar" % (pkFolder, packageName)

        if os.path.exists(tempFile):
            return "fail: downloading"

        if os.path.exists(packageFile):
            return "success: exist"

        server = "git" if path.__contains__(gitHost) else "svn"
        if server == "git":
            cmd = "%s %s %s %s %s" % (gitBash, module, branch, path, tempFile)
        else:
            cmd = svnBash % (path , tempFile, svnUser, svnPasswd)

        exeInfo = "success"
        if os.system(cmd) == 0:
            tarCmd = "cd %s;tar cf %s %s" % (pkFolder, packageFile, toFolder)
            os.system(tarCmd)
        else:
            exeInfo = "failed: execute upload code failed"

        delCmd = "rm -rf %s" % tempFile
        os.system(delCmd)
        return exeInfo

if __name__ == "__main__":
    from cserver import servering
    servering(" -p 8080 -n bill-tool-test")


