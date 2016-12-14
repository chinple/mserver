    sysFunReg = PyRegExp('__.+__|beginTestCase|endTestCase|setUp|tearDown|errorHandle')
            raise TestCheck(MTConst.containInfo % ("False", msg, strA, inStrB))
        self.tlog.success(MTConst.containInfo % ("True", msg, strA, inStrB))
        self.tprop = IniConfigure()
        self.startTime = time.time()
    def init(self, runMode="debug", testrunConfig="", logFilePath="", isXmlLog=False,
            tcPattern=None, outTcPattern=None, searchKey=None, propConf={}):
        
        if not self.tprop.load(testrunConfig):
            if testrunConfig != "":
                slog.warn("Not found testrunConfig: %s" % testrunConfig)

            tcInfo.orders = None
                try:
                    caseFun = eval("tempObj.%s" % caseName)
                except:
                    raise Exception("Deuplicate class %s, no method %s" % (tempObj.__class__, caseName))
        if tcInfo.orders != None:
            tOrders = type(tcInfo.orders)
                runList.sort(reverse=not tcInfo.orders)
            if tOrders == list and len(tcInfo.orders) > 0 and len(runList) > 1:
                for caseName in tcInfo.orders:
        runRep = {'startTime':self.startTime, 'endTime':time.time(), 'num':0, 'time':0,
            'cases':{MTConst.passed:{}, MTConst.warned:{}, MTConst.failed:{}, MTConst.notRun:{}},
            MTConst.passed:0, MTConst.warned:0, MTConst.failed:0, MTConst.notRun:0}


                    tcFullName = self.getTCFullName(tcName, tpIndex, tcResInfo['d'])
                    if resType is None:
                        searchkey = tcResInfo['k']
                        author = ObjOperation.tryGetVal(searchkey, 'author', '')
                        priority = ObjOperation.tryGetVal(searchkey, 'priority', '')
                        runRep['cases'][tcRes][tcFullName] = "%ss%s%s" % (tcTime,
                            "" if author == "" else (", %s" % author), "" if priority == "" else (", %s" % priority))
                    elif resType == tcRes:
                        repHandler("\t%s%s", tcFullName , ("\t%ss" % tcTime) if tcTime > 0 else "")
