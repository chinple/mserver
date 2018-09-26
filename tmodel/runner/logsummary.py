'''
Created on 2016-10-8

@author: chinple
'''
from tmodel.model.casemodel import MTConst
import time
from libs.objop import ObjOperation
from libs.syslog import slog
import base64
import os


class LogAnalyzer:

    def __init__(self):
        self.runInfo = {0: 7, 1: 0, 2: 0, 3: 0, 'num': 7, 'startTime': 1475911195.424, 'endTime':time.time(), 'time': 0.0}
        self.htmlReportTemplate = '''
<table border="2" cellspacing="0">
  <tr>
    <td colspan="2" align="center" bgcolor="{color}">{product} Test Report({span})</td>
  </tr>
  <tr>
    <td width="80" bgcolor="#CCCCCC"> Version</td>
    <td>{version}</td>
  </tr>
  <tr>
    <td bgcolor="#CCCCCC"> Environment</td>
    <td>{env}</td>
  </tr>
  <tr>
    <td bgcolor="#CCCCCC"> Result</td>
    <td>run {inScope} = {passed}({passPercent}%) passed + {failed}({failPercent}%) failed, {actTime} min</td>
  </tr>
  <tr>
    <td bgcolor="#CCCCCC">Logs</td>
    <td>{logs}</td>
  </tr>
  <tr>
    <td colspan="2" bgcolor="{color}">Test Summary: </td>
  </tr>
  <tr>
    <td colspan="2"><pre>{summary}</pre></td>
  </tr>
</table>'''
        self.subjectTemplate = '{product} Test Report({passPercent}%: {passed} passed, {failed} failed; {actTime} min: {span})'

    def uploadTestlogs(self, logServer, logfiles):
        self.loglinks = []
        if logServer != "":
            for logfile in logfiles:
                if os.path.exists(logfile):
                    filename = time.strftime("test-%Y%m%d-%H%M%S") + logfile
                    upcmd = 'curl "http://%s/fileupload/?filename=%s&folder=testlog" -F "upload=@%s"' % (logServer, filename, logfile)
                    slog.info(upcmd)
                    os.system(upcmd)
                    self.loglinks.append('<a href="http://%s/testlog/%s">%s</a>' % (logServer, filename, logfile))

    def __makeTestSummary(self, totalNum, totalTime, passedNum, failedNum, notRunNum, cases):
        simpleSum = '\r\nTotal %s, %sm:\r\n\tPassed: %s + Failed: %s + NotRun: %s' % (totalNum, totalTime, passedNum, failedNum, notRunNum)
        leftRes = totalNum - passedNum - failedNum - notRunNum
        if leftRes > 0:
            simpleSum += ' + Block: %s' % leftRes

        listCases = lambda code:"\n\t".join(tuple([("%s\t%s" % (c, cases[code][c])) for c in cases[code].keys()]))
        summary = "Failed:\n\t%s\nPassed:\n\t%s" % (listCases(MTConst.failed), listCases(MTConst.passed))

        return simpleSum, summary

    def makeHtmlSummary(self, product, version, environment, runInfo):

        actTime = int((runInfo['endTime'] - runInfo['startTime']) / 60 + 0.5)
        totalTime = int(actTime / 60 + 0.5)
        totalNum, passedNum, failedNum = runInfo['num'], runInfo[MTConst.passed] + runInfo[MTConst.warned], runInfo[MTConst.failed]
        inScope = passedNum + failedNum
        notRunNum = totalNum - inScope

        passPercent = int(0 if passedNum <= 0 else passedNum * 1000.0 / inScope) / 10.0
        failPercent = (1000 - passPercent * 10) / 10

        timeSpan = "%s~%s" % (time.strftime("%Y-%m-%d %H:%M", time.localtime(runInfo['startTime'])),
            time.strftime("%H:%M"))
        bgcolor = ('green' if passPercent == 100 else ('yellow' if passPercent >= 80 else 'red'))

        simpleSum, summary = self.__makeTestSummary(totalNum, totalTime, passedNum, failedNum, notRunNum, runInfo['cases'])

        historyResGraph, logAttachLink = "", " &nbsp;".join(self.loglinks)
    
        subject = self.subjectTemplate.format(product=product, version=version, env=environment,
            passed=passedNum, failed=failedNum, passPercent=passPercent, failPercent=failPercent,
            inScope=inScope, notRun=notRunNum, total=totalNum, time=totalTime, actTime=actTime, span=timeSpan)

        htmlContent = self.htmlReportTemplate.format(product=product, version=version, env=environment,
            passed=passedNum, failed=failedNum, passPercent=passPercent, failPercent=failPercent,
            inScope=inScope, notRun=notRunNum, total=totalNum, time=totalTime, actTime=actTime, span=timeSpan,
            subject=subject, color=bgcolor, logs=logAttachLink, stability=historyResGraph, simpleSum=simpleSum, summary=summary)

        return subject, htmlContent

    def __addCase(self, caseName, resCode, resTime):
        self.caseResult[resCode][caseName] = resTime

#     def parseLogFile(self, logFile):
# 
#         xmlCaseNameReg = '.*<TestCase casename="([^ |^\t]+ ).*" param='
#         caseNameReg = "<TestCase>  \[casename\] ([^ |^\t]+ ).*"
# 
#         xmlCaseResReg = '\t\t<Result casename="([^ |^\t]+)" *rescode="([0-9]+)" *result="([A-Z|a-z]+)" *time="([0-9|.]+)"/>'
#         caseResReg = "  <Result>.*\[casename\] ([^ |^\t]+) \[rescode\] ([0-9]+).*\[result\] ([A-Z|a-z]+).*"
# 
#         isXmlLog = None
#         caseName = ""
#         with open(logFile) as fh:
#             while True:
#                 curStr = fh.readline()
#                 if curStr == "":
#                     break
#                 elif caseName == "":
#                     if isXmlLog or isXmlLog is None:
#                         caseMatch = re.match(xmlCaseNameReg, curStr)
#                     if not isXmlLog or isXmlLog is None:
#                         caseMatch = re.match(caseNameReg, curStr)
# 
#                     if caseMatch is not None:
#                         caseName = caseMatch.groups()[0]
#                 else:
#                     resMatch = re.match(xmlCaseResReg if isXmlLog else caseResReg, curStr)
#                     if resMatch != None:
#                         resGroup = resMatch.groups()
#                         resCode = int(resGroup[1])
#                         try:
#                             resTime = float(resGroup[3])
#                         except:
#                             resTime = 0
#                             timeMatch = re.match('.*\[time\] ([0-9|.]+) .*', curStr)
#                             if timeMatch != None:
#                                 resTime = float(timeMatch.groups()[0])
# 
#                         self.__addCase(caseName, resCode, resTime)
#                         caseName = ""


class SummaryReport:

    def __init__(self):
        self.la = LogAnalyzer()

    def setReport(self, product, version, environment, runInfo, logServer, logfiles):
        self.la.uploadTestlogs(logServer, logfiles)
        subject, htmlContent = self.la.makeHtmlSummary(product, version, environment, runInfo)
        self.subject = subject
        self.htmlContent = htmlContent

    def __makeEmail(self, sender, receiver, subject, htmlBody):
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        mimeMail = MIMEMultipart()
        mimeMail.add_header("Date", time.strftime("%A, %d %B %Y %H:%M"))
        mimeMail.add_header("From", sender)
        mimeMail.add_header("To", ("%s;" * len(receiver)) % tuple(receiver))
        mimeMail.add_header("Subject", subject)
        mimeMail.attach(MIMEText(_text=htmlBody.encode("utf8"), _subtype="html", _charset="utf8"))
        return mimeMail

    def sendEmail(self, emailProxy, smtpAddr, smtpLogin, sender, receiver):
        if emailProxy == "" and smtpAddr == "":return

        try:
            if receiver == "":
                raise Exception("No receiver")
            receiver = receiver.split(";")
            mimeMail = self.__makeEmail(sender, receiver, self.subject, self.htmlContent)
            if emailProxy.strip() != "":
                from server.cclient import curl
                from libs.parser import toJsonStr
                slog.info("Sending report: %s -> %s" % (emailProxy, receiver))
                slog.info(curl("%s/cservice/TestPlanApi/sendMtestEmail" % emailProxy,
                    toJsonStr({"mimeMail":mimeMail.as_string(), "mailto":";".join(receiver), "mailcc":"", "verify":"mtest"})))
                return

            smtpAccount, smtpPasswd = base64.decodestring(smtpLogin).split("/")
            slog.info("Sending report mail(SMTP %s):\n\t%s -> %s" % (smtpAddr, smtpAccount, receiver))
            smtp = smtpAddr.split(':')
            smtpServer = smtp[0]
            smtpPort = int(ObjOperation.tryGetVal(smtp, 1, 25))

            from smtplib import SMTP
            smtpClient = SMTP(smtpServer, smtpPort)
            try:
                smtpClient.ehlo()
                smtpClient.login(smtpAccount, smtpPasswd)
            except:pass
            smtpClient.sendmail(sender, receiver, mimeMail.as_string())
            smtpClient.quit()
        except Exception as ex:
            slog.info(self.htmlContent)
            slog.info("Fail to send mail for: %s" % ex)


if __name__ == '__main__':
    sr = SummaryReport()
    runInfo = {0: 7, 1: 0, 2: 0, 'num': 7, 'endTime':time.time(), 'startTime': 1475916106.17, 'time': 1, 'cases': {0: {'sampleFun ': 
 0.0, 'sampleTest4 ([4]letter:b)': 0.0, 'sampleTest2 ([2]number:2)': 0.0, 'sampleTest (letter:a)': 0.0,
 'sampleTest5 ([5]letter:c)': 0.0, 'sampleTest1 ([1]other:y)': 0.0, 'sampleTest3 ([3]number:3)': 0.0},
 1: {}, 2: {}, 3: {}}, 3: 0}

    sr.analyzeLogs("product", "version", "environment", runInfo)
    print sr.htmlContent
