'''

@author: chinple
'''
import time
from threading import Thread
from libs.syslog import slog
import traceback
from multiprocessing.pool import ThreadPool

class TaskDriver:
    def __init__(self, interval, taskHandler, driverName="driver", poolSize=100):
        self.tasks = {}
        self.taskPool = ThreadPool(poolSize)

        self.__setTaskDriver(interval, taskHandler)
        Thread(name=driverName, target=self.__startTimmer__).start()

    def __setTaskDriver(self, interval, taskHandler):
        interval = int(interval)
        if interval < 0.1:
            interval = 0.1
        self.interval = interval
        self.count = 0
        self.taskHandler = taskHandler

    def deleteTask(self, taskKey):
        if self.tasks.__contains__(taskKey):
            self.tasks.__delitem__(taskKey)

    def saveTask(self, taskKey, hour=0, minute=0, span=0, **taskArgs):
        if self.tasks.__contains__(taskKey):
            task = self.tasks[taskKey]
            task['hour'] = int(hour)
            task['minute'] = int(minute)
            task['span'] = int(span)
        else:
            task = {'key':taskKey,
                'hour':int(hour), 'minute':int(minute), 'span':int(span),
                'now':time.time(), 'time':0, 'status':'ready', 'pause':False}
            self.tasks[taskKey] = task
            self.taskHandler.prepare(task)

        for a in taskArgs:
            task[a] = taskArgs[a]

    def operateTask(self, taskKey, optype="run"):
        task = self.tasks[taskKey]
        if optype == "pause":
            task['pause'] = True
        else:
            task['pause'] = False
            self.__runTaskInPool__(time.time(), task)
        return task

    def __startTimmer__(self):
        while 1:
            self.count += 1
            Thread(name="time-task", target=self.__runAllTask__).start()
            time.sleep(self.interval)

    def __runAllTask__(self):
        now = time.localtime()
        secTime, hour, minute = time.time(), now.tm_hour, now.tm_min
        for sc in self.tasks:
            try:
                self.__runMatchSchedule__(secTime, hour, minute, self.tasks[sc])
            except:
                slog.error("Fail schedule: %s" % traceback.format_exc())

    def __runMatchSchedule__(self, secTime, nowHour, nowMin, task):
        if task['span'] > 0:
            if secTime - task['now'] >= task['span']:
                self.taskPool.apply_async(self.__runTaskInPool__, (secTime, task))
        if nowHour == task['hour'] and nowMin == task['minute']:
            self.taskPool.apply_async(self.__runTaskInPool__, (secTime, task))

    def __runTaskInPool__(self, secTime, task):
        def updateTask():
            try:
                self.taskHandler.update(task)
            except Exception as ex:
                slog.error(ex)

        if not task['pause'] and task['status'] != 'run' and task['status'] != 'wait':
            try:
                task['status'] = "wait"
                self.taskHandler.initRun(task)

                task['now'] = secTime
                task['status'] = 'run'
                updateTask()
                self.taskHandler.run(task)

                task['status'] = 'stop'
                task['time'] = time.time() - secTime
            finally:
                if task['status'] != 'stop':
                    task['status'] = 'exception'
                try:
                    self.taskHandler.endRun(task)
                    updateTask()
                except Exception as ex:
                    slog.error(ex)
            return 1
        return 0

class FunctionTaskHandle:
    def __init__(self, isTaskInProcess, poolSize):
        pool = None
        if isTaskInProcess:
            import multiprocessing
            pool = multiprocessing.Pool(processes=poolSize)
        self.pool = pool

    def update(self, task):
        pass

    def prepare(self, task):
        task['fun'] = None

    def initRun(self, task):
        pass

    def run(self, task):
        if self.pool is None:
            task['fun']()
        else:
            self.pool.apply(task['fun'])

    def endRun(self, task):
        pass

class TaskMananger:
    def __init__(self, initFunGroup=True, groupInterval=1, poolSize=10, isTaskInProcess=False):
        self.taskGroups = {}
        if initFunGroup:
            self.addTaskGroup("function", FunctionTaskHandle(isTaskInProcess, poolSize), groupInterval, poolSize)

    def hasTaskGroup(self, groupName):
        return self.taskGroups.__contains__(groupName)

    def addTaskGroup(self, groupName, taskHandler, interval=31, poolSize=100):
        if not self.hasTaskGroup(groupName):
            taskGroup = TaskDriver(interval, taskHandler, groupName, poolSize)
            self.taskGroups[groupName] = taskGroup

    def saveTask(self, taskKey, groupName="function", hour=-1, minute=0, span=-1, **taskArgs):
        taskGroup = self.taskGroups[groupName]
        task = taskGroup.saveTask(taskKey, hour, minute, span, **taskArgs)
        return task

    def deleteTask(self, taskKey , groupName="function"):
        taskGroup = self.taskGroups[groupName]
        return taskGroup.deleteTask(taskKey)

    def operateTask(self, taskKey, groupName="function", optype="run"):
        taskGroup = self.taskGroups[groupName]
        return taskGroup.operateTask(taskKey, optype)
