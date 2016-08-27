# -*- coding: utf8 -*-
'''
Created on 2015-8-19

@author: chinple
'''

from libs.objop import StrOperation

from db.sqllib import SqlConnFactory, Sql
from db.filedb import FileDataBase

class SqlOpTool:
    def __init__(self, isCheckUpdate=True, isSupportDelete=False, isSupportAnySql=False, dbstoreName="dbstore", isMysqldb=True):
        self.conns = {}
        self.fdb = FileDataBase("./", keyDefines={"configName":"equal"})
        self.dbConfigs = {}
        self.isCheckUpdate = isCheckUpdate
        self.isSupportDelete = isSupportDelete
        self.isSupportAnySql = isSupportAnySql
        self.dbstoreName = dbstoreName
        self.isMysqldb = isMysqldb
        for r in self.fdb.getRecord(self.dbstoreName):
            self.dbConfigs[r['configName']] = r['config']

    def __addConn__(self, configName, host, port, user, passwd):
        if configName != "":
            self.dbConfigs[configName] = {'host':host, 'port':int(port), 'user':user, 'passwd':passwd, 'charset':'utf8'}
            self.fdb.saveRecord(self.dbstoreName, {'configName':configName, 'config':self.dbConfigs[configName]},
                isUpdate=True, isFlush=True)
        return self.dbConfigs

    def __getConn(self, dbConfig):
        if self.conns.__contains__(dbConfig):
            conn = self.conns[dbConfig]
        else:
            if self.isMysqldb:
                from db.mysqldb import MysqldbConn
                conn = SqlConnFactory(MysqldbConn, self.dbConfigs[dbConfig], 1)
            else:
                from db.pysql import PymysqlConn
                conn = SqlConnFactory(PymysqlConn, self.dbConfigs[dbConfig], 1)
            self.conns[dbConfig] = conn
        return conn

    def __executeSql__(self, operation="show", fields="*", table="db", dbName="",
            where="1=1", whereArgs="", affectRows=100, dbConfig="local"):
        if Sql.isEmpty(dbConfig):
            return "no db config"
        if Sql.isEmpty(dbName):dbName = None

        if Sql.isEmpty(affectRows):
            affectRows = 100
        affectRows, operationType = int(affectRows), operation[0:10].lower().strip()

        try:
            argIndex = 0
            for arg in StrOperation.splitStr(whereArgs, ",", "'"):
                where = where.replace("{%s}" % argIndex, arg)
                argIndex += 1
        except Exception as ex:
            return ("%s" % ex)

        conn = self.__getConn(dbConfig)

        if operationType == "select":
            query = "select %s from %s.%s where %s limit %s" % (fields, dbName, table, where, affectRows)
            return conn.executeSql(query, True, dbName=dbName)
        elif operationType == "update":
            if self.isCheckUpdate:
                query = "select count(1) as affectRows from %s.%s where %s " % (dbName, table, where)
                actAffectRows = conn.executeSql(query, True, dbName=dbName)[0]['affectRows']
            else:
                actAffectRows = affectRows
            if actAffectRows == affectRows:
                update = "update %s.%s set %s where %s limit %s" % (dbName, table, fields, where, affectRows)
                return conn.executeSql(update, isSelect=False, isCommit=True, dbName=dbName)
            else:
                return "Actual %s != Expect %s" % (actAffectRows, affectRows)
        elif self.isSupportDelete and operationType == "delete":
            delete = "delete from %s.%s where %s limit %s" % (dbName, table, where, affectRows)
            return conn.executeSql(delete, isSelect=False, isCommit=True, dbName=dbName)
        elif operationType == "show":
            if Sql.isEmpty(dbName):
                return conn.executeSql("show databases", dbName=dbName)
            else:
                return conn.executeSql("show tables", dbName=dbName)
        elif self.isSupportAnySql:
            return conn.executeSql(operation, dbName=dbName)
        else:
            return "Bad operation %s" % operation
