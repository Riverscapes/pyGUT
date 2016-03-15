import os, sys, xml, datetime, pytz, re
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import logging, logging.handlers

class Logger:

    def __init__(self, logRoot, xmlFilePath, config={}):
        self.logDir = os.path.join(logRoot, "logs")
        self.logFilePath = os.path.join(self.logDir, xmlFilePath)
        if not os.path.exists(self.logDir):
            os.makedirs(self.logDir)
        self.logTree = ET.ElementTree(ET.Element("gut"))
        self.method = ""

        # File exists. Delete it.
        if os.path.isfile(self.logFilePath):
            os.remove(self.logFilePath)
        if 'metadata' in config:
            self.obj2XML("metadata", config, self.logTree.getroot())
        self.write()

        self.write()

    def setMethod(self, method):
        self.method = method

    def addMeta(self, key, val):
        metaNode = self.logTree.find("metadata")
        if metaNode is None:
            metaNode = ET.SubElement(self.logTree.getroot(), "metadata")
        ET.SubElement(metaNode, key, ).text = val
        self.write()

    def addResult(self, key, val):
        resultsNode = self.logTree.find("results")
        if resultsNode is None:
            resultsNode = ET.SubElement(self.logTree.getroot(), "results")
        ET.SubElement(resultsNode, key).text = "{0}".format(val)
        self.write()

    def addResultObj(self, keyname, obj):
        resultsNode = self.logTree.find("results")
        if resultsNode is None:
            resultsNode = ET.SubElement(self.logTree.getroot(), "results")
        self.obj2XML(keyname, obj, resultsNode)
        self.write()

    def log(self, msg, severity="info", exception=None):
        dateStr = datetime.datetime.now(pytz.timezone('US/Pacific')).strftime('%Y-%m-%dT%H:%M:%S%z')
        print '[{}] [{}] {}'.format(severity, self.method, msg)
        logNode = self.logTree.find("log")
        if logNode is None:
            logNode = ET.SubElement(self.logTree.getroot(), "log")

        messageNode = ET.SubElement(logNode, "message", severity=severity, time=dateStr)
        ET.SubElement(messageNode, "description").text = msg
        if exception is not None:
            ET.SubElement(messageNode, "exception").text = exception
        self.write()

    def write(self):
        """Return a pretty-printed XML string for the Element.
        """
        rough_string = ET.tostring(self.logTree.getroot(), 'utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty = reparsed.toprettyxml(indent="\t")
        f =  open(self.logFilePath, "wb")
        f.write(pretty)
        f.close()

    def obj2XML(self, keyname, obj, resultsNode):
        adapt={
            dict: self.getXML_dict,
            list: self.getXML_list,
            tuple: self.getXML_list,
            xml.etree.ElementTree.Element: self.getXML_XML
        }
        if adapt.has_key(obj.__class__):
            adapt[obj.__class__](keyname, obj, resultsNode)
        else:
            node = ET.SubElement(resultsNode, self.SaniTag(keyname)).text = str(obj)

    def getXML_dict(self, keyname, indict, rootNode):
        node = ET.SubElement(rootNode, self.SaniTag(keyname))
        for k, v in indict.items():
            self.obj2XML(k,v,node)

    def getXML_XML(self, keyname, node, rootNode):
        elements = node.findall("*")
        for el in elements:
            rootNode.append(el)


    def getXML_list(self, keyname, inlist, rootNode):
        node = ET.SubElement(rootNode, self.SaniTag(keyname))
        for i in inlist:
            self.obj2XML("value",i,node)

    def SaniTag(self, string):
        return re.sub('[\W]+', '_', string).lower()