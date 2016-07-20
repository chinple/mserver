'''
Created on 2010-11-8

@author: chinple
'''
import codecs
import os

class XmlOperation:
    @staticmethod
    def xpathToJson(xpath, tempUiLocator="{'Name':'', 'Index':1, 'Handle':0}"):
        baseuiLocator = {}
        lastuiLocator = baseuiLocator
    
        uiLocator = None
        csName = ""
        propName = ""
        propValue = ""

        isClass = True
        isPropName = True
        isNotVal = True
        isNotChangeVal = True
        for c in (xpath + "/"):
            if isNotVal:
                if c == '/':
                    hasProp = propName != ""
                    if uiLocator == None:
                        if csName != "" or hasProp:
                            uiLocator = eval(tempUiLocator)
                        if hasProp:
                            if isPropName:
                                uiLocator['Index'] = propName
                            else:
                                uiLocator[propName] = None
                    elif hasProp:
                        uiLocator[propName] = None

                    if uiLocator != None:
                        if csName != "":
                            uiLocator['ClassName'] = csName
                        try:
                            uiLocator['Index'] = int(uiLocator['Index'])
                        except:
                            raise Exception("Index invalid: %s" % xpath)
                        lastuiLocator["Child"] = uiLocator
                        lastuiLocator = uiLocator

                    uiLocator = None
                    csName = ""
                    propName = ""
                    propValue = ""
                    isClass = True
                    isPropName = True
                    isNotVal = True
                    continue
                elif c == '@':
                    if propName != "":
                        if uiLocator == None:
                            uiLocator = eval(tempUiLocator)
                        uiLocator[propName] = None
                    propName = ""
                    propValue = ""
                    isPropName = True
                    continue
                elif c == '=':
                    isPropName = False
                    continue
                elif c == '[':
                    propName = ""
                    propValue = ""
                    isClass = False
                    continue
                elif c == ']':
                    continue

            if isNotChangeVal:
                if c == '\'':
                    isNotVal = not isNotVal
                    if isNotVal and propName != "":
                        if uiLocator == None:
                            uiLocator = eval(tempUiLocator)
                        uiLocator[propName] = propValue
                        propName = ""
                    continue
                if c == '\\':
                    isNotChangeVal = False
                    continue
            else:
                isNotChangeVal = True

            if isClass:
                if c != ' ':
                    csName += c
            elif isPropName:
                if c != ' ':
                    propName += c
            else:
                propValue += c

        if {} == baseuiLocator:
            return {}
        return baseuiLocator["Child"]

    @staticmethod
    def jsonToXpath(uiPath, addBaseName=False, globalFirst=False, *showProps):

        if uiPath == {}:
            return ""

        xpath = ""
        isBase = True
        csName = ""
        uiName = ""
        while uiPath != None:
            uiName = uiPath['Name']
            uiIndex = uiPath['Index']

            tempXpath = ""
            for showProp in showProps:
                try:
                    propVal = uiPath[showProp]
                except:continue
                if propVal == None:
                    tempXpath += "@%s=%s " % (showProp, propVal)
                elif propVal != '' and propVal != 0:
                    tempXpath += "@%s='%s' " % (showProp, propVal)
    
            if isBase:
                if addBaseName:
                    xpath += str(uiName) + ":\n"
                try:
                    csName = uiPath['ClassName']
                except:
                    csName = ""
                xpath += "  //%s" % csName
                isBase = False
            else:
                xpath += "/"
                if uiName == None:
                    tempXpath += "@Name=%s" % uiName
                elif uiName != "":
                    tempXpath += "@Name='%s'" % uiName
                if tempXpath == "":
                    tempXpath = uiIndex
                elif uiIndex != 1:
                    tempXpath += " @Index='%s'" % uiIndex
    
            if tempXpath != "":
                xpath += "[%s]" % tempXpath
            try:
                uiPath = uiPath['Child']
            except:
                break
        if globalFirst and csName != "" and uiName != "":
            return "  //%s[@global='%s']" % (csName, uiName)
        return xpath

class XmlDataGenerator:
    def __init__(self, xmlTDT, nonXmlPrint=None, xmlStyleData=None):
        from xml.dom.minidom import Document
        self.xmlDoc = Document()
        self.xmlTDT = xmlTDT

        eleCount = 0
        self.eleMap = {}
        for eleTDT in self.xmlTDT:
            self.eleMap[eleTDT['name']] = eleCount
            if eleTDT.__contains__('alias'):
                for eName in eleTDT['alias']:
                    self.eleMap[eName] = eleCount
            eleTDT['ele'] = None
            if not eleTDT.__contains__('cls'):
                eleTDT['cls'] = eleTDT['findex'] + 1
            if not eleTDT.__contains__('sname'):
                eleTDT['sname'] = eleTDT['name']
            if not eleTDT.__contains__('must'):
                eleTDT['must'] = True
            eleCount += 1
        for eleTDT in self.xmlTDT:
            eleTDT['clslist'] = [index for index in range(0, eleCount) if self.xmlTDT[index]['cls'] > eleTDT['cls']]

        self.topEle = self.__createElement(self.xmlDoc, self.xmlTDT[0])
        if xmlStyleData != None:
            self.xmlDoc.insertBefore(self.xmlDoc.createProcessingInstruction("xml-stylesheet", xmlStyleData), self.topEle)

    def __getFele(self, eleIndex):
        feleIndex = self.xmlTDT[eleIndex]['findex']
        feleTDT = self.xmlTDT[feleIndex]

        if feleIndex > 0:
            fele = feleTDT['ele']
            if fele == None:
                ffele = self.__getFele(feleIndex)
                if feleTDT['must']:
                    fele = self.__createElement(ffele, feleTDT)
                else:
                    fele = ffele
            return fele
        else:
            return self.topEle

    def __createElement(self, fele, eleTDT, content=None, eleName=None, **eleAttrs):
        ele = self.xmlDoc.createElement(eleName if eleName != None else eleTDT['sname'])
        eleTDT['ele'] = ele
        fele.appendChild(ele)
        for eleAttr in eleAttrs.keys():
            ele.setAttribute(eleAttr, eleAttrs[eleAttr])
        if content != None:
            ele.appendChild(self.xmlDoc.createCDATASection(content))

        for index in eleTDT['clslist']:
            self.xmlTDT[index]['ele'] = None
        return ele

    def addElement(self, eleName, content=None, **eleAttrs):
        eleIndex = self.eleMap[eleName]
        fele = self.__getFele(eleIndex)
        self.__createElement(fele, self.xmlTDT[eleIndex], content, eleName, **eleAttrs)

    def __str__(self, indent="\t", newl="\n", encoding=None):
        return self.xmlDoc.toprettyxml(indent, newl, encoding)

class XpathXml:
    def __init__(self, xmlFile=None, xmlRoot=None):
        from xml.dom.minidom import parse, Document, parseString
        self._xmlDoc = Document() if (xmlFile == None or xmlFile == "") else\
            (parse(xmlFile) if os.path.exists(xmlFile) else parseString(xmlFile))
        if xmlRoot != None:
            self._xmlDoc.appendChild(self.CreateNode(xmlRoot))

    def getNode(self, xpath, isGlobal=False, refNode=None):
        jpath = XmlOperation.XpathToJson(xpath, "{'Index':1}")
        if refNode == None:
            refNode = self._xmlDoc
        if isGlobal:
            attrs = [attr for attr in jpath.keys() if (attr != "Index" and attr != 'ClassName')]
            expIndex = jpath['Index']
            actIndex = 0
            for curDoml in refNode.getElementsByTagName(jpath['ClassName']):
                isFound = True
                for attName in attrs:
                    if curDoml.getAttribute(attName) != jpath[attName]:
                        isFound = False
                        break
                if isFound:
                    actIndex += 1
                    if actIndex == expIndex:
                        return curDoml
            return None

        curDoml = refNode
        while curDoml != None:
            expNode = jpath['ClassName']
            expIndex = jpath['Index']

            actIndex = 0
            for tempDom in curDoml.childNodes:
                if tempDom.nodeName == expNode:
                    actIndex += 1
                    if actIndex == expIndex:
                        break
            if actIndex == expIndex:
                curDoml = tempDom
            else:
                curDoml = None

            try:
                jpath = jpath['Child']
            except:
                break
        return curDoml

    def getNodeContent(self, node, attName=None, refNode=None):
        from xml.dom.minidom import  Element
        if refNode != None and type(node) != Element:
            node = self.GetNode(node, False, refNode)
        if node == None:
            return
        if attName == None or attName.length() == 0:
            return node.childNodes[0].nodeValue
        else:
            attNode = node.getAttribute(attName)
            if attNode != None:
                return attNode.nodeValue

    def getChildNodes(self, pXpath, refNode=None):
        from xml.dom.minidom import  Element
        fNode = pXpath if type(pXpath) == Element else self.GetNode(pXpath, False, refNode)
        return [tempNode for tempNode in fNode.childNodes if type(tempNode) == Element]

    def getChildren(self, pXpath, attName, seperator, *childXpaths) :
        children = []
        if seperator == None:
            seperator = ""

        for tempNode in self.GetChildNodes(pXpath):

            childContent = None
            for  childXpath in childXpaths:
                cNode = self.GetNode(childXpath, False, tempNode)
                if cNode != None:
                    if childContent == None:
                        childContent = ""
                    else:
                        childContent += seperator

                    nodeValue = self.GetNodeContent(cNode, attName)
                    if nodeValue != None:
                        childContent += nodeValue

            if childContent != None:
                children.append(childContent)

        return children;

    def createNode(self, nodeName, nodeContent=None, **eleAttrs):
        ele = self._xmlDoc.createElement(nodeName)
        if nodeContent != None:
            ele.appendChild(self._xmlDoc.createTextNode(nodeContent))
        for attName in eleAttrs.keys():
            attVal = eleAttrs[attName]
            if attVal != None:
                ele.setAttribute(attName, attVal)
        return ele

    def setNode(self, xpath, isGlobal=False, nodeContent=None, nodeName=None, **eleAttrs):
        tNode = self.GetNode(xpath, isGlobal)
        if tNode != None:
            if nodeName != None:
                tNode.appendChild(self.CreateNode(nodeName, nodeContent, **eleAttrs))
            else:   
                if nodeContent != None:
                    tempContent = self._xmlDoc.createTextNode(str(nodeContent))
                    if len(tNode.childNodes) > 0:
                        tNode.childNodes[0] = tempContent
                    else:
                        tNode.appendChild(tempContent)
                for attName in eleAttrs:
                    tNode.setAttribute(attName, eleAttrs[attName])
            return True
        return False

    def removeNode(self, xpath, isGlobal=False, delNext=None):
        tNode = self.GetNode(xpath, isGlobal)
        if tNode != None:
            pNode = tNode.parentNode.childNodes
            if delNext != None:
                nIndex = pNode.index(tNode)
                for delIndex in range(nIndex, len(pNode)):
                    if pNode[delIndex].nodeName == delNext:
                        pNode.__delitem__(delIndex)
                        break
            pNode.remove(tNode)
            return True
        return False

    def saveTo(self, filePath):
        with codecs.open(filePath, mode='w', encoding="utf-8") as fileHandle:
            fileHandle.write(str(self))

    def __str__(self):
        return self._xmlDoc.saveXML(None)
