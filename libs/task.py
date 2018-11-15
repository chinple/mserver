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

    def resetTask(self, taskKey, hour, minute, span, maxCount, runCount, **taskArgs):
        if self.tasks.__contains__(taskKey):
            task = self.tasks[taskKey]
        else:
            task = {'key':taskKey, 'stime':time.time() - 60, 'rspan':0, 'status':'ready', 'runCount':int(runCount), 'pause':False}
            self.tasks[taskKey] = task
            self.taskHandler.prepare(task)

        task['hour'], task['minute'], task['span'], task['maxCount'] = \
            int(hour), int(minute), int(span), int(maxCount)
        if task['status'] == 'finish':task['status'] = 'ready'
        for a in taskArgs:
            task[a] = taskArgs[a]
        return task

    def changeTask(self, taskKey, optype="run"):
        if not self.tasks.__contains__(taskKey):
            raise Exception("task not exist")

        task = self.tasks[taskKey]
        if optype == 'delete':
            self.tasks.__delitem__(taskKey)
        elif optype == "pause":
            task['pause'] = True
        elif optype == 'run':
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
        curTime, hour, minute = time.time(), now.tm_hour, now.tm_min
        for sc in self.tasks:
            try:
                self.__runMatchSchedule__(curTime, hour, minute, self.tasks[sc])
            except:
                slog.error("Fail schedule: %s" % traceback.format_exc())

    def __runMatchSchedule__(self, curTime, nowHour, nowMin, task):
        if (task['maxCount'] > 0 and task['maxCount'] <= task['runCount']):
            task['status'] = 'finish'
        elif (task['span'] > 0 and curTime - task['stime'] >= task['span']) or \
            (nowHour == task['hour'] and nowMin == task['minute'] and curTime - task['stime'] > 60):
            self.taskPool.apply_async(self.__runTaskInPool__, (curTime, task))

    def __runTaskInPool__(self, curTime, task):
        task['runCount'] += 1

        def updateTask():
            try:
                self.taskHandler.update(task)
            except Exception as ex:
                slog.error(ex)

        if not task['pause'] and task['status'] != 'run' and task['status'] != 'wait':
            try:
                task['status'] = "wait"
                self.taskHandler.initRun(task)

                task['stime'] = curTime
                task['status'] = 'run'
                updateTask()
                self.taskHandler.run(task)
                task['status'] = 'stop'
            finally:
                task['rspan'] = time.time() - curTime
                if task['status'] != 'stop': task['status'] = 'exception'
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

    def prepare(self, task):  # one time
        task['fun'] = None

    def update(self, task):  # sync task status no exception
        pass

    def initRun(self, task):  # starting
        pass

    def run(self, task):  # running
        if self.pool is None:
            task['fun']()
        else:
            self.pool.apply(task['fun'])

    def endRun(self, task):  # ending
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

    def saveTask(self, taskKey, groupName="function", hour=-1, minute=0, span=-1, maxCount=-1, runCount=0, **taskArgs):
        taskGroup = self.taskGroups[groupName]
        task = taskGroup.resetTask(taskKey, hour, minute, span, maxCount, runCount, **taskArgs)
        return task

    def operateTask(self, taskKey, groupName="function", optype="run"):
        taskGroup = self.taskGroups[groupName]
        return taskGroup.changeTask(taskKey, optype)
