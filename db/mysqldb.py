'''
Created on 2016-6-1

@author: chinple
'''

from db.sqllib import SqlConnBase
import MySQLdb
from _mysql_exceptions import OperationalError, InterfaceError

# rely: mysql-devel setuptools-22.0.0.tar MySQL-python-1.2.5.tar

class MysqldbConn(SqlConnBase):
# sqlConfig = {'host':host, 'port':port, 'user':user, 'passwd':passwd, 'db':db, 'charset':'utf8'}
    def __executeSql__(self, sqlStr, isSelect=True, isFethall=True, isCommit=True, dbName=None):
        try:
            if isSelect:     
                c = self.conn.cursor(MySQLdb.cursors.DictCursor if isFethall else None)
                try:
                    if dbName is not None: c.execute("use %s" % dbName)
                    res = c.execute(sqlStr)
                    if isFethall:
                        res = c.fetchall()
                finally:
                    if isFethall:
                        c.close()
                    else:
                        return c
            else:
                c = self.conn.cursor()
                if dbName is not None: c.execute("use %s" % dbName)
                res = c.execute(sqlStr)
                if res > 0 and isCommit:
                    c.execute('commit')
            return res
        except Exception as ex:
            actEx = ex.args[len(ex.args) - 1]
            if isinstance(ex, OperationalError) or isinstance(ex, InterfaceError) or isinstance(actEx, AssertionError):
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
        self.conn = MySQLdb.connect(**self.sqlConfig)
        self.conn.autocommit(1)
