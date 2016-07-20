from server.cclient import curl
from libs.syslog import slog
from threading import Thread
import time

sleepcurl = lambda t : slog.info(curl("http://127.0.0.1:8081/cservice/ServerApi/sleepSeconds?t=%s" % t))

for i in xrange(10240):
    print(i)
    time.sleep(0.01)
    Thread(target=sleepcurl, args=(3600,)).start()

sleepcurl(0)
