'''
Created on 2016-6-1

@author: chinple
'''

from db.sqllib import SqlConnBase
from server.cclient import curlCservice


class SqlCserviceProxy(SqlConnBase):

# sqlConfig = { 'host':host, 'path':path, 'passwd':passwd }
    def __executeSql__(self, sqlStr, isSelect=True, isFethall=True, isCommit=True, dbName=None):
        return curlCservice(self.host, self.path, isCheckResp=True, passwd=self.passwd,
                sqlStr=sqlStr, isSelect=isSelect, isFethall=isFethall, isCommit=isCommit, dbName=dbName)

    def __reConnect__(self):
        self.host = self.sqlConfig['host']
        self.path = self.sqlConfig['path']
        self.passwd = self.sqlConfig['passwd']
