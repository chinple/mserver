'''
Created on 2010-11-8

@author: chinple
'''

from json.decoder import JSONDecoder
from json.encoder import JSONEncoder


class __ObjStrEncoder__(JSONEncoder):

    def default(self, obj):
        return str(obj)


class JsonParser:

    def __init__(self):
        self.jsDecoder = JSONDecoder()
        self.jsEncoder = __ObjStrEncoder__()
        self.encoding = "utf-8"

    def toDict(self, targetStr, isDeepClone=False):

        if isinstance(targetStr, str) or isinstance(targetStr, unicode):
            try:
                return self.jsDecoder.decode(targetStr)
            except:pass
            raise ValueError('Bad JSON "%s"' % targetStr)
        else:
            import copy
            return copy.deepcopy(targetStr) if isDeepClone else targetStr
            
    def csvToDict(self, filepath, encoding="utf-8", isToDict=True):
        csvData = []
        if isToDict:
            heads = None
        import codecs
        with codecs.open(filepath, 'r', encoding=encoding) as dataFile:
            import csv
            csvReader = csv.reader(dataFile, quoting=csv.QUOTE_MINIMAL)
            for row in csvReader:
                if isToDict:
                    if heads == None:
                        heads = row
                    else:
                        rj = {}
                        for i in range(0, len(heads)):
                            try:
                                rj[heads[i]] = row[i]
                            except:pass
                        csvData.append(rj)
                else:
                    csvData.append(row)
        return csvData

    def xmlToDict(self, filepath, propMark="Property", nameMark="name", valueMark="value", typeMark="type", hasList=False):
        from xml.dom.minidom import parse
        doml = parse(filepath)
        jsonMap = {}
        for node in doml.getElementsByTagName(propMark):
            tvgN = node.getAttribute(nameMark)
            tvgT = node.getAttribute(typeMark)
            tvgV = node.getAttribute(valueMark)
            if tvgT != "":
                tvgV = {"v":tvgV, "t":tvgT}
            if tvgN != "":
                if hasList and jsonMap.__contains__(tvgN):
                    listVal = jsonMap[tvgN]
                    if type(listVal) == list:
                        listVal.append(tvgV)
                    else:
                        jsonMap[tvgN] = [listVal, tvgV]
                else:
                    jsonMap[tvgN] = tvgV

        return jsonMap
    
    def toStr(self, obj):
        return self.jsEncoder.encode(obj)


_parser = JsonParser()


def toJsonStr(obj):
    if isinstance(obj, dict) or isinstance(obj, list) or isinstance(obj, tuple):
        return _parser.toStr(obj)
    return obj


def toJsonObj(jsonStr, isDeepClone=False):
    return _parser.toDict(jsonStr, isDeepClone)
