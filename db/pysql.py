'''
Created on 2016-6-1

@author: chinple
'''

import pymysql
from pymysql.err import OperationalError, Error
from db.sqllib import SqlConnBase

class PymysqlConn(SqlConnBase):
    # sqlConfig = {'host':host, 'port':port, 'user':user, 'passwd':passwd, 'db':db, 'charset':'utf8', 'auto_commit':True }
    def __executeSql__(self, sqlStr, isSelect=True, isFethall=True, isCommit=True, dbName=None):
        try:
            if isSelect:     
                c = self.conn.cursor(pymysql.cursors.DictCursor if isFethall else None)
                res = c.execute(sqlStr)
                if isFethall:
                    res = c.fetchall()
            else:
                c = self.conn.cursor()
                res = c.execute(sqlStr)
                if res > 0 and isCommit:
                    c.execute('commit')
            return res
        except Exception as ex:
            actEx = ex.args[len(ex.args) - 1]
            if isinstance(ex, OperationalError) or isinstance(actEx, AssertionError) or not isinstance(actEx, Error):
                raise SqlConnBase.SqlConnException(ex)
            raise ex

    def __reConnect__(self):
        if self.conn is not None:
            try:
                if self.conn.ping():
                    return
            except:pass
            try:
                self.conn.close()
            except:pass
        self.conn = pymysql.connect(**self.sqlConfig)
        self.conn.autocommit(1)
