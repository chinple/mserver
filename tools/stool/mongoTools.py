'''
Created on 2017-9-29

@author: chinple
'''
from libs.parser import toJsonObj
from cserver import cloudModule

@cloudModule(condition={"t":'textarea'}, addContent={"t":'textarea'})
class MongoTool:
    def __init__(self):
        self.dbs = {}

    def addMongoConn(self, key, hostport):
        host, port = hostport.split(":")
        self.dbs[key] = {'h':host, 'p':int(port), 'c':None}
        return self.dbs.keys()

    def _getConn(self, key):
        db = self.dbs[key]
        c = db['c']
        if c is None:
            from pymongo import MongoClient
            c = MongoClient(db['h'], db['p'])
            db['c'] = c
        return c

    def executeMongo(self, op="find|add|remove", key="", db="", collection="", condition="{}", addContent="{}"):
        if db == "":
            raise Exception("No database set")
        condition = toJsonObj(condition)
        conn = self._getConn(key)
        if collection == "":
            return conn[db].collection_names()

        if op == "find":
            r = conn[db][collection].find(condition)
            return list(r)
        elif op == "remove":
            return conn[db][collection].remove(condition)
        elif op == "add":
            return conn[db][collection].add(addContent)
        else:
            raise Exception("No such operation")
