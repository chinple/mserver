'''
Created on 2012-3-21

@author: chinple
'''

from server.chandle import RouterHandler, FileHandler, FolderHandler, \
    CServerHandler, FileUploadHandler, ObjHandler, SessionRouterHandler
import os
from libs.syslog import slog
import time
from BaseHTTPServer import HTTPServer
import sys

from SocketServer import ForkingMixIn
class ForkingHTTPServer(ForkingMixIn, HTTPServer):
# a process handle a request at the same time
# for long time request(IO wait), the performance is low 
# and the request may be blocked when request reaches 1024 at the same time
    max_children = 1024

from SocketServer import ThreadingMixIn
class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
# thread mode cost much CPU to create threads: thread.lock, thread.acquire, thread.release
# when TPS reach 1024(limited by ...), CPU may be 100% cost
# but if use os.fork(ForkingMixIn), at the same time the max requests <= max_children(process numbers)
# so use os.fork create process, which create threads to handle request
# if request failed for TIME_WAIT, please set:
# vi /etc/sysctl.conf
# net.ipv4.tcp_timestamps=1
# net.ipv4.tcp_tw_recycle=0
# net.ipv4.tcp_tw_reuse=1
# net.ipv4.tcp_max_tw_buckets=10000
# sysctl -p

    allow_reuse_address = True
    request_queue_size = 100

def launchHttpServer(serverArgs, ports):
    if len(ports) == 1:
        if hasattr(sys, 'getwindowsversion'):
            processes = serverArgs[11]
            for fockId in xrange(1, processes):
                from multiprocessing import Process
                Process(target=createHttpServer, name="cserver: %s" % fockId, args=serverArgs).start()
        createHttpServer(*serverArgs)
    else:
        for port in ports:
            sa = list(serverArgs)
            sa[1] = int(port)
            from threading import Thread
            Thread(target=createHttpServer, name="cserver: %s" % port, args=tuple(sa)).start()

def createHttpServer(host="", port=8089, timeout=None, isCpuPriority=False, webroot=".", mainpage=None, uploadFolder=".",
        servicePath="cservice", cserviceInfo=[], cserviceProxy=[], stubFiles=(), forkProcess=2, setProcessLog=False):
    # create handle
    rHandler = createRouterHandler(webroot, uploadFolder)
    CServerHandler.rHandler = rHandler

    # set service
    CServerHandler.timeout = timeout
    CServerHandler.webroot = os.path.abspath(webroot)
    CServerHandler.mainpage = ("/" + mainpage) if mainpage and mainpage != "" else None
    CServerHandler.uploadFolder = uploadFolder if os.path.exists(uploadFolder) else ""

    # create server
    s = ForkingHTTPServer((host, int(port)), CServerHandler) if isCpuPriority else\
        ThreadingHTTPServer((host, int(port)), CServerHandler)

    if not hasattr(sys, 'getwindowsversion') and forkProcess > 1:  # multi process to launch server
        for fockId in xrange(1, forkProcess):
            pid = eval("os.fork")()
            if pid:  # Parent process
                slog.info("Fork %s process id %s" % (fockId, pid))
                time.sleep(0.1)
            else:  # Child process
                if setProcessLog:
                    from libs.syslog import logManager
                    logManager.setProcessId(fockId)
                break  # break to start server

    # start server
    createCservice(servicePath, cserviceInfo, cserviceProxy, stubFiles, rHandler)
    s.serve_forever(poll_interval=0.5)

def createCservice(servicePath, cserviceInfo, cserviceProxy, stubFiles, rHandler):
    servicePath = servicePath.strip().lower()
    if servicePath == "":
        servicePath = "cservice"
    if rHandler.handlers.__contains__(servicePath):
        return

    from libs.refrect import DynamicLoader
    ignoreImportExcept = False
    DynamicLoader.getClassFromFile(None, ignoreImportExcept, *stubFiles)

    slog.info("Service: %s" % ", ".join([c[0].__name__ for c in cserviceInfo]))
    cservice = ObjHandler()
    cservice.loadClasses(cserviceInfo, rHandler)

    rHandler.addHandler(servicePath, cservice)
    for cserviceCls, handleUrl in cserviceProxy:
        rHandler.addHandler(handleUrl.lower(), cserviceCls(cservice.objs))

def createRouterHandler(webroot, uploadFolder):
    # file setting
    if True:
        rHandler = SessionRouterHandler(FileHandler())
    else:
        rHandler = RouterHandler(FileHandler())
    if os.path.exists(webroot):
        rHandler.addHandler("__file__", rHandler.defHandler)
        rHandler.addHandler("file", FolderHandler())
    if uploadFolder != "" and os.path.exists(uploadFolder):
        rHandler.addHandler("fileupload", FileUploadHandler())

    return rHandler

if __name__ == "__main__":
    createHttpServer()
