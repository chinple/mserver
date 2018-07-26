'''
Created on 2015-7-10

@author: chinple
'''
from mtest import model, TestCaseBase, scenario, testing
from db.sqllib import SqlConnFactory, Sql
from db.pysql import PymysqlConn
from db.mysqldb import MysqldbConn

@model()
class LibTest(TestCaseBase):

    @scenario()
    def testMysqldb(self):
        
        sqlConfig = {'host':'127.0.0.1', 'port':3306, 'user':'root',
            'passwd':'200123', 'charset':'utf8'}
        # {'passwd': u'200123', 'charset': 'utf8', 'db': u'msg', 'host': u'127.0.0.1', 'user': u'root', 'auto_commit': True, 'port': 3306}
        conn = SqlConnFactory(MysqldbConn, sqlConfig, 1)
        print(conn.executeSql("show tables", dbName='msg'))
        print(conn.getSql("msg", Sql.select).execute())
        
    @scenario()
    def testPymysql(self):
        
        sqlConfig = {'host':'127.0.0.1', 'port':3306, 'user':'root',
            'passwd':'200123', 'db':'msg', 'charset':'utf8', 'auto_commit':True}
        # {'passwd': u'200123', 'charset': 'utf8', 'db': u'msg', 'host': u'127.0.0.1', 'user': u'root', 'auto_commit': True, 'port': 3306}
        conn = SqlConnFactory(PymysqlConn, sqlConfig, 1)
        print(conn.executeSql("show tables"))
        print(conn.getSql("msg", Sql.select).execute())

if __name__ == "__main__":
    testing("-r debug")
