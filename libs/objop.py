'''
Created on 2010-11-8

@author: chinple
'''
from random import randint
import codecs
import os
from optparse import OptionParser
import re


class ObjOperation:

    @staticmethod
    def tryGetVal(obj, key, defValue):
        try:
            return obj[key]
        except:
            return defValue

    @staticmethod
    def traversalObj(v, h, p=None, k=None):
        t = type(v)
        if p is None:
            pf = "%s"
        else:
            pf = "%s.%%s" % p
        if t == list:
            for k in range(len(v)):
                ObjOperation.traversalObj(v[k], h, pf % k, k)
        elif t == dict:
            for k in v:
                ObjOperation.traversalObj(v[k], h, pf % k, k)
        elif k is not None:
            h(p, k, v)

    @staticmethod
    def findValByCondition(obj, condHandle=lambda val, index:True, valHandle=lambda val, index:True, existFound=True, maxRange=100):
        vals = None if existFound else []
        for index in range(0, maxRange):
            try:
                if condHandle(obj, index):
                    if existFound:
                        return valHandle(obj, index)
                    else:
                        vals.append(valHandle(obj, index))
            except:
                break
        return vals

    @staticmethod
    def jsonFormat(s, j, isUsePath=False):
        js = {"s":s}

        def fh(p, k, v):
            if v is not None:
                js['s'] = js['s'].replace("{%s}" % (p if isUsePath else k), str(v))

        ObjOperation.traversalObj(j, fh)
        return js['s']

    @staticmethod
    def jsonEqual(expVal, actVal, isAddEqInfo=True, cmpHandler=lambda val1, val2, valKey:val1 == val2,
            cmpFormat="\n%s\t<%s>  %s : %s", isCmpHandler=lambda key, keyPath: True, keyInfo=""):
        cmpRes, cmpInfo, expType, actType = 0, "", type(expVal), type(actVal)

        if not cmpHandler(expType , actType, None) and expType != float and expType != int and expType != str and expType != unicode:
            cmpInfo = cmpFormat % ("!=Type", keyInfo, expVal, actVal)
            cmpRes += 1
        elif expType == dict or expType == list or expType == tuple:
            isList = expType != dict
            if isList:
                expKeys = range(0, len(expVal))
                actKeys = list(range(0, len(actVal)))
            else:
                expKeys = expVal.keys()
                actKeys = list(actVal.keys())

            for cmpKey in expKeys:
                keyPath = "%s.%s" % (keyInfo, cmpKey)
                if not isCmpHandler(cmpKey, keyPath):
                    continue
                try:
                    actKeys.remove(cmpKey)
                    tempRes, tempInfo = ObjOperation.jsonEqual(expVal[cmpKey], actVal[cmpKey], isAddEqInfo,
                        cmpHandler, cmpFormat, isCmpHandler, keyPath)
                    cmpRes += tempRes
                    cmpInfo += tempInfo
                except:
                    if not cmpHandler(True, False, keyPath):
                        cmpInfo += cmpFormat % ("-Key", keyPath, expVal[cmpKey], "")
                        cmpRes += 100
            if len(actKeys) > 0:
                cmpInfo += cmpFormat % ("+Key", keyInfo, "", actKeys)
                cmpRes += 10000
       
        else:
            if cmpHandler(expVal , actVal, keyInfo):
                if isAddEqInfo:
                    cmpInfo = cmpFormat % ("==", keyInfo, expVal, actVal)
            else:
                cmpInfo = cmpFormat % ("!=", keyInfo, expVal, actVal)
                cmpRes += 1
        return cmpRes, cmpInfo
    

class FileOperation:

    @staticmethod
    def getFileEncoding(filePath):
        sourceFormats = [ 'utf-8', 'gbk', 'ascii', 'iso-8859-1']
        for encode in sourceFormats: 
            try:
                with codecs.open(filePath, 'r', encode) as testFile:
                    testFile.read()
                return encode
            except UnicodeDecodeError: 
                pass
        return "gbk"

    @staticmethod
    def openFile(filePath, mode='r', encoding=None):
        return codecs.open(filePath, mode, FileOperation.getFileEncoding(filePath) if encoding is None else encoding)

    @staticmethod
    def filterFileContent(filePath, lineHandle=None, lineReg=None):
        fh = FileOperation.OpenFile(filePath)
        while True:
            lStr = fh.readline()
            if lStr == "":
                break
            if lineReg == None:
                lineHandle(lStr)
            else:
                lGroup = re.match(lineReg, lStr)
                if lGroup != None:
                    lineHandle(lGroup.groups())

    @staticmethod
    def mergeFiles(mergeToFilePath, *mergeFilePaths):
        mergTo = open(mergeToFilePath, "wb")
        for mergeFilePath in mergeFilePaths:
            if os.path.exists(mergeFilePath):
                with open(mergeFilePath, "rb") as  mergeFrom:
                    while True:
                        logLine = mergeFrom.readline()
                        if logLine == b'':
                            break
                        mergTo.write(logLine)
        mergTo.close()

    @staticmethod
    def getSubFiles(fpath, ftype=None, findSubFile=True):
        subFiles = []
        fpath = str(fpath).replace("\\", "/")
        if not os.path.isdir(fpath):
            subFiles.append(fpath)
            return subFiles

        if not fpath.endswith("/"):
            fpath = fpath + "/"
    
        for fname in os.listdir(fpath):
            fname = fpath + fname
            if os.path.isdir(fname):
                if findSubFile:
                    subFiles = subFiles + FileOperation.getSubFiles(fname + "/", ftype)
            elif ftype == None or fname.endswith(ftype):
                subFiles.append(fname)
        return subFiles

    @staticmethod
    def splitPathName(filePath):
        ci = -1
        for i in range(0, len(filePath)):
            c = filePath[i]
            if c == "/" or c == "\\":
                ci = i
        ci += 1
        return filePath[0:ci], filePath[ci:]


class StrOperation:

    @staticmethod
    def splitStr(target, sep=",", quote=None):
        ss = []
        si = 0
        l = len(target)
        isQuote = False
        for i in range(l):
            c = target[i]
            if quote != None:
                if c == quote:
                    if isQuote:
                        ss.append(target[si:i])
                        si = i + 1
                        isQuote = False
                    else:
                        si = i + 1
                        isQuote = True
                    continue
            if c == sep and not isQuote:
                if si == i:
                    si = i + 1
                    continue
                ss.append(target[si:i])
                si = i + 1
        if si < l:
            ss.append(target[si:l])
        return ss

    @staticmethod
    def lowerStr(lwStr, middleIndex=1, startIndex=0):
        if lwStr == None:
            return ""
        return "%s%s" % (lwStr[startIndex:middleIndex].lower(), lwStr[middleIndex:])

    @staticmethod
    def getRandomString(length, strType="password | low| upper |letter | number", targetSeed=None, separator=''):
        sampleStr = "1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ~!@#$%^&*()_+[]\\{}|;':\",./<>?";
        minSelector = 10
        maxSelector = 61

        if targetSeed != None: minSelector = 0; maxSelector = len(targetSeed) - 1
        elif strType == "number": minSelector = 0; maxSelector = 9
        elif strType == "low": minSelector = 10; maxSelector = 35
        elif strType == "upper": minSelector = 36; maxSelector = 61
        elif strType == "letter": minSelector = 10; maxSelector = 61
        elif strType == "password": minSelector = 0; maxSelector = 90
        # Need To Use StringIO
        result = ""
        hasSeparator = separator != ''
        strLen = 0
        while strLen < length:
            strLen += 1
            if hasSeparator and result != '':
                result += separator
            selector = randint(minSelector, maxSelector)
            if targetSeed == None:
                result += sampleStr[selector]
            else:
                result += targetSeed[selector]
        return result


class ArgsOperation:

    @staticmethod
    def getJsonArgs(jsonArg, argNames, tupleArg, defArg=None):
        argIndex = 0
        for argName in argNames:
            try:
                jsonArg[argName] = tupleArg[argIndex]
                argIndex += 1
            except:break

        argNameIndex = len(argNames)
        if defArg != None:    
            argIndex = argNameIndex - len(tupleArg)
            if argIndex > 0:
                for defArgIndex in range(len(defArg) - 1, len(defArg) - 1 - argIndex, -1):
                    argNameIndex -= 1
                    argName = argNames[argNameIndex]
                    if not jsonArg.__contains__(argName): 
                        jsonArg[argName] = defArg[defArgIndex]

        return jsonArg

    @staticmethod
    def getTupleArgs(jsonArg, argNames, tupleArg, defArg=None):
        if jsonArg == None or len(jsonArg) == 0:
            return tupleArg
        else:
            listArgs = []
            ArgsOperation.GetJsonArgs(jsonArg, argNames, tupleArg, defArg)
            for argIndex in range(len(jsonArg)):
                listArgs.append(jsonArg[argNames[argIndex]])

            return tuple(listArgs)

    @staticmethod
    def parseArgs(args, mustArgs=[], jsonParser=None, *argFormat):
        '''
    simpleName/storeName, helpInfo, defaultValue, storeType

Example:
    mtArgs, parseMsg, isSuccess = DataOperation.ParseArg = 
(runArgs, [], TValueGroup.ToJsonMap, (name, helpInfo, defaultValue, storeType))

    '''
        parser = OptionParser()
        listArgs = []
        boolArgs = []
        intArgs = []
        propArgs = []
        argList = []
        for argf in argFormat:
            argIndex = 0
            soname = argf[0]
            if len(soname) == 1 and soname != '-':
                argIndex += 1
                soname = "-%s" % soname
            else:
                soname = ""
            oname = argf[argIndex]
            argIndex += 1
            ohelp = argf[argIndex]

            if oname.__contains__("-"):
                parser.set_usage(ohelp)
                continue

            argList.append(oname)
            argIndex += 1
            odef = argf[argIndex] if len(argf) > argIndex else ""
            argIndex += 1
            otype = argf[argIndex] if len(argf) > argIndex else None
            ohelp = "%s. %s%s" % (ohelp, (otype if otype != None else "string").upper(), (", default %s" % odef) if odef != "" else "")
            oaction = None
            if otype == "int" or otype == "float":
                intArgs.append(oname)
            elif otype == "list":
                listArgs.append(oname)
                otype = None
                oaction = "append"
            elif otype == "prop":
                propArgs.append(oname)
                otype = None
                oaction = "append"
            elif otype == "bool":
                boolArgs.append(oname)
                otype = None
                odef = "true" == odef or odef == True
                oaction = "store_true"
            parser.add_option(soname, "--%s" % oname, dest=oname, type=otype, action=oaction, help=ohelp, default=odef)
    
        if len(args) == 0:
            args.append("-h")

        isParsed = False
        if type(args) == dict:
            jsonVal = args
            isParsed = True
        elif jsonParser != None and len(args) > 0 and os.path.exists(args[0]):
            jsonVal = jsonParser(args[0])
            isParsed = True
        if isParsed:
            parseValue, leftArgs = parser.parse_args([])
            for oname in argList:
                try:
                    oval = jsonVal[oname]
                except:continue
                if listArgs.__contains__(oname):
                    if type(oval) != list:
                        oval = [oval]
                elif boolArgs.__contains__(oname):
                    oval = oval == True or oval == "true"
                elif intArgs.__contains__(oname):
                    if oval.__contains__("."):
                        oval = float(oval)
                    else:
                        oval = int(oval)
                parseValue.__dict__[oname] = oval
        else:
            parseValue, leftArgs = parser.parse_args(args)

        for oname in propArgs:
            pval = {}
            for propKeyVal in parseValue.__dict__[oname]:
                try:
                    pIndex = propKeyVal.index('=')
                    pval[propKeyVal[0:pIndex]] = propKeyVal[pIndex + 1:]
                except:pass
            parseValue.__dict__[oname] = pval

        isSuccess = True
        parseMsg = ""
        for mustArg in mustArgs:
            if  parseValue.__dict__[mustArg] == "":
                if parseMsg == "":
                    parseMsg = "\nMiss arguments: --%s" % mustArg
                else:
                    parseMsg += ", --%s" % mustArg
                isSuccess = False
    
        if not isSuccess:
            parseMsg = parser.format_help() + parseMsg
        elif len(leftArgs) > 0:
            parseMsg += "\nInvalid argument: %s" % leftArgs
        else:
            for oname in argList:
                oval = parseValue.__dict__[oname]
                if type(oval) == list:
                    for loval in oval:
                        parseMsg += ' --%s "%s"' % (oname, loval)
                elif type(oval) == dict:
                    for prop in oval:
                        parseMsg += ' --%s "%s=%s"' % (oname, prop, oval[prop])
                elif oval != "" and oval != False:
                    parseMsg += ' --%s "%s"' % (oname, oval)

        del parser, listArgs, boolArgs, intArgs, propArgs, argList
        return parseValue, parseMsg, isSuccess


class ArrayOperation:

    @staticmethod
    def findStepToArray(byIndex):
        ajustStep = []
        lenArray = len(byIndex)
        orderArray = list(range(lenArray))
        
        sIndex = -1
        sele = sIndex
    
        while True:
            if sele == sIndex:
                sIndex += 1
                if sIndex >= lenArray:
                    break
                else:
                    sele = orderArray[sIndex]
                    if sele == byIndex[sIndex]:
                        sele = sIndex
                        continue
                    ajustStep.append((-1, sIndex))
        
            ajustStep.append((byIndex[sele], sele))
            orderArray[sele] = byIndex[sele]
            sele = orderArray[sele]
    
        return ajustStep, orderArray

    @staticmethod
    def adjustArrayByStep(aryData, adjSteps):
        tIndex = None
        tData = None
        for adjStep in adjSteps:
            fIndex = adjStep[0]
            if fIndex < 0:
                tIndex = adjStep[1]
                tData = aryData[tIndex]
            else:
                aryData[adjStep[1]] = tData if fIndex == tIndex else aryData[fIndex]
        return aryData


class NumberOperation:

    @staticmethod
    def roundNum(floatNum, pointCount=1, isRound=True):
        baseInt = pow(10, pointCount)
        return int(floatNum * baseInt + (0.5 if isRound else 0)) / baseInt
