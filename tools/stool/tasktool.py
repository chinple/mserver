# -*- coding: utf8 -*-
from cserver import cprop
from libs.task import TaskMananger, FunctionTaskHandle
from server.cclient import curlCservice
from libs.parser import toJsonStr, toJsonObj
from libs.syslog import slog


class OnlineTaskClient(object):

    def __init__(self, taskcls=None):
        self.serverhost = cprop.getVal("task", "serverhost")
        self.serverpath = "TestPlanApi/proxyApi"
        self.serverauth = cprop.getVal("task", "serverauth")
        self.nodename = cprop.getVal("task", "nodename")
        self.nodehost = cprop.getVal("task", "nodehost")

        self._taskmgr = TaskMananger(True, groupInterval=60, poolSize=1)
        if taskcls is None: taskcls = SyncFunctionTaskHandle
        self.task = taskcls(self._syncTasks, self._callServer)
        try:
            self.task.rhandler = self.run
            slog.info("Using function run")
        except:pass
        self._taskmgr.addTaskGroup("online", self.task , 2, 2)
        
        self._taskmgr.saveTask('pullTask', span=300, fun=self._pullTasks)
        self._taskmgr.operateTask("pullTask")

    def _pullTasks(self):
        tasks = self._syncTasks()
        if tasks:
            tkeys = self.receiveSyncTask(tasks)
            oldtasks = self._taskmgr.taskGroups['online'].tasks
            for tkey in list(oldtasks.keys()):
                if not tkeys.__contains__(tkey):
                    self._taskmgr.operateTask(tkey, 'online', "delete")
            slog.info("Online tasks: %s" % ", ".join(tkeys))
            try:
                self.__reinitTasks__()
            except:pass

    def __reinitTasks__(self):
        pass

    def _syncTasks(self, task=None, isfinish=False, tret=None):
        if task is not None:
            slog.info(toJsonStr(task))
        if isfinish:
            subject, body = self.task.getTaskReport(task, tret)
        else:
            subject, body = None, None
        try:
            return self._callServer(aname="_syncTaskNode",
                task=task, subject=subject, body=body, tnode={'n':self.nodename, 'v':self.nodehost })
        except Exception as ex:
            slog.info("Fail to sync for %s: %s" % (ex, task))

    def _callServer(self, aname, **args):
        return curlCservice(self.serverhost, self.serverpath, isCheckResp=True, passwd=self.serverauth, aname=aname, **args)
    
    def receiveSyncTask(self, tasks):
        tkeys = []
        for task in tasks:
            if self.nodename == task['tnode']:
                try:
                    tkeys.append(self.task.addOnlineTask(self._taskmgr, task['taskid'], task['tkey'], task['targs'], task['ttype'], task['hour'], task['minute'], task['span'], task['maxCount'], task['runCount'], notifycond=task['notifycond'])['key'])
                except:
                    slog.warn("Drop task {taskid} {tkey}".format(**task))
            else:
                slog.warn("Node not match, drop task {tkey} {taskid}".format(**task))
        return tkeys

    def operateTask(self, tkey, optype, rargs=None):
        return self._taskmgr.operateTask(tkey, "online", optype, rargs)

    def getTasks(self, g='online'):
        return self._taskmgr.taskGroups[g].tasks
    
    def getTaskInfo(self, taskid=None, ttype=None, runCount=None, tkey=None, perfkey=None):
        return self.getTasks()[tkey]


class SyncFunctionTaskHandle(FunctionTaskHandle):

    def __init__(self, uhandler, callserver):
        FunctionTaskHandle.__init__(self, False, 0)
        self.uhandler = uhandler
        self.callserver = callserver
        self.rhandler = None

    def update(self, task, isfinish, tret):
        self.uhandler(task, isfinish, tret)
    
    def addOnlineTask(self, taskmgr, taskid, taskKey, targs, ttype, hour=-1, minute=0, span=-1, maxCount=-1, runCount=0, **taskprops):
        task = taskmgr.saveTask(taskKey, 'online', hour, minute, span, maxCount, runCount,
            ttype=ttype, targs=toJsonObj(targs), taskid=taskid)
        for p in taskprops.keys(): task[p] = taskprops[p]
        return task

    def getTaskReport(self, task, tret):
        subject, body = None, None
        return subject, body

    def run(self, task):
        if self.rhandler: return self.rhandler(task)
        if task['ttype'] == 'fun': return SyncFunctionTaskHandle.run(self, task)


if __name__ == "__main__":
    from cserver import cloudModule

    @cloudModule()
    class TaskclientApi(OnlineTaskClient):

        def run(self):
            slog.info("Run the task")

    from cserver import servering
    cprop.load("task.ini")
    servering(" -p 8085")
