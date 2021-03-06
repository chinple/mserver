'''

@author: chinple
'''
import time
from cperf import stressScenario, running, apiStatisticHandler
from mtest import adapter
from server.cclient import curl


@adapter(adapterHandler=apiStatisticHandler)
class Api(object):

    def getCservice(self):
        curl("localhost:8089/cservice")

    def getFile(self):
        curl("localhost:8089/file")


api = Api()


@stressScenario(startThreads=2044, maxThreads=10000, expTps=100000)
def SampleTest(thid, degree):

#     curl("http://127.0.0.1:8081/cservice/ServerApi/sleepSeconds?t=3600")
#     curl("127.0.0.1:8089/cservice")
#     curl("http://imgcache.qq.com/open_proj/proj_qcloud_v2/qcloud_2015/css/img/global/qcloud-logo.png")
    if degree==0: print thid
    time.sleep(.1)
#     if degree/3 == 0: raise Exception("Fail Test")


if __name__ == '__main__':
    running("-r run --maxTime 100")
