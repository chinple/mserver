'''
Created on 2012-3-21

@author: chinple
'''
from libs.ini import IniConfigure
class ServerDriver:
    def __init__(self):
        self.cserviceInfo = []
        self.cserviceProxy = []
        self.cprop = IniConfigure()

    def addServiceProxy(self, cserviceCls, handleUrl):
        if handleUrl is not None and handleUrl.strip() != "":
            self.cserviceProxy.append((cserviceCls, handleUrl))

    def addService(self, moduleCls, handleUrl, moduleInfo):
        self.cserviceInfo.append((moduleCls, handleUrl, moduleInfo))

    def startService(self):
        self.__registerService(self.__getLocalExIp(), self.ports)

        from server.claunch import launchHttpServer
        launchHttpServer(self._serverArgs, self.ports)

    def __getLocalExIp(self):
        try:
            import socket
            return socket.gethostbyname_ex(socket.gethostname())[2][0]
        except:return ""

    def __registerService(self, exip, ports):
        from libs.syslog import slog
        slog.warn("%s:%s register to %s with %s" % (exip, ", ".join([str(p) for p in ports]), self.regServer, self.regName))
        if self.regServer is not None:
            from server.cclient import curlCservice
            curlCservice(self.regServer, 'CServiceTool/RegistServer',
                hostport="%s:%s" % (exip, ports[0]), serverName=self.regName)

    def setDriverByArgs(self, args):
        from libs.objop import ArgsOperation

        cArgs, parseMsg, isSuccess = ArgsOperation.parseArgs(list(args), [], None, *self.__getDefine())
        from libs.syslog import slog
        slog.info(parseMsg)
        if not isSuccess:
            import sys
            sys.exit(-1)

        import os
        if cArgs.config != None and os.path.exists(cArgs.config):
            self.cprop.load(cArgs.config)

        self.regServer = cArgs.regServer
        self.regName = cArgs.regName
        self.ports = [8089] if len(cArgs.ports) == 0 else cArgs.ports
        host, port = "", int(self.ports[0])
        self._serverArgs = (host, port, cArgs.timeout, cArgs.isCpuPriority, cArgs.webroot, cArgs.mainpage, cArgs.uploadFolder,
            cArgs.servicePath, self.cserviceInfo, self.cserviceProxy, cArgs.stubFiles, cArgs.processes, cArgs.setProcessLog)
        del cArgs
    
    def __getDefine(self):  

        return (("c", "config", "run properties file", "cservice.ini"),

    ("t", "stubFiles", "python stub files", [], 'list'),
    ("f", "webroot", "Html folder", "NotConfigure"),
    ("uploadFolder", "upload folder", ""),
    ("m", "mainpage", "home or main page, such as HomePage.html"),
    ("o", "timeout", "timeout", 5, "float"),

    ("p", "ports", "http ports, such as -p 80 -p 8080", [], "list"),
    ("isCpuPriority", "CPU priority: request handle by process (logs may lost) if true, otherwise request handle by threads", False, "bool"),
    ("processes", "processes launched: for Linux fork process, for windows create sub process", 1, "int"),
    ("setProcessLog", "when forking process, set different log name for each process if true", False, "bool"),

    ("servicePath", "URL path of service", "cservice"),
    ("s", "regServer", "register server address", None),
    ("n", "regName", "register server name", None)
)

