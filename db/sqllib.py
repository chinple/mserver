# -*- coding: utf8 -*-
'''
Created on 2012-5-4

@author: chinple
'''
import thread
from random import randint


class SqlConnBase:

    class SqlConnException(Exception):
        pass

    def __init__(self, sqlConfig, connid):
        self.sqlConfig = sqlConfig
        self.connid = connid
        self.conn = None
        self.isFree = True

        self._connLock = thread.allocate_lock()

    def __executeSql__(self, sqlStr, isSelect=True, isFethall=True, isCommit=True, dbName=None):
        pass

    def __reConnect__(self):
        pass

    def lockConn(self):
        self._connLock.acquire()
        self.isFree = False

    def unLockConn(self):
        try:
            self._connLock.release()
        finally:
            self.isFree = True

    def __str__(self):
        return "%s: %s" % (self.connid, self.isFree)


class SqlConnFactory:
    
    def __init__(self):
        self.conns = []

    def isInited(self):
        return len(self.conns) > 0

    def setSqlclass(self, sqlConnClass, sqlConfig, maxConns=10):
        if sqlConnClass is None:return
        self.nowConnId, self.maxConns = 0, maxConns
        self.conns = []
        for connid in range(maxConns):
            sqlConn = sqlConnClass(sqlConfig, connid)
            sqlConn.__reConnect__()
            self.conns.append(sqlConn)

    def __getConn(self):
        conn = None
        for i in range(0, self.maxConns):
            nowConnId = (self.nowConnId + i) % self.maxConns
            nowConn = self.conns[nowConnId]
            if nowConn.isFree:
                nowConn.lockConn()
                self.nowConnId = nowConnId
                conn = nowConn
                break
        if conn is None:
            nowConnId = randint(0, self.maxConns) % self.maxConns
            self.nowConnId = nowConnId
            conn = self.conns[nowConnId]
            conn.lockConn()
        return conn

    def executeSql(self, sqlStr, isSelect=True, isFethall=True, isCommit=True, dbName=None):
        sqlConn = self.__getConn()
        try:
            return sqlConn.__executeSql__(sqlStr, isSelect, isFethall, isCommit, dbName)
        except SqlConnBase.SqlConnException:
            sqlConn.__reConnect__()
            return sqlConn.__executeSql__(sqlStr, isSelect, isFethall, isCommit, dbName)
        finally:
            sqlConn.unLockConn()

    def getSql(self, opTable, opType=0, isDict=False, fieldDesp="*"):
        return Sql(self, opTable, opType, isDict, fieldDesp)


def _2sqlVal(v):
    return str(v).replace("'", "''").replace("\\", "\\\\")


def _2sqlInval(vs):
    vsj = []
    for v in vs:
        vsj.append(_2sqlVal(v))
    return tuple(vsj)


class Sql:

    def __init__(self, connFactory, opTable, opType=0, isDict=False, fieldDesp="*"):
        self.connFactory = connFactory
        self.opTable = opTable
        self.opType = opType
        self.isDict = isDict

        self.where = []
        self.names = []
        self.values = []
        self.orders = ""
        self.groups = ""
        self.subCondStart = -1
        self.fieldDesp = fieldDesp
        self.limit = None

    select = 0
    insert = 1
    update = 2
    delete = 3
    replace = 4

    @staticmethod
    def isEmpty(tStr):
        if tStr == None or tStr == "":
            return True
        return False

    def execute(self, isFethall=True, isCommit=True):
        sqlStr = str(self)
        return self.connFactory.executeSql(sqlStr, self.opType == Sql.select, isFethall, isCommit)

    def __str__(self):
        _cond = " ".join(self.where)
        _sql = ""
        if _cond != "":
            _cond = "WHERE " + _cond
        if self.opType == Sql.select:
            _cond += self.groups + self.orders
            _sql = "SELECT %s FROM %s %s %s" % (self.fieldDesp, self.opTable, _cond, ("limit %s" % self.limit) if self.limit != None else "")
        elif self.opType == Sql.insert:
            _sql = "INSERT INTO %s(%s) VALUES(%s)" % (self.opTable,
                ((", %s" * len(self.names)) % tuple(self.names))[1:], ((", '%s'" * len(self.values)) % tuple(self.values))[1:])
        elif self.opType == Sql.update:
            setSql = (", %s ='%%s'" * len(self.names)) % tuple(self.names)
            _sql = "UPDATE %s SET %s %s" % (self.opTable, setSql[1:] % tuple(self.values), _cond)
        elif self.opType == Sql.delete:
            _sql = "DELETE FROM %s %s" % (self.opTable, _cond)
        elif self.opType == Sql.replace:
            _sql = "REPLACE INTO %s(%s) VALUES%s" % (self.opTable,
                ((", %s" * len(self.names)) % tuple(self.names))[1:], tuple(self.values))
        return _sql

    def appendWhere(self, name, val, cond="=", isAnd=True, isRemoveEmpty=True, isYesCond=True):
        if val is not None:
            if name[0] != '`': name = '`%s`' % name
            if isRemoveEmpty and val == "":
                return self
            isInCond, tv = cond == 'in', type(val)
            if isInCond:
                if tv == str or tv == unicode:
                    val = _2sqlVal(val)
                    val = tuple(val.split(','))
                else:
                    val = _2sqlInval(val)
                cond = 'in'
                if len(val) == 0:
                    return self
                elif len(val) == 1:
                    isInCond, cond, val = False, "=", val[0]
                else:
                    val = '(%s)' % (((", '%s'" * len(val)) % val)[1:])
            else:
                val = _2sqlVal(val)
            if len(self.where) > 0:
                self.where.append("and" if isAnd else "or")
            self.where.append("%s %s %s " % (name, "" if isYesCond else " not", cond))
            if isInCond or tv == int:
                self.where.append("%s" % str(val))
            else:
                self.where.append("'%s'" % str(val))
        return self

    def appendWhereByJson(self, jobj, cond="=", isAnd=True, isRemoveEmpty=True, isYesCond=True):
        for k in jobj:
            self.appendWhere(k, jobj[k], cond, isAnd, isRemoveEmpty, isYesCond)

    def orderBy(self, names):
        if not Sql.isEmpty(names):
            self.orders = " order by %s " % names
        return self

    def groupBy(self, names):
        if not Sql.isEmpty(names):
            self.groups = " group by %s " % names
        return self

    def startCondition(self):
        self.subCondStart = len(self.where)
        return self

    def endCondition(self, isAnd=True):
        if self.subCondStart >= 0:
            if len(self.where) > self.subCondStart:
                if self.subCondStart == 0:
                    self.where[self.subCondStart] = "(" + self.where[self.subCondStart]
                else:
                    self.where[self.subCondStart] = ("and" if isAnd else "or") + "("
                self.where.append(") ")
            self.subCondStart = -1
        return self

    def appendCondition(self, cond, args, isAnd=True):
        if cond is not None:
            if len(self.where) > 0:
                self.where.append("and" if isAnd else "or")
            self.where.append(cond % (_2sqlInval(args)))
        return self

    def appendLogicCondition(self, name, value, isLike):
    # name = aaa+bbb&ccc|ddd , means: name = aaa and name = bbb and name = ccc or name = ddd
        if not self.isEmpty(value):
            self.startCondition()
            value, s, isAnd = value + "&", 0, True
            for e in range(len(value)):
                if e > (s + 1) and '+&|'.find(value[e]) >= 0:
                    v = value[s:e].strip()
                    if not self.isEmpty(v):
                        ci = 2 if isLike else 0
                        if v[0] == '!':
                            ci += 1
                            v = v[1:]
                            if self.isEmpty(v):continue
                        if isLike: v = "%" + v + "%"
                        self.appendWhere(name, v, ['=', '!=', 'like', 'not like'][ci], isAnd)
                    s, isAnd = e + 1, value[e] == '&' or value[e] == '+'
            self.endCondition()
        return self
    
    def appendLikeCondition(self, value, isAnd, *name):
        if not self.isEmpty(value):
            value = "%" + value + "%"
            self.startCondition()
            for n in name:
                self.appendWhere(n, value, 'like', isAnd)
            self.endCondition()
        return self

    def appendValue(self, name, val):
        if val != None:
            self.names.append(name if name[0] == "`" else ("`%s`" % name))
            self.values.append(_2sqlVal(val))
        return self

    def appendValueByJson(self, jobj):
        for k in jobj:
            self.appendValue(k, jobj[k])
