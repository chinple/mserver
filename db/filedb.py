'''
Created on 2016-2-25

@author: chinple
'''
from libs.parser import toJsonObj, toJsonStr
import codecs

class FileDataBase:
    # record size must be less than 10000, otherwise search may be slow
    def __init__(self, dbFolder, fileFormat="%s.json", keyDefines={'key1':'json|equal'}, isSignleKey=True):
        self.dbFileFormat = "%s/%s" % (dbFolder, fileFormat)
        self.dbBuffer = {}
        self.keyDefines = keyDefines
        self.isSignleKey = isSignleKey

    def __getRecords(self, fname):
        try:
            records = self.dbBuffer[fname]
        except:
            dbFile = self.dbFileFormat % fname
            try:
                records = toJsonObj(open(dbFile).read())
            except:
                records = []
            self.dbBuffer[fname] = records
        return records

    def saveRecord(self, fname, record, isUpdate=False, isFlush=False):
        keyCond = {}
        for k in self.keyDefines:
            try:
                keyCond[k] = record[k]
            except:
                return False

        isNeedAdd = True
        if len(keyCond) > 0:
            rs = self.getRecord(fname, keyCond)
            if len(rs) > 0:
                if not isUpdate:
                    return False
                r = rs[0]
                for k in record:
                    r[k] = record[k]
                isNeedAdd = False

        if isNeedAdd:
            self.__getRecords(fname).append(record)

        if isFlush:
            self.flushRecord(fname)
        return True

    def flushRecord(self, fname):
        with codecs.open(self.dbFileFormat % fname, "w", encoding="utf-8") as df:
            df.write(toJsonStr(self.__getRecords(fname)))

    def getRecord(self, fname, keyCond=None):
        orecords = self.__getRecords(fname)
        records = []
        if keyCond is None:
            records = orecords
        else:
            for r in orecords:
                if self.__isRecordEqual(keyCond, r):
                    records.append(r)
        return records

    def removeRecord(self, fname, keyCond=None):
        if keyCond is None:
            return False
        orecords = self.__getRecords(fname)
        for k in self.getRecord(fname, keyCond):
            orecords.remove(k)
        return False

    def __isKeyEqual(self, key, expVal, val):
        isJson = self.keyDefines.__contains__(key) and self.keyDefines[key] == "json"
        if isJson:
            for k in expVal:
                try:
                    if expVal[k] != val[k]:
                        return False
                except:
                    return False
            return True
        else:
            return expVal == val

    def __isRecordEqual(self, expRecord, record):
        equalCount = 0
        for k in expRecord:
            try:
                if self.__isKeyEqual(k, expRecord[k], record[k]):
                    equalCount += 1
            except:pass
        expCount = len(expRecord)
        return expCount == 0 or (self.isSignleKey and equalCount > 0)\
            or (not self.isSignleKey and equalCount == expCount)
