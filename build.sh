rm *.pyc
rm */*.pyc
rm */*/*.pyc

rm ../mserver.tar
tar cf ../mserver.tar run.py  mtest.py cserver.py cperf.py libs db server tmodel tools uimodel
ls -l ../mserver.tar
