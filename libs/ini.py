'''
Created on 2015-10-18

@author: chinple
'''
import os

class IniParser:
# ini example:
#
# [queue]
# msgMaxQueueSize = 512
# msgMaxMsgSize   = 200
# maxTopicSize    = 100

    def __init__(self, readLineHandler, addSectionHandler):
        self.nextLineHandle = readLineHandler
        self._stepHandle_ = addSectionHandler
        self._initSection_()
        self._initEle_()

    def _initSection_(self):
        self.sectionName = None
        self.sectionValues = []
    def _initEle_(self):
        self.eleName = None
        self.eleValue = ""

    def _addSection_(self):
        if self.sectionName and self.sectionName != "":
            self._addEle_()
            self._stepHandle_(self.sectionName, self.sectionValues)
            self._initSection_()
    def _addEle_(self):
        if self.eleName:
            v = self.eleValue.strip()
            self.sectionValues.append((self.eleName, v[1:] if v.startswith("\\ ") else v))
            self._initEle_()
    def parse(self):
        while True:
            cl = self.nextLineHandle()
            if cl == "":
                break
            lcl = cl.lstrip()
            lclLen = len(lcl)
            if(lclLen == 0):
                self.eleValue += cl
                continue
            c0 = lcl[0]
            if c0 == '#' or c0 == ";":
                continue
            elif c0 == '[':
                self._addSection_()
                lcl = lcl.rstrip()
                self.sectionName = lcl[1:len(lcl) - 1]
            else:
                isOldEle = True
                isNotSep = False
                for i in range(0, lclLen):
                    c = lcl[i]
                    if c == "=":
                        if isNotSep:
                            lcl = lcl.replace("\\=", "=")
                        else:
                            isOldEle = False
                            self._addEle_()
                            self.eleName = lcl[0:i].rstrip()
                            self.eleValue = lcl[i + 1:]
                        break
                    elif c == '\\':
                        isNotSep = True
                    else:
                        isNotSep = False
                if isOldEle:
                    self.eleValue += lcl
        self._addSection_()

class IniConfigure:
    class NoConfigException(Exception):
        pass
    def __init__(self, iniPath=""):
        self.sections = {}
        self.load(iniPath)

    def load(self, iniPath):
        if os.path.exists(iniPath):
            import codecs
            with codecs.open(iniPath, encoding="utf-8") as iniFile:
                IniParser(lambda:iniFile.readline(), self.__addSection).parse()
            return True
        return False

    def __addSection(self, sectionName, sectionValues):
        try:
            section = self.sections[sectionName]
        except:
            section = {}
            self.sections[sectionName] = section
        for v in sectionValues:
            section[v[0]] = v[1]

    def getVal(self, section, key, default=None):
        try:
            return self.sections[section][key]
        except:
            if default is not None:
                return default
        raise IniConfigure.NoConfigException("%s.%s" % (section, key))

    def getInt(self, section, key, default=None):
        return int(self.getVal(section, key, default))

    def getFloat(self, section, key, default=None):
        return float(self.getVal(section, key, default))

    def getBool(self, section, key, default=None):
        return self.getVal(section, key, default).lower() == "true"
