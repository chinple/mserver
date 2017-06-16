'''
Created on 2016-12-16

@author: chinple
'''
import time
from tools.cmd.syscmd import CmdExecuter
from libs.parser import toJsonObj
import os
from random import randint

class CurlCmdWrapper:
    def __init__(self, curlPath='/usr/bin/curl'):
        self.curlPath = curlPath

    def makeFormValue(self, name, value, filetype=None):
        return '%s=%s%s' % (name, value, '' if filetype is None else (';type=%s' % filetype))

    def __makeArgs(self, name, value):
        if (value is None or value == ''):return ''
        return " %s '%s'" % (name, str(value).replace("'", "''"))

    def _makeCurlCmd(self, url, curlBody, command, headers, headerFile, isFormRequest, sslVersion):

        header, body, fargs = "", "", ""

        # body
        if isFormRequest:
            for fn in curlBody:
                body += self.__makeArgs("--form", curlBody[fn])
        elif curlBody != '':
            body = self.__makeArgs("-d", curlBody)

        # header
        if headers is not None:
            for h in headers.keys():
                header += self.__makeArgs("-H" , "%s:%s" % (h, headers[h]))
        header += self.__makeArgs("-D", headerFile)

        return "{curl} {request} {ssl} '{url}' {body} {fargs} {header}".format(curl=self.curlPath,
            request=self.__makeArgs('--request', command), ssl=('-k -%s' % sslVersion) if sslVersion > 0 else None,
            url=url, body=body, fargs=fargs, header=header)

    def _parseHeaderFile(self, headerFile):
        header = {}
        for l in open(headerFile, 'r').read().split('\r\n'):
            try:
                i = l.index(":")
                header[l[0:i].strip().lower()] = l[i + 1:].strip()
            except:pass
        os.system("rm -rf %s" % headerFile)
        return header
        
    def curlByCmd(self, url, body=None, command=None, isFormRequest=False, headers=None, isRespHeader=False, isLogResp=True, logHandler=None, sslVersion= -1):
        headerFile = ("header-%s-%s.txt" % (time.time(), randint(10, 1000))) if isRespHeader else None
        curlcmd = self._makeCurlCmd(url, body, command, headers, headerFile, isFormRequest, sslVersion)
        if logHandler:
            logHandler(curlcmd)

        resp = CmdExecuter(curlcmd)
        if isLogResp and logHandler:
            logHandler(resp)
        try:
            resp = toJsonObj(str(resp))
        except:pass

        if isRespHeader:
            return self._parseHeaderFile(headerFile), resp
        else:
            return resp
