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
        print("please type command: server, or direct test arguments.")
    elif sys.argv[1] == "server":
        from cserver import servering
        servering(*sys.argv[2:] if len(sys.argv) > 2 else ("-h",))
    else:
        from mtest import testing
        testing(*sys.argv[2 if sys.argv[1] == "test" else 1:])
