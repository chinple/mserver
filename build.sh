rm *.pyc
rm */*.pyc
rm */*/*.pyc

rm ../mserver.tar
tar cf ../mserver.tar run.py  mtest.py cserver.py cperf.py libs db server tmodel tools uimodel
ls -l ../mserver.tar

scp ../mserver.tar  sh_testdev:/data/qa/tytestplatform/files/pic/
scp ../mserver.tar  tuya@172.16.0.85:/data/qa/tytestplatform/files/pic/