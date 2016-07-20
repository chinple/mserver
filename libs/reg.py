'''
Created on 2010-11-8

@author: chinple
'''

import re
class PyRegExp:
    def __init__(self, pattern, pattonMaxlen=30720):
        self.patterns = []
        if pattern == "":
            self.patterns.append("")
        else:
            startIndex = 0
            while startIndex >= 0:
                endIndex = pattern.find("|", (startIndex + pattonMaxlen))
                self.patterns.append(pattern[startIndex if pattern[startIndex] != '|' else (startIndex + 1):endIndex if endIndex > 0 else len(pattern)])
                startIndex = endIndex
    def isMatch(self, pyStr):
        try:
            return self.match(pyStr) != None
        except:
            return False
    def match(self, pyStr):
        for pattern in self.patterns:
            mcher = re.match(pattern, pyStr)
            if mcher != None:
                return (pattern, mcher)
    def __str__(self):
        bufStr = ""
        for pStr in self.patterns:
            if bufStr != "":
                bufStr += "|"
            else:
                bufStr += pStr
        return bufStr
    def __repr__(self):
        return str(self)
