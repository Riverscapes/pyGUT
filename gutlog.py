import os, sys, xml, datetime, pytz, re
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import logging, logging.handlers

class Logger:

    def __init__(self, logRoot, xmlFilePath, meta={}):
        self.logDir = os.path.join(logRoot, "logs")
        self.logFilePath = os.path.join(self.logDir, xmlFilePath)
        if not os.path.exists(self.logDir):
            os.makedirs(self.logDir)
        self.logTree = ET.ElementTree(ET.Element("gut"))
        self.method = ""

        # File exists. Delete it.
        if os.path.isfile(self.logFilePath):
            os.remove(self.logFilePath)
        for key, val in meta.iteritems():
            self.addMeta(key, val)
        self.write()

    def setMethod(self, method):
        self.method = method

    def addMeta(self, key, val):
        resultsNode = self.logTree.find("meta")
        if resultsNode is None:
            resultsNode = ET.SubElement(self.logTree.getroot(), "meta")
        ET.SubElement(resultsNode, key, ).text = val
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
        }
        if adapt.has_key(obj.__class__):
            adapt[obj.__class__](keyname, obj, resultsNode)
        else:
            tagname = re.sub('[\W_]+', '', keyname.printable)
            node = ET.SubElement(resultsNode, tagname.lower()).text = str(obj)

    def getXML_dict(self, keyname, indict, rootNode):
        node = ET.SubElement(rootNode, keyname)
        for k, v in indict.items():
            self.obj2XML(k,v,node)

    def getXML_list(self, keyname, inlist, rootNode):
        node = ET.SubElement(rootNode, keyname)
        for i in inlist:
            self.obj2XML("value",i,node)