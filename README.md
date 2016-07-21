# 样例
  参考test目录

# 功能
1. 测试驱动开发：单元测试、基于模型测试
2. 简易高并发的http服务框架：window下多进程监听同一端口，linux下fork出多进程提高并发

# 编码约定
1. 类名：TestCaseBase
2. 函数名：setup、beginTestCase
3. 变量名：caseInfo
4. 保护变量前加 _ ，私有变量前加 __

# 服务
<pre>
   python2.7 -u mtest/run.py server -t test/servertest/serverTest.py -p 8088 -f /data/test/builds/ --uploadFolder /data/test/builds/uploads

serverTest.py:

<code>

from cserver import cloudModule, servering, cserviceProxy
import time
from server.chandle import CserviceProxyBase

@cserviceProxy(handleUrl="/api")
class ApiService(CserviceProxyBase):
    pass

@cloudModule()
class SampleServerApi:
    def emptyCall(self):
        return "emptyCall"
    def callWithArgs(self, callId, method="post"):
        return "callId: %s" % callId
    def sleepSeconds(self, t):
        t = int(t)
        if t > 0:
            time.sleep(t)
        return "Sleep: %s" % t

if __name__ == "__main__":
    servering(" -p 8081 --processes 1")
</code>
列出api：
    curl localhost:8081/cservice/SampleServerApi/ 或者 curl localhost:8081/api/SampleServerApi/
SampleServerApi/
        callWithArgs(callId, method)
        sleepSeconds(t)
        emptyCall()

调用api：
curl localhost:8081/api/SampleServerApi/emptyCall?
[0, "emptyCall"]

curl localhost:8081/api/SampleServerApi/callWithArgs -d "{\"callId\":1}"
[0, "callId: 1"]

数组第一个值，返回码，0表示成功；数组第二个值，调用函数的返回值
</pre>

# 测试
<pre>
  python2.7 -u mtest/run.py test -t test/tmodeltest/sampleTest.py

sampleTest.py:
<code>

from mtest import model, TestCaseBase, scenario

@model()
class SampleTestCase(TestCaseBase):
    @scenario(param={'letter':['a', 'b', 'c'],
            'number':['1', '2', '3'], 'other':['x', 'y']},
        where={'combine':"letter,number,other".split(",")})
    def sampleTest(self, letter, number, other):
        pass
    @scenario()
    def sampleFun(self):
        self.tlog.info("called")
        return "OK"

if __name__ == "__main__":
    from mtest import testing
    testing("-r run ")
<code>
</pre>