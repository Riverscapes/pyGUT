import os, sys, xml, datetime, pytz
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
        ET.SubElement(resultsNode, key).text = val
        self.write()

    def log(self, msg, severity="info"):
        dateStr = datetime.datetime.now(pytz.timezone('US/Pacific')).strftime('%Y-%m-%dT%H:%M:%S%z')
        print '[{}] [{}] {}'.format(severity, self.method, msg)
        logNode = self.logTree.find("log")
        if logNode is None:
            logNode = ET.SubElement(self.logTree.getroot(), "log")

        ET.SubElement(logNode, "message", severity=severity, date=dateStr).text = msg
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
