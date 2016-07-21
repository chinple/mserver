'''
Created on 2015-7-10

@author: chinple
'''

from mtest import model, TestCaseBase, scenario
from server.claunch import QueueRequestWorker
import time
from libs.syslog import slog

def handleRequest(name, t):
    slog.info("%s sleep %s" % (name, t))
    if t > 0:
        time.sleep(t)

@model()
class QueTestCase(TestCaseBase):
    @scenario()
    def queTest(self):
        qw = QueueRequestWorker(handleRequest, 2)
        for i in xrange(10):
            qw.putRequest(("request", 0))
            time.sleep(0.1)
            print(i, "hold: %s, active: %s, queue: %s" % qw.getStatus())

        for i in xrange(10):
            qw.putRequest(("request", 3600))
            time.sleep(0.1)
            print(i, "hold: %s, active: %s, queue: %s" % qw.getStatus())
        time.sleep(1)
        print("hold: %s, active: %s, queue: %s" % qw.getStatus())

if __name__ == "__main__":
    from mtest import testing
    testing("-r debug ")
