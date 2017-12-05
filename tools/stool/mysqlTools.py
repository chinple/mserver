'''
Created on 2016-9-21

@author: chinple
'''
from cserver import cloudModule
from db.sqltool import SqlOpTool, BasicSqlTool

@cloudModule(jwhere={"t":'textarea'}, jvalue={"t":'textarea'}, where={"t":'textarea'}, whereArgs={"t":'textarea'})
class BillSqlTool(BasicSqlTool):
    pass

@cloudModule(jwhere={"t":'textarea'}, jvalue={"t":'textarea'}, where={"t":'textarea'}, whereArgs={"t":'textarea'})
class OnlineSqlTool(SqlOpTool):
    def __init__(self, isCheckUpdate=True, isSupportDelete=False, isSupportAnySql=False, dbstoreName="dbstore"):
        SqlOpTool.__init__(self, True, False, False, "onlinedb")

    def onlineAddConn(self, configName, host, port, user, passwd):
        return SqlOpTool.__addConn__(self, configName, host, port, user, passwd).keys()

    def onlineExecuteSql(self, operation="show", fields="*", table="db", dbName="",
            where="1=1", whereArgs="", affectRows=100, dbConfig="local"):
        return SqlOpTool.__executeSql__(self, operation, fields, table, dbName, where, whereArgs, affectRows, dbConfig)

if __name__ == "__main__":
    from cserver import servering
    servering(" -p 8080")
