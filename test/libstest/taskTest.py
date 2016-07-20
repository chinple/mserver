'''
Created on 2015-7-10

@author: chinple
'''
from mtest import model, TestCaseBase, scenario, testing
import time
from libs.task import TaskMananger
from libs.syslog import slog
def funHandleSample():
    slog.info("Running: %s" % time.time())
    time.sleep(2)
    slog.info("Run over: %s\n" % time.time())

@model()
class LibTest(TestCaseBase):

    @scenario()
    def testtask(self):
        t = TaskMananger(isTaskInProcess=True)
        t.saveTask("run-test", span=1, fun=funHandleSample)

if __name__ == "__main__":
    testing("-r debug")
