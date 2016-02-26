import os, sys
import xml.etree.ElementTree as ET

logFilePath = os.path.join(os.getcwd(), "log.xml")
logTree = ET.ElementTree(ET.Element("gut"))

def InitLogXML(xmlPath):
  global logFilePath, logTree
  logFilePath = xmlPath
  # File exists. Delete it.
  if os.path.isfile(xmlPath):
    os.remove(xmlPath)
  # File Doesn't Exist
  else:
    logTree.write(logFilePath)

def addResult(xmlTag, Val):
  global logTree
  resultsNode = logTree.find("results")
  ET.SubElement(resultsNode, xmlTag, ).text = Val
  logTree.write(logFilePath)

def log(msg, severity, method):
  global logTree
  print msg
  MessageNode = logTree.find("log")

  # General logs

  # ET.SubElement(doc, "field1", name="blah").text = "some value1"
  # ET.SubElement(doc, "field2", name="asdfasd").text = "some vlaue2"
  logTree.write(logFilePath)





