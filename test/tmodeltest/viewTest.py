'''
Created on 2015-7-10

@author: chinple
'''
from mtest import adapter, model, TestCaseBase, scenario, testing

@adapter()
class TestAdapter(object):
    def callOK(self, a, b="default"):
        print("call ....")
        return("input args", a, b)
    def printFun(self, i, j):
        print(i)

@model()
class ViewModelTest(TestCaseBase):

    @scenario(param={"letter":['a','b','c']}, where={'combine':['letter']})
    def modelView(self):
        adapter = TestAdapter()
        ret = adapter.callOK(123)
        adapter.printFun(ret[1], ret)
        self.tassert.areEqual(1, ret[2], "Check info")

if __name__ == "__main__":
    testing("-r mtest")


