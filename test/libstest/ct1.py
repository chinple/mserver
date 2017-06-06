# -*- coding: utf8 -*-
'''
Created on 2016-10-2

@author: chinple
'''
from db.sqllib import SqlConnFactory, Sql
from db.mysqldb import MysqldbConn
from cserver import cprop, cloudModule
from libs.timmer import TimmerOperation
import time
from libs.syslog import slog
from libs.objop import ObjOperation
import base64
from server.csession import LocalMemSessionHandler
from server.chandle import RedirectException, ReturnFileException
from libs.parser import toJsonObj
from server.cclient import curl

class CtestDbOp:
    def __init__(self):
        sqlConfig = {'host':cprop.getVal("db", "host"), 'port':cprop.getInt("db", "port"),
            'user':cprop.getVal("db", "user"), 'passwd':cprop.getVal("db", "passwd"),
            'db':cprop.getVal("db", "db"), 'charset':'utf8'}
        self.sqlConn = SqlConnFactory(MysqldbConn, sqlConfig)

    def saveCtree(self, name, fnid= -1, nid=None):
        sql = self.sqlConn.getSql("ctree", Sql.insert if nid is None else Sql.update, True)
        sql.appendValueByJson({'name':name, "fnid":fnid, "nid":nid})
        sql.appendWhere("nid", nid)
        return sql.execute()

    def getCtree(self, fnid=None, name=None, nid=None):
        sql = self.sqlConn.getSql("ctree", Sql.select, True)
        sql.appendWhereByJson({'name':name, "fnid":fnid, "nid":nid})
        return sql.execute()
    def deleteCtree(self, nid):
        if Sql.isEmpty(nid):
            return 0
        sql = self.sqlConn.getSql("ctree", Sql.delete, True)
        sql.appendWhere("nid", nid)
        return sql.execute()
# test case
    def saveCtestcase(self, scenario=None, tags=None, name=None, ttype=None, priority=None, steps=None, remark=None, owner=None,
            fnid=None, nid1=None, nid2=None, caseid=None):
        modifytime = TimmerOperation.getFormatTime(time.time())
        sql = self.sqlConn.getSql("testcase", Sql.insert if Sql.isEmpty(caseid) else Sql.update, True)
        sql.appendValueByJson({'scenario':scenario, 'tags':tags, 'name':name, "ttype":ttype, "priority":priority,
            'steps':steps, "remark":remark, "owner":owner, 'modifytime':modifytime,
            "fnid":fnid, "nid1":nid1, "nid2":nid2, "caseid":caseid})
        sql.appendWhere("caseid", caseid)
        return sql.execute()

    def getCtestcase(self, fnid=None, nid1=None, nid2=None,
            searchKey=None, ttype=None, priority=None, name=None, owner=None, caseid=None):
        sql = self.sqlConn.getSql("testcase", Sql.select, True)
        conditions = []
        if not Sql.isEmpty(fnid):
            conditions.append('fnid = %s' % fnid)
        if not Sql.isEmpty(nid1):
            conditions.append('nid1 = %s' % nid1)
        if not Sql.isEmpty(nid2):
            conditions.append('nid2 = %s' % nid2)
        if len(conditions) > 0:
            sql.appendCondition("(%s)" % (" or ".join(conditions)))

        sql.appendWhereByJson({'name':name, "ttype":ttype, "priority":priority,
            "owner":owner, "caseid":caseid})
        if not Sql.isEmpty(searchKey):
            searchKey = '%%%s%%' % searchKey
            sql.appendCondition("(name like '%s' or tags like '%s'or scenario like '%s')" % (searchKey, searchKey, searchKey))
        sql.orderBy("scenario,name")
        return sql.execute()

    def deleteCtestcase(self, caseid):
        if Sql.isEmpty(caseid):
            return 0
        sql = self.sqlConn.getSql("testcase", Sql.delete, True)
        sql.appendWhere("caseid", caseid)
        return sql.execute()

# test plan
    def saveCtestplan(self, name=None, owner=None, tags=None, summary=None, issues=None,
            ptype=None, priority=None, status=None, progress=None,
            pstarttime=None, pendtime=None, starttime=None, endtime=None,
            mailto=None, fnid=None, nid1=None, nid2=None, planid=None):
        # status: created, executing, finished, paused

        sql = self.sqlConn.getSql("testplan", Sql.insert if Sql.isEmpty(planid) else Sql.update, True)
        sql.appendValueByJson({'name':name, 'owner':owner, 'tags':tags, 'summary':summary, 'issues':issues,
            'ptype':ptype, 'priority':priority, "status":status, "progress":progress,
            'pstarttime':pstarttime, "pendtime":pendtime, "starttime":starttime, 'endtime':endtime,
            "mailto":mailto, "fnid":fnid, "nid1":nid1, "nid2":nid2, "planid":planid})
        sql.appendWhere("planid", planid)
        return sql.execute()

    def saveCtestplanStatus(self, planid, status=None, progress=None, starttime=None, endtime=None,
            mailto=None, mailfrom=None, mailcc=None):
        if Sql.isEmpty(planid):
            return 0
        sql = self.sqlConn.getSql("testplan", Sql.update, True)
        sql.appendValueByJson({ 'status':status, 'progress':progress, 'starttime':starttime, 'endtime':endtime,
            'mailto':mailto, 'mailfrom':mailfrom, 'mailcc':mailcc})
        sql.appendWhere("planid", planid)
        return sql.execute()

    def getCtestplan(self, fnid=None, nid1=None, nid2=None,
            nameOrTags=None, ptype=None, priority=None, inStatus=None, outStatus=None,
            starttime1=None, starttime2=None, owner=None, name=None, tags=None, planid=None):
        sql = self.sqlConn.getSql("testplan", Sql.select, True)

        conditions = []
        if not Sql.isEmpty(fnid):
            conditions.append('fnid = %s' % fnid)
        if not Sql.isEmpty(nid1):
            conditions.append('nid1 = %s' % nid1)
        if not Sql.isEmpty(nid2):
            conditions.append('nid2 = %s' % nid2)
        if len(conditions) > 0:
            sql.appendCondition("(%s)" % (" or ".join(conditions)))

        if not Sql.isEmpty(nameOrTags):
            nameOrTags = '%%%s%%' % nameOrTags
            sql.appendCondition("(name like '%s' or tags like '%s')" % (nameOrTags, nameOrTags))
        if not Sql.isEmpty(name):
            name = '%%%s%%' % name
            sql.appendWhere('name', name, 'like')
        if not Sql.isEmpty(tags):
            tags = '%%%s%%' % tags
            sql.appendWhere('tags', tags, 'like')
        
        sql.appendWhereByJson({"owner":owner, 'priority':priority, 'status':inStatus, "planid":planid})
        sql.appendWhere('ptype', ptype, 'in')
        sql.appendWhere('status', outStatus, '!=')
        sql.appendWhere("starttime", starttime1, ">=").appendWhere("starttime", starttime2, "<")

        sql.orderBy("status,ptype,name,tags,fnid desc,endtime desc")
        return sql.execute()

    def deleteCtestplan(self, planid):
        if Sql.isEmpty(planid):
            return 0
        sql = self.sqlConn.getSql("testplan", Sql.delete, True)
        sql.appendWhere("planid", planid)
        return sql.execute()

# plan related
    def savePlancase(self, planid=None, caseid=None, scenario=None, tags=None, name=None, owner=None, status=None, remark=None, plancaseid=None):
        # status: not-start, executing, passed, failed
        modifytime = TimmerOperation.getFormatTime(time.time())
        sql = self.sqlConn.getSql("plancase", Sql.insert if Sql.isEmpty(plancaseid) else Sql.update, True)
        sql.appendValueByJson({'planid':planid, "caseid":caseid, "tags":tags, "scenario":scenario, "name":name,
            'owner':owner, 'remark':remark, "status":status, "modifytime":modifytime})
        sql.appendWhere("plancaseid", plancaseid)
        return sql.execute()

    def setPlancase(self, plancaseid, status, owner):
        # status: not-start, executing, passed, failed
        sql = self.sqlConn.getSql("plancase", Sql.update, True)
        sql.appendValueByJson({"status":status, 'owner':owner})
        sql.appendWhere("plancaseid", plancaseid)
        return sql.execute()

    def getPlancase(self, planid, caseid=None, owner=None, status=None, caseTags=None, caseName=None, fields='*'):
        sql = self.sqlConn.getSql("plancase", Sql.select, True, fields)
        sql.appendWhereByJson({'planid':planid, "caseid":caseid,
            "status":status })

        if not Sql.isEmpty(owner):
            owner = '%%%s%%' % owner
            sql.appendCondition("(owner like '%s')" % (owner))

        if not Sql.isEmpty(caseTags):
            caseTags = '%%%s%%' % caseTags
            sql.appendCondition("(tags like '%s' or scenario like '%s')" % (caseTags, caseTags))

        if not Sql.isEmpty(caseName):
            caseName = '%%%s%%' % caseName
            sql.appendCondition("(name like '%s')" % (caseName))

        sql.orderBy('tags,scenario,caseid')
        return sql.execute()

    def countPlancase(self, planid=None, status=None):
        sql = self.sqlConn.getSql("plancase", Sql.select, True, 'count(*) as count')
        sql.appendWhereByJson({'planid':planid, "status":status })
        return sql.execute()

    def deletePlancase(self, plancaseid):
        if Sql.isEmpty(plancaseid):
            return 0
        sql = self.sqlConn.getSql("plancase", Sql.delete, True)
        sql.appendWhere("plancaseid", plancaseid)
        return sql.execute()

    def savePlandaily(self, planid, day, status, progress, caseprogress,
            costtime, costman, summary, issues, dailyId=None):
        sql = self.sqlConn.getSql("plandaily", Sql.insert if Sql.isEmpty(dailyId) else Sql.update, True)
        sql.appendValueByJson({'planid':planid, "day":day, "status":status, "progress":progress, 'caseprogress':caseprogress,
            'costtime':costtime, 'costman':costman, 'summary':summary, 'issues':issues, "dailyId":dailyId})
        sql.appendWhere("dailyId", dailyId)
        return sql.execute()

    def getPlandaily(self, planid=None, day=None, dailyId=None, limit=None, status=None):
        sql = self.sqlConn.getSql("plandaily", Sql.select, True)
        sql.appendWhereByJson({'planid':planid, "dailyId":dailyId, 'day':day, "status":status})
        sql.limit = limit
        sql.orderBy("day DESC")
        return sql.execute()
    
# test env
    def getTestEnv(self, envname, hostip, vmaccount, owner, ownerStatus, fnid, nid1, nid2, testenvid=None):
        sql = self.sqlConn.getSql("testenv", Sql.select, True)
        sql.appendWhereByJson({'hostip': hostip,
            'owner':owner, 'ownerStatus': ownerStatus})

        conditions = []
        if not Sql.isEmpty(fnid):
            conditions.append('fnid = %s' % fnid)
        if not Sql.isEmpty(nid1):
            conditions.append('nid1 = %s' % nid1)
        if not Sql.isEmpty(nid2):
            conditions.append('nid2 = %s' % nid2)
        if len(conditions) > 0:
            sql.appendCondition("(%s)" % (" or ".join(conditions)))

        if not Sql.isEmpty(vmaccount):
            vmaccount = '%%%s%%' % vmaccount
            sql.appendCondition("(vmaccount like '%s')" % (vmaccount))

        if not Sql.isEmpty(envname):
            envname = '%%%s%%' % envname
            sql.appendCondition("(envname like '%s' or tags like '%s')" % (envname, envname))
        # 'vmammounts': vmammounts
        # 'ownerStartTime': ownerStartTime, 'ownerEndTime': ownerEndTime,
        sql.appendWhere("testenvid", testenvid)
        return sql.execute()

    def saveTestEnv(self, envname, tags, hostip, hostaccount, hostinfo,
            vmaccount, vmammounts, vminfo, owner, ownerStatus, ownerInfo, ownerStartTime, ownerEndTime,
            fnid, nid1, nid2, testenvid=None):

        sql = self.sqlConn.getSql("testenv", Sql.insert if Sql.isEmpty(testenvid) else Sql.update, True)
        sql.appendValueByJson({'envname':envname, 'tags':tags, 'hostip': hostip, 'hostaccount': hostaccount, 'hostinfo': hostinfo,
            'vmaccount': vmaccount, 'vmammounts': vmammounts, 'vminfo':vminfo,
            'owner':owner, 'ownerStatus': ownerStatus, 'ownerInfo': ownerInfo, 'ownerStartTime': ownerStartTime, 'ownerEndTime': ownerEndTime,
            'fnid': fnid, 'nid1': nid1, 'nid2': nid2})
        sql.appendWhere("testenvid", testenvid)
        return sql.execute()

    def deleteTestEnv(self, testenvid):
        if Sql.isEmpty(testenvid):
            return 0
        sql = self.sqlConn.getSql("testenv", Sql.delete, True)
        sql.appendWhere("testenvid", testenvid)
        return sql.execute()

# test config
    def getTestConfig(self, subject=None, stype=None, cname=None, ckey=None, fnid=None, nid1=None, nid2=None, configid=None):
        sql = self.sqlConn.getSql("cconfig", Sql.select, True)
        sql.appendWhereByJson({'configid': configid, 'stype':stype})

        conditions = []
        if not Sql.isEmpty(fnid):
            conditions.append('fnid = %s' % fnid)
        if not Sql.isEmpty(nid1):
            conditions.append('nid1 = %s' % nid1)
        if not Sql.isEmpty(nid2):
            conditions.append('nid2 = %s' % nid2)
        if len(conditions) > 0:
            sql.appendCondition("(%s)" % (" or ".join(conditions)))

        if not Sql.isEmpty(subject):
            subject = '%%%s%%' % subject
            sql.appendCondition("(subject like '%s')" % (subject))

        if not Sql.isEmpty(cname):
            cname = '%%%s%%' % cname
            sql.appendCondition("(cname like '%s')" % (cname))
        
        if not Sql.isEmpty(ckey):
            ckey = '%%%s%%' % ckey
            sql.appendCondition("(ckey like '%s')" % (ckey))

        return sql.execute()

    def saveTestConfig(self, cname, subject, ckey, stype, ccontent, owner, fnid, nid1, nid2, configid=None):
        modifytime = TimmerOperation.getFormatTime(time.time())

        sql = self.sqlConn.getSql("cconfig", Sql.insert if Sql.isEmpty(configid) else Sql.update, True)
        sql.appendValueByJson({'cname':cname, 'subject':subject, 'ckey': ckey, 'stype': stype, 'ccontent': ccontent,
            "owner":owner, 'modifytime':modifytime, 'fnid': fnid, 'nid1': nid1, 'nid2': nid2})
        sql.appendWhere("configid", configid)
        return sql.execute()

    def deleteTestConfig(self, configid):
        if Sql.isEmpty(configid):
            return 0
        sql = self.sqlConn.getSql("cconfig", Sql.delete, True)
        sql.appendWhere("configid", configid)
        return sql.execute()

class EmailReportor:
    def __init__(self):
        self.emailDailySubject = cprop.getVal('plan', 'emailDailySubject')
        self.emailDailySp = cprop.getVal('plan', 'emailDailySp')
        self.emailDailyRow = cprop.getVal('plan', 'emailDailyRow')
        self.emailDailyBody = cprop.getVal('plan', 'emailDailyBody')
        self.planLink = cprop.getVal('plan', 'planLink')
        self.emailDailyTitle = cprop.getVal('plan', 'emailDailyTitle')

        self.riskStatusDefine = cprop.getVal('plan', 'planStatus').split()
        self.emailPlanBodyTemplate = cprop.getVal('plan', 'emailPlanBodyTemplate')
        emailPlanRowFormat = 'textarea'
        self.emailPlanRowFormat = ObjOperation.tryGetVal({'textarea':"<textarea>%s</textarea>", 'pre':"<pre>%s</pre>"}, emailPlanRowFormat, '%s')
        self.emailPlanRow = cprop.getVal('plan', 'emailPlanRow')
        self.emailPlanRowTitle = cprop.getVal('plan', 'emailPlanRowTitle')
        
        self.reportBodyTemplate = cprop.getVal('plan', 'reportBodyTemplate')

# plan report
    def formatPlanreport(self, planReportTarget, planReportDetail, planreportSummary, planreportIssues, planReportCaseSummary):
        planreport = open(self.reportBodyTemplate).read()
        planreport = planreport.replace('{planReportTarget}', planReportTarget)
        planreport = planreport.replace('{planReportDetail}', planReportDetail)
        planreport = planreport.replace('{planreportSummary}', planreportSummary)
        planreport = planreport.replace('{planreportIssues}', planreportIssues)
        planreport = planreport.replace('{planReportCaseSummary}', planReportCaseSummary)
        return planreport

# plan group
    def formatSubject(self, plan, day):
        plan['day'] = day
        plan['planLink'] = self.planLink
        subject = self.emailDailySubject.format(**plan)
        title = self.emailDailyTitle.format(**plan)
        return subject, title

    def formatDaily(self, daily):
        day, progress, caseprogress = daily['day'], daily['progress'], daily['caseprogress']
        summary, issues = daily['summary'], daily['issues']
        daily['day'] = day.strftime("%Y-%m-%d")
        daily['progress'] = '%s%%' % progress
        daily['caseprogress'] = 'N/A' if caseprogress is None else ('%s%%' % caseprogress)
        space = '    '
        daily['summary'] = space + ('' if summary is None else summary.replace('\n', '\n' + space))
        daily['issues'] = space + ('' if issues is None else issues.replace('\n', '\n' + space))
        return self.emailDailyRow.format(**daily)
    
    def formatPlans(self, dailys, title):
        return self.emailDailyBody.format(plan=("\n" + self.emailDailySp).join(dailys), sp=self.emailDailySp, title=title)

    def addPlangroupTitle(self, name, plans):
        plans.append(self.emailPlanRowTitle.format(name=name))
    def addPlangroup(self, plan, daily, plans):
        plan['status'] = self.riskStatusDefine[plan['status']]
        plan['planLink'] = self.planLink
        plan['summary'] = self.emailPlanRowFormat % plan['summary']
        plan['pstarttime'] = str(plan['pstarttime']).split(' ')[0]
        plan['pendtime'] = str(plan['pendtime']).split(' ')[0]
        plan['endtime'] = str(plan['endtime']).split(' ')[0]
        plan['starttime'] = str(plan['starttime']).split(' ')[0]

        daily = daily[0] if len(daily) > 0 else None

        plan['progress'] = '' if daily is None else ('%s%%' % daily['progress'])
        plan['dailyDay'] = '' if daily is None else str(daily['day']).split(' ')[0]
        plan['dailySummary'] = '' if daily is None else (self.emailPlanRowFormat % daily['summary'])
        plan['dailyIssues'] = '' if daily is None else (self.emailPlanRowFormat % daily['issues'])
        plans.append(self.emailPlanRow.format(**plan))

    def formPlangroup(self, plans):
        return open(self.emailPlanBodyTemplate).read().replace("{plans}", "".join(plans))

    def makeEmail(self, sender, receiver, ccReceiver, subject, htmlBody):
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        mimeMail = MIMEMultipart()
        mimeMail.add_header("Date", time.strftime("%A, %d %B %Y %H:%M"))
        mimeMail.add_header("From", sender)
        mimeMail.add_header("To", receiver)
        mimeMail.add_header("cc", ccReceiver)
        mimeMail.add_header("Subject", subject)
        mimeMail.attach(MIMEText(_text=htmlBody.encode("utf8"), _subtype="html", _charset="utf8"))
        return mimeMail

    def sendEmail(self, smtpAddr, smtpLogin, smtpSender, receiver, ccReceiver, mimeMail):
        try:
            if receiver == "":
                raise Exception("No receiver")
            receiver = (receiver + ";" + ccReceiver).replace(';;', ';').split(";")
            smtpAccount, smtpPasswd = base64.decodestring(smtpLogin).split("/")
            from smtplib import SMTP
            slog.info("Sending mail(SMTP %s):\n\t%s -> %s" % (smtpAddr, smtpAccount, receiver))
            smtp = smtpAddr.split(':')
            smtpServer = smtp[0]
            smtpPort = int(ObjOperation.tryGetVal(smtp, 1, 25))
            smtpClient = SMTP(smtpServer, smtpPort)
            try:
                smtpClient.ehlo()
                smtpClient.login(smtpAccount, smtpPasswd)
            except:pass
            smtpClient.sendmail(smtpSender, receiver, mimeMail.as_string())
            smtpClient.quit()
            return 'Success'
        except Exception as ex:
            slog.info("Fail to send mail for: %s" % ex)
            return str(ex)

    # test cases
    def formatTestCase(self, testcases):
        cases = []
        for t in testcases:
            cases.append(cprop.getVal("testcase", 'caseRow').format(**t))
        return open(cprop.getVal("testcase", 'caseReportTemplate')).read().replace("{testcases}", "".join(cases))
