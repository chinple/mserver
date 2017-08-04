

'''
Created on 2015-7-10

@author: chinple
'''
from cserver import servering

if __name__ == "__main__":
    # --workerSize 5
    servering(r' -p 8081 -t D:\explore\mserver\tools\stool\logProxy.py -s 172.16.6.37:8089 --initMethods "LogHttpProxy.addUrlMock,LogHttpProxy.reloadProxyConfig"')
