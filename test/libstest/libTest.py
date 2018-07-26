'''
Created on 2015-7-10

@author: chinple
'''
from mtest import model, TestCaseBase, scenario, testing
from libs.parser import JsonParser
from libs.tvg import TValueGroup
from libs.objop import ObjOperation
from tmodel.model.paramgen import CombineGroupParam

@model()
class LibTest(TestCaseBase):

    @scenario()
    def testlog(self):
        self.tlog.step("This is ok")
    def output(self, *args):
        print(args)

    @scenario(param={"eventId": 6418609, "componentName": "cvm_mc", "version": 1, "user": "auto", "timestamp": 1442306584260, "interface": {"interfaceName": "qcloud.Qcvm.getCvmList", "para": {"endNum": 19, "projectId": 0, "regionId": "1", "startNum": 0, "allType": 1, "uin": "1002000590", "orderField": "addTimeStamp", "appId": 251000723, "order": 1}}})
    def testObjOp(self):
        ObjOperation.traversalObj(self.param.__prop__, self.output)
        print(ObjOperation.jsonFormat("{eventId}", self.param.__prop__))

    @scenario()
    def testtvg(self):
        self.tlog.info(JsonParser().toStr({'a':TValueGroup({'b':1})}))

    def checkParams(self, gp, expNum):
        i = 0
        while True:
            p = gp.nextParam()
            if p == None:
                break
            i += 1
            print(p)
        self.tassert.areEqual(expNum, i, "number")
    @scenario()
    def paramGenGroup2(self):
        gp = CombineGroupParam({
        }, {'strategy':'product'},
        
        [{'param':{
            "regionId":[1, 4, 5, 6],
            "cpu":1,
            'mem':[1, 2, 4, 8, 12],
            },
           'combine':["regionId", "mem"],
        }, {'param':{
            "regionId":[1, 4, 5, 6],
            "cpu":2,
            'mem':[ 2, 4, 8, 12, 16],
            },
           'combine':["regionId", "mem"],
        }, {'param':{
            "regionId":[1, 4, 5, 6],
            "cpu":4,
            'mem':[ 4, 8, 12, 16, 24],
            },
           'combine':["regionId", "mem"],
        }, {'param':{
            "regionId":[1, 4, 5, 6],
            "cpu":8,
            'mem':[8, 12, 16, 24, 32],
            },
           'combine':["regionId", "mem"],
        }, {'param':{
            "regionId":[1, 4, 5, 6],
            "cpu":12,
            'mem':[12, 16, 24, 32, 60],
            },
           'combine':["regionId", "mem"],
        }, {'param':{
            "regionId":[1, 4, 5, 6],
            'storage':[0, 100, 300, 500]
            },
           'combine':["regionId", "storage"],
        }])
        self.checkParams(gp, 111)

    @scenario()
    def paramGenGroup(self):
        gp = CombineGroupParam({
            'letter':'a', "number":1, 'other':'ok'
        }, {'strategy':'product'},
        
        [{
            "param":{ 'letter':['a', 'b', 'c'],
                      'number':['1', '2', '3'],
                      'specParam':1  
            },
          'combine':['letter', 'number']
        }, {
            "param":[{'other':'x', 'o':1}, {'other':'y', 'o':1}],
            'combine':['other'],
            'strategy':'datalist'
        }])
        self.checkParams(gp, 10)

    @scenario()
    def paramGenProduct(self):
        param = {'letter':['a', 'b', 'c'],
            'number':['1', '2', '3'], 'other':['x', 'y']}
        gp = CombineGroupParam(param, {'combine':['letter', 'number', 'other'], 'strategy':'product'}, None)
        self.checkParams(gp, 18)
        param = {'letter':['a', 'b', 'c'],
            'number':['1', '2', '3'], 'other':['x', 'y']}
        gp = CombineGroupParam(param, {'combine':['letter', 'number', 'other'], 'strategy':'add'}, None)
        self.checkParams(gp, 6)

    @scenario()
    def paramGenWhere(self):
        param = {'letter':['a', 'b', 'c'],
            'number':['1', '2', '3'], 'other':['x', 'y']}

        gp = CombineGroupParam(param, {'strategy':'product',
            'group':[{'combine':['letter', 'number'],'strategy':'product'}, 
                     {'combine':['other']}]}, None)
        self.checkParams(gp, 18)
        
        gp = CombineGroupParam(param, {'strategy':'product',
            'group':[{'combine':['letter', 'number'],'strategy':'add'}, 
                     {'combine':['other']}]}, None)
        self.checkParams(gp, 10)
    

if __name__ == "__main__":
    testing('-r debug -i ""')
