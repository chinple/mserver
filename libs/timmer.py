'''
Created on 2010-11-8

@author: chinple
'''
import time
import datetime

class TimmerOperation:
    @staticmethod
    def getFormatTime(secTime, timeFormat="%Y-%m-%d %H:%M:%S"):
        return time.strftime(timeFormat, time.localtime(secTime))

    @staticmethod
    def getIntTime(timeStr, refTime=0, timeFormat="%Y-%m-%d %H:%M:%S"):
        if isinstance(timeStr, datetime.datetime):
            timeStr = str(timeStr)
        return time.mktime(time.strptime(timeStr, timeFormat)) - refTime

    @staticmethod
    def waitConditionIsTrue(sleepTimeSpan, maxSleepTimeSpan, condition):
        sleepTime = 0
        while sleepTime < maxSleepTimeSpan:
            if condition(sleepTime):
                return True
            else:
                sleepTime += sleepTimeSpan
                time.sleep(sleepTimeSpan)
        return False

class TimmerJson:
    def __init__(self):
        self.tj = {}

    def getKey(self, k):
        try:
            v = self.tj[k]
        except:return
        if time.time() - v['t'] >= v['m']:
            self.tj.__delitem__(k)
        else:
            return v['v']

    def addKey(self, k, v, maxTime=3600):
        self.tj[k] = {'t':time.time(), 'v':v, 'm':maxTime}
