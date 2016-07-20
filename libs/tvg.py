# -*- coding: utf8 -*-
'''
Created on 2010-9-28

@author: chinple
'''
from libs.parser import JsonParser
import codecs
import os

class TValueGroup:
    _parser = JsonParser()
    def __init__(self, groupSource, isTValue=False, typeWord='t', valueWord='v', isProp=False, isFileSoruce=False, isDeepClone=False):
        tgs = groupSource.__class__.__name__

        if tgs == 'TValueGroup':
            groupSource = groupSource.__prop__

        self.isTvalue = isTValue
        self.tWord = typeWord
        self.vWord = valueWord
        self.propConfig = {} if isProp else None
        self.load(groupSource, isDeepClone)

    def load(self, groupSource, isDeepClone=False):
        if (isinstance(groupSource, str) or isinstance(groupSource, unicode)) and os.path.exists(groupSource):
            if groupSource.endswith("xml"):
                return self._parser.xmlToDict(groupSource)
            elif groupSource.endswith("csv"):
                return self._parser.csvToDict(groupSource)
            else:
                with codecs.open(groupSource, 'r') as jsonFile:
                    groupSource = jsonFile.read()
                
        self.__prop__ = self._parser.toDict(groupSource, isDeepClone)

    def __getitem__(self, typeKey, isValue=True):
        tempItem = self.__prop__[typeKey]

        if isValue and self.isTvalue:
            try:
                return tempItem[self.vWord]
            except:pass
        return tempItem

    def __delitem__(self, typeKey):
        self.__prop__.__delitem__(typeKey)

    def __setitem__(self, typeKey, value):
        self.__prop__[typeKey] = value

    def __len__(self):
        return len(self.__prop__)

    def __repr__(self):
        return str(self)

    def __str__(self, isJsonFormat=True):
        if isJsonFormat:
            return self._parser.toStr(self.__prop__)
        else:
            return self.__prop__.__str__()

    def __contains__(self, typeKey):
        return self.__prop__.__contains__(typeKey)

    def append(self, value):
        self.__prop__.append(value)

    def keys(self):
        return self.__prop__.keys()

    def getType(self, typeKey):
        tempItem = self.__prop__[typeKey]

        if self.isTvalue and ((type(tempItem) is dict and tempItem.__contains__(self.vWord)) 
                or hasattr(tempItem, self.tWord)):
            return tempItem[self.tWord]

        return None

    def getInt(self, typeKey):
        return int(self[typeKey])

    def getBool(self, typeKey):
        return self[typeKey].lower() == "true"

    def tryGet(self, typeKey, defVal):
        try:
            return self[typeKey]
        except:
            if self.propConfig != None:
                self.propConfig[typeKey] = defVal
            return defVal

    def toFormatString(self, tvValueHandler=None, seperator=";", props=[]):
        tempProp = []
        if(len(props) == 0):
            tempProp = self.keys()
        else:
            tempProp = props
        countProp = 0
        propLen = len(tempProp)
        outputStr = ""
        for tType in tempProp:
            countProp += 1
            if tvValueHandler != None:
                tempStr = tvValueHandler(tType, self[tType])
                if tempStr == None:
                    continue
            else:
                tempStr = '%s:%s' % (tType, self[tType])
            if countProp <= propLen and outputStr != "":
                outputStr += seperator
            outputStr += tempStr

        return outputStr

    def toXml(self, rootName="Properties"):
        from libs.xml import XmlDataGenerator
        xmlTvg = XmlDataGenerator([{'name':rootName, 'findex':-1}, {'name':'Property', 'findex':0}])
        for tValue in self.keys():
            xmlTvg.addElement("Property", name=tValue, value=self[tValue])
        return xmlTvg

    def getValByCondition(self, condHandle=lambda val, index:True, valHandle=lambda val, index:True, existFound=True, maxRange=100):
        vals = None if existFound else []
        for index in range(0, maxRange):
            try:
                if condHandle(self, index):
                    if existFound:
                        return valHandle(self, index)
                    else:
                        vals.append(valHandle(self, index))
            except:
                break
        return vals
    def saveTo(self, path):
        with codecs.open(path, "w", encoding="utf-8") as f:
            f.writelines(str(self))
