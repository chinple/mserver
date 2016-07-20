'''
Created on 2013-3-13

@author: chinple
'''
from mtest import model, scenario, TestModelBase, step, testing

@model()
class StatusModelingSample(TestModelBase):

    def __GetArgList__(self, sFrom, sTo):
        if sFrom == "B":
            return ["Arg1", "Arg2"]
        if sFrom == "C":
            return ["Arg3", "Arg4"]

    @step('S', 'A')
    def StartToA(self):
        pass

    @step('A', 'B')
    def AToB(self):
        pass

    @step('B', 'C')
    def BToC(self):
        pass

    @step('B', 'D')
    def BToD(self):
        pass

    @step('C,D', 'E')
    def CDToE(self):
        pass

    @step('D', 'A', 0)
    def DToA(self):
        pass

    @step('C', 'A')
    def CToA(self):
        pass

    @scenario(param={
        'username':'username@a.com',
        'password':'password'
        }, status={"start":"B", "coverage":"condition"})
    def StatusModelingSampleAnotherScenario(self):
        pass

    @scenario(param={
        'username':'username@a.com',
        'password':'password'
        }, status={"start":"S", "coverage":"condition"})
    def StatusModelingSampleScenario(self):
        pass

if __name__ == '__main__':
    testing("-r mview")

