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


class SqlToolProxy(SqlConnBase):

# sqlConfig = { 'host':host, 'path':path, 'dbconfig':dbconfig }
    def __executeSql__(self, sqlStr, isSelect=True, isFethall=True, isCommit=True, dbName=None):
        import base64
        return curlCservice(self.host, None, urlPath=self.path, isCheckResp=True,
                base64Sql=base64.encodestring(sqlStr), dbName=dbName, dbconfig=self.dbconfig)

    def __reConnect__(self):
        self.host = self.sqlConfig['host']
        self.path = self.sqlConfig['path']
        self.dbconfig = self.sqlConfig['dbconfig']


if __name__ == '__main__':
    from db.sqllib import SqlConnFactory
    conn = SqlConnFactory()
    conn.setSqlclass(SqlToolProxy, {'host':'172.16.12.124:8085', 'path':'/cservice/OnlineSqlTool/onlineExecuteSql', 'dbconfig':"dev"}, 1)
    print conn.executeSql("show tables", dbName='mysql')
