'''
Created on 2015-7-10

@author: chinple
'''
import sys
from server.cclient import curl
sys.path.insert(0, 'mtestPath')

from mtest import model, TestCaseBase, scenario

@model()
class TestClass1(TestCaseBase):
    @scenario(param={ "voucherType":[1, 2], "goodsType":[5000, 6000, 7000, 8000]}, where={"combine":['goodsType', 'voucherType'], 'strategy':'product1'})
    def testCombine(self, letter, number, other):
        pass

# @model()
class TestClass(TestCaseBase):

    @scenario(param={}, where={}, priority="P1", author="chinple")
    def testExample(self):
        self.tlog.step("curl request")
        resp = curl(url="http://www.qq.com", body=None, method="GET")
        self.tlog.info(resp)
        
        self.tlog.step("step to do ...")
        self.tassert.areEqual(1, 2, "check")
        
    @scenario(param={ "voucherType":[1, 2], "goodsType":[5000, 6000, 7000, 8000]}, where={"combine":['goodsType', 'voucherType'], 'strategy':'product1'})
    def testCombine(self, letter, number, other):
        self.tlog.step(self.param.getType("letter"))
    @scenario(param={'letter':['a', 'b', 'c'],
            'number':['1', '2', '3'], 'other':['x', 'y']},
       where={'strategy':'product',
        'group':[{'combine':['letter', 'number'], 'strategy':'product'},
        {'combine':['other']}]})
    def testWhere(self, letter, number, other):
        self.tlog.step(self.param.getType("letter"))

    @scenario(param={
            'letter':'a', "number":1, 'other':'ok'
        },
       where={'combine':['letter', 'number'], 'strategy':'product'},
        group=[{
            "param":{ 'letter':['a', 'b', 'c'],
                      'number':['1', '2', '3']   
            }
        }, {
            "param":{ 'other':['x', 'y'], "test":1
            },
            'combine':['other'], 'strategy':'product'
        }])
    def testParamGroup(self, letter, number, other):
        self.tlog.step(self.param.getType("letter"))

if __name__ == "__main__":
    from mtest import testing
    testing("-r param ")
