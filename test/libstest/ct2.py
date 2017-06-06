
@cloudModule()
class CTestPlanAPi:
    def __init__(self):
        self.dbapi = CtestDbOp()
        self.emailRp = EmailReportor()
    def deleteCtree(self, nid):
        return self.dbapi.deleteCtree(nid)
    def saveCtree(self, name, fnid= -1, nid=None):
        return self.dbapi.saveCtree(name, fnid, nid)
    def getCtreeRoot(self, fnid=None, name=None, nid=None):
        return self.dbapi.getCtree(fnid, name, nid)

    def saveCtestcase(self, scenario, tags, name, ttype, priority, steps, remark,
            fnid=None, nid1=None, nid2=None, caseid=None, __session__=None):
        owner = __session__['name']
        return self.dbapi.saveCtestcase(scenario, tags, name, ttype, priority, steps, remark, owner, fnid, nid1, nid2, caseid)
    def getCtestcase(self, fnid=None, nid1=None, nid2=None,
            searchKey=None, ttype=None, priority=None, name=None, owner=None, caseid=None):
        return self.dbapi.getCtestcase(fnid, nid1, nid2, searchKey, ttype, priority, name, owner, caseid)

    def exportCtestcase(self, fnid=None, nid1=None, nid2=None, searchKey=None, ttype=None, priority=None, owner=None):
        raise ReturnFileException(self.emailRp.formatTestCase(self.dbapi.getCtestcase(fnid, nid1, nid2, searchKey, ttype, priority, owner=owner)),
            'text/html')

    def deleteCtestcase(self, caseid):
        return self.dbapi.deleteCtestcase(caseid)

    def saveCtestplan(self, name=None, owner=None, tags=None, summary=None, issues=None,
            ptype=None, priority=None, status=None, progress=None,
            pstarttime=None, pendtime=None, starttime=None, endtime=None,
            mailto=None, fnid=None, nid1=None, nid2=None, planid=None):
        return self.dbapi.saveCtestplan(name, owner, tags, summary, issues, ptype, priority, status, progress, pstarttime, pendtime, starttime, endtime, mailto, fnid, nid1, nid2, planid)

    def getCtestplan(self, fnid=None, nid1=None, nid2=None,
            nameOrTags=None, ptype=None, priority=None, inStatus=None, outStatus=None,
            starttime1=None, starttime2=None, owner=None):
        return self.dbapi.getCtestplan(fnid, nid1, nid2, nameOrTags, ptype, priority, inStatus, outStatus, starttime1, starttime2, owner)

    def getCtestplanById(self, planid):
        if Sql.isEmpty(planid):
            return
        plans = self.dbapi.getCtestplan(planid=planid)
        if len(plans) > 0:
            plan = plans[0]
            planStatus = cprop.getVal('plan', 'planStatus').split()
            plan['planStatus'] = planStatus[plan['status']]
            plan['pstarttime'] = str(plan['pstarttime']).split()[0]
            plan['pendtime'] = str(plan['pendtime']).split()[0]
            plan['starttime'] = str(plan['starttime']).split()[0]
            plan['endtime'] = str(plan['endtime']).split()[0]
            plan['reportTarget'] = cprop.getVal('plan', 'reportTarget').format(**plan)
            plan['reportSummary'] = cprop.getVal('plan', 'reportSummary').format(**plan)
            case = self.countPlancase(planid, 1)
            plan['reportSummary'] = plan['reportSummary'].format(**case)
        return plans

    def getCtestplancasereport(self, planid):
        planCaseRow = cprop.getVal('plan', 'planCaseRow')
        planCaseStatus = cprop.getVal('plan', 'planCaseStatus').split()
        caseinfo = []
        for case in self.dbapi.getPlancase(planid):
            case['result'] = planCaseStatus[case['status']]
            case['remark'] = '' if case['remark'] is None else case['remark']
            caseinfo.append(planCaseRow.format(**case))
        
        return cprop.getVal('plan', 'planCaseTable').format(body="".join(caseinfo))

    def deleteCtestplan(self, planid):
        return  self.dbapi.deleteCtestplan(planid)

    def savePlancase(self, planid, ftags, plancases, __session__):
        for plancase in plancases:
            caseid, scenario, remark, _, name = plancase.split("|,|")# not use owner
            caseInfo = self.dbapi.getPlancase(planid, caseid)
            if len(caseInfo) > 0:
                case = caseInfo[0]
                plancaseid = case['plancaseid']
                status = case['status']
                owner = case['owner']
                if not Sql.isEmpty(case['remark']):
                    remark = case['remark']
            else:
                plancaseid = None
                status = 0
                owner = __session__['name']

            self.dbapi.savePlancase(planid, caseid, scenario, ftags, name,
                owner, status, remark, plancaseid=plancaseid)

    def syncPlancase(self, planid):
        for plancase in self.dbapi.getPlancase(planid, fields='plancaseid,caseid,remark'):
            plancaseid, caseid, remark = plancase['plancaseid'], plancase['caseid'], plancase['remark']
            case = self.dbapi.getCtestcase(caseid=caseid)
            if len(case) == 0:
                self.dbapi.deletePlancase(plancaseid)
            else:
                scenario, name = case[0]['scenario'], case[0]['name']
                if Sql.isEmpty(remark):
                    remark = case[0]['remark']
                else:
                    remark = None
                self.dbapi.savePlancase(scenario=scenario, name=name, remark=remark, plancaseid=plancaseid)

    def savePlancaseRemark(self, plancaseid, caseid, scenario=None, name=None, remark=None, __session__=None):
        if Sql.isEmpty(plancaseid) or Sql.isEmpty(caseid):return
        owner = __session__['name']
        self.dbapi.saveCtestcase(scenario=scenario, name=name, remark=remark, caseid=caseid)
        self.dbapi.savePlancase(scenario=scenario, name=name, remark=remark, owner=owner, plancaseid=plancaseid)

    def getPlancase(self, planid=None, status=None, owner=None, caseTags=None, caseName=None):
        return self.dbapi.getPlancase(planid, None, owner, status, caseTags, caseName)

    def deletePlancase(self, plancaseid):
        return self.dbapi.deletePlancase(plancaseid)

    def setPlancase(self, plancaseid, status, __session__):
        return self.dbapi.setPlancase(plancaseid, status, __session__['name'])

    def savePlandaily(self, planid, day, status, progress, caseprogress, costtime, costman,
            starttime, endtime, summary, issues, dailyId=None):
        if dailyId is None:
            daily = self.dbapi.getPlandaily(planid, day)
            if len(daily) > 0:
                dailyId = daily[0]['dailyId']
        caseprogress = self.countPlancase(planid, 1)['percent']
        self.dbapi.saveCtestplanStatus(planid, status, progress, starttime, endtime)
        return self.dbapi.savePlandaily(planid, day, status, progress, caseprogress, costtime, costman, summary, issues, dailyId)

    def getPlandaily(self, planid=None, day=None, dailyId=None):
        return self.dbapi.getPlandaily(planid, day, dailyId)

    def countPlancase(self, planid=None, status=None):
        count, total = self.dbapi.countPlancase(planid, status)[0]['count'], self.dbapi.countPlancase(planid)[0]['count']
        percent = 0 if total <= 0 else count * 100 / total
        return {'count':count, 'total':total, 'percent':percent}

    planStatusFinished = 3
    def getPlanSummary(self, planid):
        psummary = self.dbapi.getPlandaily(planid, limit=1)
        if len(psummary) == 1 and psummary[0]['status'] == self.planStatusFinished:
            return psummary[0]

    def getPlanSummaryReport(self, planid, summary, issues, isSetFinish=False):
        isSetFinish = str(isSetFinish).lower() == 'true'
        psummary = self.getPlanSummary(planid)
        if psummary is None:
            day = self.getDay()
        else:
            day = psummary['day']
        if isSetFinish:
            self.savePlandaily(planid, day, status=self.planStatusFinished,
                progress=100, caseprogress=None, costtime=None, costman=None,
                starttime=None, endtime=None, summary=summary, issues=issues)

        cplan = self.getCtestplanById(planid)[0]
        casereport = self.getCtestplancasereport(planid)
        subject = cprop.getVal("plan", "reportSubject").format(**cplan)
        emailbody = self.emailRp.formatPlanreport(cplan['reportTarget'], cplan['reportSummary'],
                summary, issues, casereport)
        return subject, emailbody

    def sendPlanSummaryEmail(self, planid, summary, issues, sender, receiver, ccReceiver, isSetFinish):
        subject, emailbody = self.getPlanSummaryReport(planid, summary, issues, isSetFinish)

        smtpSender = cprop.getVal("email", "smtpSender")
        smtpAddr = cprop.getVal("email", "smtpAddr")
        smtpLogin = cprop.getVal("email", "smtpLogin")
        mimeMail = self.emailRp.makeEmail(sender, receiver, ccReceiver, subject, emailbody)
        self.dbapi.saveCtestplanStatus(planid, mailto=receiver, mailfrom=sender, mailcc=ccReceiver)
        return self.emailRp.sendEmail(smtpAddr, smtpLogin, smtpSender, receiver, ccReceiver, mimeMail)

    def getDay(self):
        return time.strftime('%Y-%m-%d')

    def getPlandailyEmail(self, planid, day=None):
        plan = self.dbapi.getCtestplan(planid=planid)[0]
        subject, title = self.emailRp.formatSubject(plan, day)
        
        dailys = []
        for daily in self.dbapi.getPlandaily(planid):
            dailys.append(self.emailRp.formatDaily(daily))
        return subject, self.emailRp.formatPlans(dailys, title)

    def sendPlandailyEmail(self, planid, day, sender, receiver, ccReceiver=''):
        subject, htmlBody = self.getPlandailyEmail(planid, day)

        smtpSender = cprop.getVal("email", "smtpSender")
        smtpAddr = cprop.getVal("email", "smtpAddr")
        smtpLogin = cprop.getVal("email", "smtpLogin")
        mimeMail = self.emailRp.makeEmail(sender, receiver, ccReceiver, subject, htmlBody)
        self.dbapi.saveCtestplanStatus(planid, mailto=receiver, mailfrom=sender, mailcc=ccReceiver)
        return self.emailRp.sendEmail(smtpAddr, smtpLogin, smtpSender, receiver, ccReceiver, mimeMail)

    def getPlanReport(self, ptype, inStatus=None, outStatus=None,
            fnid=None, nid1=None, nid2=None, name='all', tags=None, starttime1=None, starttime2=None):

        names = name.split(',')
        planList = []
        for n in names:
            if n.strip() == "":
                continue
            
            plans = self.dbapi.getCtestplan(fnid, nid1, nid2, ptype=ptype, inStatus=inStatus, outStatus=outStatus,
                starttime1=starttime1, starttime2=starttime2, name=(None if n == 'all' else n), tags=tags)
            if n != 'all':
                self.emailRp.addPlangroupTitle(n, planList)
            for plan in plans:
                planid = plan['planid']
                daily = self.dbapi.getPlandaily(planid, limit=1)
                self.emailRp.addPlangroup(plan, daily, planList)
        return self.emailRp.formPlangroup(planList)

    def sendPlanReport(self, sender, receiver, ccReceiver, subject,
            ptype, inStatus=None, outStatus=None,
            fnid=None, nid1=None, nid2=None, name='all', tags=None, starttime1=None, starttime2=None):
        htmlBody = self.getPlanReport(ptype, inStatus, outStatus, fnid, nid1, nid2, name, tags, starttime1, starttime2)

        smtpSender = cprop.getVal("email", "smtpSender")
        smtpAddr = cprop.getVal("email", "smtpAddr")
        smtpLogin = cprop.getVal("email", "smtpLogin")
        mimeMail = self.emailRp.makeEmail(sender, receiver, ccReceiver, subject, htmlBody)
        return self.emailRp.sendEmail(smtpAddr, smtpLogin, smtpSender, receiver, ccReceiver, mimeMail)

    def getTestEnv(self, envname=None, hostip=None, vmaccount=None, owner=None, ownerStatus=None, fnid=None, nid1=None, nid2=None, testenvid=None):
        return self.dbapi.getTestEnv(envname, hostip, vmaccount, owner, ownerStatus, fnid, nid1, nid2, testenvid)

    def deleteTestEnv(self, testenvid):
        return self.dbapi.deleteTestEnv(testenvid)

    def saveTestEnv(self, envname, tags=None, hostip=None, hostaccount=None, hostinfo=None,
            vmaccount=None, vmammounts=None, vminfo=None, owner=None, ownerStatus=None, ownerInfo=None, ownerStartTime=None, ownerEndTime=None,
            fnid=None, nid1=None, nid2=None, testenvid=None):
        return self.dbapi.saveTestEnv(envname, tags, hostip, hostaccount, hostinfo, vmaccount, vmammounts, vminfo, owner, ownerStatus, ownerInfo, ownerStartTime, ownerEndTime, fnid, nid1, nid2, testenvid)

# test config
    def getTestConfig(self, subject=None, stype=None, cname=None, ckey=None, fnid=None, nid1=None, nid2=None, configid=None):
        return {'fileLink':cprop.getVal('cconfig', 'fileLink'), 'data':self.dbapi.getTestConfig(subject, stype, cname, ckey, fnid, nid1, nid2, configid)}

    def saveTestConfig(self, cname, subject, ckey, stype, ccontent, fnid=None, nid1=None, nid2=None, configid=None, __session__=None):
        owner = __session__['name']

        if stype == '3' and ccontent.strip() != '':
            fileFolder = cprop.getVal('cconfig', 'fileFolder')
            with open(fileFolder + cname, 'wb') as f:
                f.write(ccontent)
        return self.dbapi.saveTestConfig(cname, subject, ckey, stype, ccontent, owner, fnid, nid1, nid2, configid)

    def deleteTestConfig(self, configid):
        return self.dbapi.deleteTestConfig(configid)

class BugFreeApi:
    def __init__(self):
        sqlConfig = {'host':cprop.getVal("bugfree", "host"), 'port':cprop.getInt("bugfree", "port"),
            'user':cprop.getVal("bugfree", "user"), 'passwd':cprop.getVal("bugfree", "passwd"),
            'db':cprop.getVal("bugfree", "db"), 'charset':'utf8'}
        self.sqlConn = SqlConnFactory(MysqldbConn, sqlConfig)
        self.bfapi = cprop.getVal("bugfree", "bfapi")

    def getBfUser(self, username):
        sql = self.sqlConn.getSql("bf_test_user", Sql.select, True, 'username,realname,email')
        sql.appendWhereByJson({'username':username})
        return sql.execute()

    def _strmd5(self, str):
        import md5  
        m = md5.new()  
        m.update(str)  
        return m.hexdigest()
        
    def login(self, username, password):
        resp = toJsonObj(curl("http://%s/api3.php?mode=getsid" % self.bfapi))
        sessionname = resp['sessionname']
        sessionid = resp['sessionid']
        rand = resp['rand']
        
        auth = self._strmd5(self._strmd5(username + self._strmd5(password)) + rand) 
        
        url = 'http://%s/api3.php?mode=login&&%s=%s&username=%s&auth=%s' % (self.bfapi, sessionname, sessionid, username, auth)
        login = toJsonObj(curl(url))

        user = self.getBfUser(username)
        return {'status':login['status'] == 'success', 'name':user[0]['realname'] if len(user) == 1 else 'NotExist'}

@cloudModule(handleUrl='/')
class AuthApi(LocalMemSessionHandler):
    def __init__(self):
        self.bugfree = BugFreeApi()
        LocalMemSessionHandler.__init__(self)
        self.redirectPath = '/clogin.html'
        self.__ignoreMethods__('checkLogin')
        self.__ignorePaths__('/clogin.html', '/cservice/AuthApi/checkLogin')

    def checkLogin(self, name, password, loginfrom="", __session__=None):
        
        bglogin = self.bugfree.login(name, password)
        if bglogin['status']:
            __session__['name'] = bglogin['name']
            __session__['authorized'] = True
            url = loginfrom[6:]
            if not url.__contains__(".html") and not url.__contains__("?"):
                url = '/'
        else:
            url = "/clogin.html?login=Failed"
        raise RedirectException(url)

    def getLoginInfo(self, __session__):
        return {'name':__session__['name']}

    def logout(self, session):
        return self.__invalidateSession__(session['id'])

    def __checkSessionAuthStatus__(self, session, reqObj, reqPath, reqParam):
        return session.__contains__('authorized')

if __name__ == "__main__":
    from cserver import servering
    cprop.load("cplan.ini")
    servering("-p 8089 -f webs  -m cplan.html -t ctoolApi.py")
