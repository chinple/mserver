# -*- coding: utf8 -*-
'''
Created on 2015-8-19

@author: chinple
'''

from cserver import cloudModule
from server.chandle import parseRequestParam, tryGet
from libs.objop import ObjOperation, StrOperation
from libs.tvg import TValueGroup
from server.cclient import curl, jsonToUrlValue
from libs.parser import toJsonObj
from libs.syslog import plog, slog
from server.cclient2 import CurlCmdWrapper, httpscurl
from tools.cmd.syscmd import CmdExecuter


class HttpToolBase:

    def jsonFromUrlargs(self, urlParam, tupeKey="goodsList"):
        pjson = {}
        params = parseRequestParam(urlParam)
        for k in params:
            v = params[k]
            tjson = pjson
            try:
                i = k.index("[")
                key, k = k[0:i], k[i + 1:]
            except:
                pjson[k] = v
                continue

            keys = [key] + k.replace("][", ",").replace("[", "").replace("]", "").split(",")
            for i in range(len(keys)):
                key = keys[i]
                if i < len(keys) - 1:
                    try:
                        tjson = tjson[key]
                    except:
                        if type(tjson) == list:
                            key = int(key)
                            while len(tjson) <= key:
                                tjson.append({})
                            tjson = tjson[key]
                        else:
                            tjson[key] = [] if tupeKey.__contains__(key) else {}
                            tjson = tjson[key]
                else:
                    tjson[key] = v
        return pjson

    def jsonToUrlargs(self, jsonStr):
        return jsonToUrlValue(toJsonObj(jsonStr))

    def jsonDiff(self, jsonStr, jsonStr2):
        return "%s\n%s" % ObjOperation.jsonEqual(TValueGroup(jsonStr).__prop__, TValueGroup(jsonStr2).__prop__)

    def httprequest(self, command="POST", url="", header="", body="",
            bodyArgs="{0},{1}", reqsetting="isRespHeader:true;sslVersion:-1;connTimeout:60", isjsonresp=True):
        command = command.upper()
        if bodyArgs != "":  
            url = self.__replaceArgStr(url, bodyArgs)
            body = self.__replaceArgStr(body, bodyArgs)
        h = self.__toHeaders(header)
        reqsetting = self.__toHeaders(reqsetting)

        if url.startswith("https") or command.__contains__("FORM") or command.__contains__("CURL"):
            if not command.__contains__("CURL"):
                resp = httpscurl(url, body, command, h, tryGet(reqsetting, 'isRespHeader', 'false') == 'true')
            else:
                command = command.replace("CURL", '')
                resp = self.__curlHttpRequest(url, body, command, h,
                    tryGet(reqsetting, 'isRespHeader', 'false') == 'true', tryGet(reqsetting, 'sslVersion', '-1'))
        else:
            resp = curl(url, body, command=command, logHandler=plog.info, connTimeout=int(tryGet(reqsetting, 'connTimeout', '60')), ** h)
        if isjsonresp:
            try:
                return toJsonObj(resp)
            except:pass
        return resp

    curlcmd = CurlCmdWrapper(CmdExecuter)

    def __toHeaders(self, hs):
        try:
            return toJsonObj(hs)
        except:pass

        headers = {}
        for hv in hs.split(";"):
            hi = hv.find(":")
            if hi > 0:
                h, v = hv[0:hi].strip(), hv[hi + 1:].strip()
                if len(h) > 0:
                    headers[h] = v
        return headers

    def __splitUrl(self, url):
        url = url.replace("http://", "").replace("https://", "")
        try:
            i = url.index("/")
            hosts, path = url[0:i], url[i:]
        except:
            hosts, path = url, ""
        return hosts, path

    def __replaceArgStr(self, argStr, argRplace):
        try:
            argIndex = 0
            for arg in StrOperation.splitStr(argRplace, ",", "'"):
                argStr = argStr.replace("{%s}" % argIndex, arg)
                argIndex += 1
        except:pass
        return argStr

    def __curlHttpRequest(self, url, body, command , headers, isRespHeader, sslVersion):
        isFormRequest = command.__contains__("FORM")
        if isFormRequest:
            command, body = command.replace("FORM", ''), toJsonObj(body)
            for f in body.keys():
                value = body[f]
                body[f] = self.curlcmd.makeFormValue(f, value, filetype=None)
        return self.curlcmd.curlByCmd(url, body, command, isFormRequest, headers, isRespHeader, isLogResp=False, logHandler=slog.info,
            sslVersion=int(sslVersion))


@cloudModule(urlParam={"t":'textarea'}, param={"t":'textarea'}, svnPath={"t":'textarea'}, urlParam2={"t":'textarea'}, jsonStr={"t":'textarea'}, jsonStr2={"t":'textarea'},
    header={"t":'textarea'}, body={"t":'textarea'},
    urlParamToJson={'desp':"convert url parameter to json"}, jsonToUrlParam={'desp':'convert json to url parameter'})
class HttpTool(HttpToolBase):
    pass


@cloudModule()
class CommonTool:

    def md5(self, s):
        import md5
        m = md5.new()
        m.update(s)
        return m.hexdigest()


if __name__ == "__main__":
    from cserver import servering
    servering(" -p 8085 -n http-tool-test -s 172.16.12.124:8080")

