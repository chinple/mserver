# -*- coding: utf8 -*-
'''
Created on 2010-9-28

@author: chinple
'''
import sys

reload(sys)
eval('sys.setdefaultencoding("utf-8")')
if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("please type command: stop, server, test or perf")
    elif sys.argv[1] == "stop":
        import os
        runcmd = "ps aux |grep run.py|grep -v grep|grep -v stop %s" % (("|grep '%s'" % sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != "" else "")
        os.system(runcmd)
        print "Kill all(yes|y)?"
        if sys.stdin.readline().__contains__("y"):
            os.system("%s|awk  '{print $2}'|xargs kill -9" % runcmd)
        os.system(runcmd)
    elif sys.argv[1] == "server":
        from cserver import servering
        servering(*sys.argv[2:] if len(sys.argv) > 2 else ("-h",))
    elif sys.argv[1] == "perf":
        from cperf import running
        running(*sys.argv[2:] if len(sys.argv) > 2 else ("-h",))
    else:
        from mtest import testing
        testing(*sys.argv[2 if sys.argv[1] == "test" else 1:])
