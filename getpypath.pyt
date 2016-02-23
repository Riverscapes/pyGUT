import os, sys
import arcpy

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "ESRI Arcpy Path"
        self.alias = "pythonpath"

        # List of tool classes associated with this toolbox
        self.tools = [GetPyPath]


class GetPyPath(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Extract Raster By Mask"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Output Feature Class",
            name="fcName",
            datatype="GPString",
            parameterType="Derived",
            direction="Output")

        params = [param0]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        try:
            pydir = sys.exec_prefix
            pyexe = os.path.join(pydir, "python.exe")
            print pydir
            print pyexe
            if os.path.exists(pyexe):
                arcpy.AddMessage("Python Path: {0}".format(pyexe))
                arcpy.SetParameterAsText(0, pyexe)
            else:
                raise RuntimeError("No python.exe found in {0}".format(pydir))

        except:
            print sys.exc_info()[1]
            return