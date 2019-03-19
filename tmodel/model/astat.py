

class ApiStatistic:

    def __init__(self):
        self._ascfun = None
    
    def setStatistic(self, repHost=None, env="test", maxidletime=2, tspan=2, isperf=False, repUrl='/cservice/ApiStatistic/reportStatistic', repHandle=None):
        self.repUrl = ("%s%s" % (repHost, repUrl)) if repHost else repHost
        self.maxidletime = int(maxidletime / tspan)
        self.tspan = tspan

        self.s = {}
        self.env = env
        self.isperf = isperf
        self.repHandle = repHandle

        from server.cclient import AsyncCallFun
        self._ascfun = AsyncCallFun(self._addreport, self._doreport, tspan, self.maxidletime)

    def _addreport(self):
        s = self.s; self.s = {}
        return s

    def _doreport(self, t, s):
        if self.repUrl:
            from server.cclient import curl
            from libs.parser import toJsonStr
            if len(s) > 0: curl(self.repUrl, toJsonStr({"t":t, "s":s, 'perf':self.isperf, 'env':self.env, 'span':self.tspan}), connTimeout=.2)
        elif self.repHandle:
            self.repHandle(t, s)
        else:
            print t, s

    def _getApi(self, module, sname):
        try:
            return self.s[sname]
        except:
            return self._resetApi(module, sname)

    def _resetApi(self, module, sname):  # qps, flow, latency, fail-qps, fail-reason
        s = {'m':module, 'q':0, 'fl':0, 'lt':[], 'fq':0, 'fr':None}; self.s[sname] = s
        return s

    def putApi(self, sname, freason=None, module=None, qps=1, fqps=0, flow=0, latency=0):
        if self._ascfun and self._ascfun.iscontinue: 
            s = self._getApi(module, sname)
            s['q'] += qps;s['fq'] += fqps;s['fr'] = freason
            if self.isperf:
                if flow: s['fl'] += flow
                if latency: s['lt'].append(latency)

    def percentile(self, values, percent):
        l = len(values)
        if l == 0:
            return 0
        k = (l - 1) * percent / 100.
        i = int(k)
        if i == k:
            v = values[i]
        else:
            v = (values[i] + values[i + 1]) / 2.
        return int(v * 100) / 100.

    def finishApi(self):
        if self._ascfun:
            self._ascfun.stop()
            try:
                import time
                self._doreport(time.time(), self._addreport())
            except Exception as ex: print "Finish Static: %s" % ex


if __name__ == '__main__':
    pstat = ApiStatistic()

    def percentileRepHandle(t, s):
        for k in s.keys():
            api = s[k]
            lt = api['lt']
            pf = {"t":t, 'api':k, "qps":api['q'], "fqps":api['fq'],
                  "p30":pstat.percentile(lt, 30), "p50":pstat.percentile(lt, 50), "p90":pstat.percentile(lt, 90)}
            print  "{api}\t{t}\t QPS={qps}  FQPS={fqps}\t30%={p30} 50%={p50} 90%={p90}".format(**pf)

    pstat.setStatistic(isperf=True, repHandle=percentileRepHandle)
    for i in range(100):
        pstat.putApi("apiName1", "reason-%s" % (i % 5), latency=0.1)
        import time
        time.sleep(0.1 * i / 10)
