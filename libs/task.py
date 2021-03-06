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
        self.taskHandler = taskHandler

    def resetTask(self, taskKey, hour, minute, span, maxCount, runCount, **taskArgs):
        if self.tasks.__contains__(taskKey):
            task = self.tasks[taskKey]
        else:
            task = {'key':taskKey, 'stime':time.time() - 60, 'rspan':0, 'status':'ready', 'result':9, 'runCount':int(runCount), 'fcount':0, 'ftime':0, 'pause':False, 'rargs':None}
            self.tasks[taskKey] = task
            self.taskHandler.prepare(task)
        for a in taskArgs:
            if not ['stime', 'status', 'runCount'].__contains__(a): task[a] = taskArgs[a]
        task['hour'], task['minute'], task['span'], task['maxCount'] = int(hour), int(minute), int(span), int(maxCount)
        return task

    def changeTask(self, taskKey, optype, rargs):
        if not self.tasks.__contains__(taskKey):
            raise Exception("task not exist")

        task = self.tasks[taskKey]

        if optype == 'delete':
            self.tasks.__delitem__(taskKey)
        elif optype == "pause":
            task['pause'] = True
        elif optype == 'asyncrun':
            task['pause'] = False
            self.taskPool.apply_async(self.__runTaskInPool__, (time.time(), task, 60, rargs))
        elif optype == 'run':
            task['pause'] = False
            self.__runTaskInPool__(time.time(), task, 10, rargs)
        return task

    def __startTimmer__(self):
        tp = ThreadPool(3)
        while 1:
            try:
                tp.apply_async(self.__runAllTask__)
                time.sleep(self.interval)
            except Exception as ex:
                slog.error("Main thread: %s" % ex)

    def __runAllTask__(self):
        now = time.localtime()
        curTime, hour, minute = time.time(), now.tm_hour, now.tm_min
        for sc in self.tasks:
            try:
                self.__runMatchSchedule__(curTime, hour, minute, self.tasks[sc])
            except:
                slog.error("Fail schedule: %s" % traceback.format_exc())

    def __runMatchSchedule__(self, curTime, nowHour, nowMin, task):
        if task['status'] == 'run': return
        if (task['maxCount'] >= 0 and task['maxCount'] <= task['runCount']):
            task['status'] = 'finish'
        else:
            nspan = curTime - task['stime']
            mspan = task['span']
            if mspan > 0 and nspan > mspan:
                self.taskPool.apply_async(self.__runTaskInPool__, (curTime, task, mspan))
            elif nspan > 60 and nowHour == task['hour'] and nowMin == task['minute']:
                self.taskPool.apply_async(self.__runTaskInPool__, (curTime, task, 60))
            else:
                task['status'] = 'wait %s' % curTime

    def __runTaskInPool__(self, curTime, task, mspan, rargs=None):

        def updateTask(isfinish=False, tret=None):
            try:
                self.taskHandler.update(task, isfinish, tret)
            except Exception as ex:
                slog.error("updateTask: %s" % ex)

        task['stime'], ltime = curTime, task['stime']
        if curTime - ltime < mspan:return  # check duplicate run

        if task['status'] != 'run':
            task['status'] = 'run'; task['stime'], task['runCount'] = curTime, task['runCount'] + 1
            try:
                task['rargs'] = rargs
                tret = None
                self.taskHandler.initRun(task)
                try:  # configured for each task
                    time.sleep(task['targs']['delay'])
                except:pass

                updateTask()
                tret = self.taskHandler.run(task)
                task['status'] = 'finish' if (task['maxCount'] >= 0 and task['maxCount'] <= task['runCount']) else 'wait'
            finally:
                if task['result'] > 0: task['fcount'] += 1
                else: task['fcount'] = 0

                task['rspan'] = time.time() - curTime
                if task['status'] == 'run':task['status'] = 'exception'
                try:
                    self.taskHandler.endRun(task)
                    updateTask(True, tret)
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

    def update(self, task, isfinish=True, tret=None):  # sync task status no exception
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

    def operateTask(self, taskKey, groupName="function", optype="run", rargs=None):
        taskGroup = self.taskGroups[groupName]
        return taskGroup.changeTask(taskKey, optype, rargs)
