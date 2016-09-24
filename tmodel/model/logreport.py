'''
Created on 2013-1-24

@author: chinple
'''
import time
from tmodel.model.logxml import TestLogger
from libs.objop import ObjOperation
from libs.timmer import TimmerOperation

class HtmlTestReport(TestLogger):
    def __init__(self, logFilePath="testreport.html", isXmlLog=False, isAppend=False):
        TestLogger.__init__(self, logFilePath, isXmlLog, isAppend)
        self.testCaseInfo = ""
        self.lastStep = ""
        self.stepInfo = ""
        self.caseCount = 0
        self.failCount = 0
        self.logFilePath = ""
        self.curModuleName = ""
        self.curModuleIndex = 0
        self.hasStep = False
        self.startTime = time.time()

    def getLog(self, logf, * args):
        return logf % args

    def outputContent(self, log):
        TestLogger.infoText(self, log)

    def beginTestCase(self, testModule, testName, testInfo, testParam, searchKey):
        if self.curModuleName != testModule:
            self.curModuleIndex += 1
            self.curModuleName = testModule
            # Write module info
            self.outputContent(self.getLog(
                    "  <tr onDblClick=\"showSubTestCase('%s')\">\n    <td class='body' colspan='5'><strong>%s</strong></td>\n  </tr>",
                    self.curModuleIndex, testModule))

        self.caseCount += 1
        # Judge test type
        testType = ObjOperation.tryGetVal(searchKey, "TestType", "Auto")
        if testType == "":
            testType = "Auto"
        elif "manual" == testType:
            testType = "Manual"

        # set test case info
        self.testCaseInfo = self.getLog(("  <tr id=rowcolor%s module=%s>" % (1 if self.caseCount % 2 == 0 else 2, self.curModuleIndex)) + 
            "\n    <td id={result} name={result} ondblclick='filterStep(" + str(self.caseCount) + 
            ")'>%s</td><td class=body>%s</td><td class=body>%s</td><td class=body>%s</td><td class=body>%s</td><td class=body>%s",
            testName, ObjOperation.tryGetVal(searchKey, "Author", ""), ObjOperation.tryGetVal(searchKey, "Priority", ""),
            testType, testParam, testInfo)

        # set step info
        self.stepInfo = ""
        self.lastStep = "<table  id='stepTable' name='stepTable' width='95%%' align='right' style='display:none'>"
        self.hasStep = False

    def endTestCase(self, caseName, result, rescode, executetime):
        if self.testCaseInfo.__contains__("failTestCase"):
            self.failCount += 1
        self.outputContent(self.testCaseInfo.replace("{result}", "passTestCase"))

        self.outputContent(self.stepInfo)
        self.outputContent(self.lastStep.replace("{result}", "pass"))
        self.outputContent("</td></tr>\n</table>" if self.hasStep else "</table>")

        self.outputContent("    </td></tr>")

    def step(self, log):
        self.hasStep = True

        # out put passed steps
        self.stepInfo += self.lastStep.replace("{result}", "pass") + "</td></tr>"
        # set current steps
        self.lastStep = self.getLog("<tr>\n <td class='{result}'>[Step] %s", log)

    def input(self, log):
        pass

    def validate(self, log):
        pass

    def info(self, log):
        pass

    def success(self, log):
        self.lastStep += "<pre class=pass>&nbsp;&nbsp;&nbsp;&nbsp;[Assert] %s</pre>" % log

    def warn(self, log):
        pass

    def error(self, log):
        self.testCaseInfo = self.testCaseInfo.replace("{result}", "failTestCase")
        if not self.hasStep:
            self.step("Default empty step")

        self.lastStep = self.lastStep.replace("{result}", "fail") + "<br>" + log.replace("\n", "<br>")

    def infoText(self, formator, *args):
        pass

    def warnText(self, formator, *args):
        pass

    def init(self, logFilePath, isXmlLog=False, xsl="", lineEnd="\r\n", isAppend=False):
        if logFilePath == self.getloggerpath() or logFilePath == None or logFilePath == "" or not logFilePath.endswith(".html"):
            return
        TestLogger.init(self, logFilePath, isXmlLog, xsl, lineEnd, isAppend)
        self.outputContent('''<html>
<head>
<title>mtest report</title>
</head>
<style type='text/css'>
<!--
body { background-color: white; font-family:verdana, arial, helvetica, geneva; font-size: 16px; font-style: italic; color: black; }
.title { font-family: verdana, arial, helvetica,geneva; font-size: 12px; font-weight:bold; color: white; }
.body { font-family: verdana, arial, helvetica, geneva; font-size: 12px; font-weight:plain; color: black; }
.pass { font-family: verdana, arial, helvetica, geneva; font-size: 12px; font-weight:plain; color: black; background-color: lightgreen; }
.fail { font-family: verdana, arial, helvetica, geneva; font-size: 12px; font-weight:plain; color: black; background-color: #FF0000; }
#passTestCase { font-family: verdana, arial, helvetica, geneva; font-size: 12px; font-weight:plain; color: black; }
#failTestCase { font-family: verdana, arial, helvetica, geneva; font-size: 12px; font-weight:plain; color: black; background-color: #FF0000; }
#tableheader { background-color: #FF6633; }
#rowcolor1 { background-color: #eeeeee; }
#rowcolor2 { background-color: white; }
-->
</style>
<script language="javascript">
HtmlTag ={
    'GetObjs': function(objName){
        var nameObj = document.getElementsByName(objName)
        if(nameObj.length==0){
            var obj = document.getElementById(objName)
            return obj==null ?[]:[obj] 
        }
        return nameObj
    },
    'SetDisplay': function(objName, isHiddon, parentCount){
        if(parentCount==undefined){
            parentCount = 0
        }
        var objs = HtmlTag.GetObjs(objName)
        for(var objIndex = 0; objIndex< objs.length; objIndex++){
            var obj = objs[objIndex]
            for(var pIndex =0; pIndex < parentCount; pIndex ++)
                if(obj.parentNode!=undefined)
                    obj = obj.parentNode
                else
                    break
            obj.style.display = isHiddon?'none':''
        }
    }
}
function filterResult(isHiddonPass, isHiddonFail){
    HtmlTag.SetDisplay('passTestCase',isHiddonPass,1)
    HtmlTag.SetDisplay('failTestCase',isHiddonFail,1)
}
function filterStep(objIndex){
    try{
        var obj = HtmlTag.GetObjs('stepTable')[objIndex-1]
        if(obj.style.display != 'none')
            obj.style.display = "none"
        else
            obj.style.display =""
    }catch(e){}
}
function showSubTestCase(refModuleIndex,isShowAll,isShowManual){
    testResTRs = testresultTable.children[0].children
    isFirstModule = true
    displayValue = ""
    for(trIndex=1; trIndex< testResTRs.length; trIndex++){
        testResTR = testResTRs[trIndex]
        var moduleIndex = testResTR.getAttribute("module")
        if(isShowManual!=undefined){
            try{
                isManualTR = testResTR.children[3].innerHTML.indexOf("Manual") >= 0
                testResTR.style.display = (isShowManual==isManualTR)?"":"none"
            }catch(e){
                // always show class TR for this TR just have one td
            }
        }else if(isShowAll!=undefined){
            if(moduleIndex != undefined){
                testResTR.style.display = isShowAll?"":"none"
            }
        }else if(moduleIndex==refModuleIndex){
            if(isFirstModule){
                isFirstModule = false
                displayValue = testResTR.style.display !="none"?"none":""
            }
            testResTR.style.display = displayValue
        }
    }
}
</script>
<body>
<div class=body>Show:
  <input type="radio" name="showType" onClick="filterResult(false,false)" value="1"/>All
  <input type="radio" name="showType" onClick="filterResult(false,true)"/>Passed
  <input type="radio" name="showType" onClick="filterResult(true,false)"/>Failed Cases,
  <input type="checkbox" onClick="HtmlTag.SetDisplay('stepTable', !this.checked)"/>Steps; 
  <input type="checkbox" onClick="HtmlTag.SetDisplay('configTable', !this.checked)"/>Configs
<br>Hiddon:
  <input type="checkbox" onClick="showSubTestCase(0, !this.checked)"/>Scenarios(or Module),
  <input type="checkbox" onClick="showSubTestCase(0, null, !this.checked)"/>Manual Cases</div>
<table border='0' width='100%' id="testresultTable">
  <tr id=tableheader>
    <th align='left' width='200'>Test Case Name </th>
    <th width='100'>Tester</th>
    <th width='50'>Pri</th>
    <th width='50'>Type</th>
    <th>Parameter</th>
    <th>Description</th>
  </tr>''')

    def Close(self):
        self.outputContent(self.getLog(
                "<hr size=2 color='#000000'/><pre class=body>Total    %s:\n    Passed: %s + Failed: %s</pre>",
                self.caseCount, (self.caseCount - self.failCount), self.failCount))

        nowTime = time.time()
        self.outputContent(self.getLog(
                "<pre class=body>Run between %s %s~%s(%s min)<pre class=body>",
                TimmerOperation.getFormatTime(self.startTime, "%Y-%m-%d"),
                TimmerOperation.getFormatTime(self.startTime, "%H:%M"),
                TimmerOperation.getFormatTime(nowTime, "%H:%M"),
                int((nowTime - self.startTime) / 6) / 10.0))
        self.outputContent("</table>")

#        self.outputContent(self.getLog(
#                "<table class=body id=\"configTable\" style=\"display:none\"><tr><td colspan=2  align=center>Configurations</td></tr>%s</table>",
#                tprop.ToFormatString(lambda * tv:"<tr><td>%s</td><td>%s</td></tr>" % tv, "\n")))

        self.outputContent("\n</body>\n</html>")
