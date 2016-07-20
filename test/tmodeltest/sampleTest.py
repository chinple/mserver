'''
Created on 2015-7-10

@author: chinple
'''

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
    s = SampleTestCase()
    print(eval(s.__class__.__name__)().sampleFun())
    print(s.__class__().sampleFun())
#     from mtest import testing
#     testing("-r param ")
