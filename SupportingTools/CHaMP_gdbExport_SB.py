# Script name: CHaMP_gdbExport.py
#
# Last updated: 1/30/2017
# Created by: Sara Bangen (sara.bangen@gmail.com)
#
# Description:
#	- Outputs shapefiles and reaster from geodatabase
#
# Output:
#	- shapefile and rasters with same name as that in gdb
#
#
# Assumomptions:
#   - *gdb is named 'SurveyGeoDatabase'
#
# The user will need to specify the function arguments
#
# Args:
#   folderPath:  Parent directory folder.

# -----------------------------------
# Set user-defined  input parameters
# -----------------------------------

folderPath = r"C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\TopographicGUs\wrk_Data\01_TestSites\Wenatchee\LWIN0001-000041\2014"

# -----------------------------------
# Start of script

# Import required modules
# Check out the ArcGIS Spatial Analyst extension license
import arcpy, os, fnmatch
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension('Spatial')


def fcToShp(folderPath): # change name before sending to natalie, add bankfull centerline to output

    # Set workspace
    # Set environment settings to overwrite output
    # arcpy.env.workspace = wd
    arcpy.env.overwriteOutput = True
    env.qualifiedFieldNames = False

    # Search workspace folder for all polygon shapefiles that match searchName
    # Add to list
    for root, dirs, files in os.walk(folderPath):
        arcpy.env.workspace = folderPath
        for dir in fnmatch.filter(dirs, 'Topo'): # need to change this line to
            print folderPath
            dirPath = os.path.join(root, dir).replace("//", "/")
            print dirPath
            outFolder = dirPath
            gdbPath = os.path.join(dirPath, 'SurveyGeoDatabase.gdb').replace("//", "/")
            arcpy.env.workspace = gdbPath

            arcpy.CopyRaster_management("Detrended", os.path.join(outFolder, "Detrended.tif"))
            arcpy.CopyRaster_management("DEM", os.path.join(outFolder, "DEM.tif"))

            arcpy.FeatureClassToShapefile_conversion(["Bankfull", "BankfullCL", "BankfullXS", "CenterLine", "Thalweg", "WaterExtent"], outFolder)

            arcpy.env.workspace = outFolder
            detHS = Hillshade("Detrended.tif", model_shadows="SHADOWS")
            detHS.save("Detrended_HS.tif")
            Contour("Detrended.tif", "Detrended_Contours10cm.shp", contour_interval=0.1)
            demHS = Hillshade("DEM.tif", model_shadows="SHADOWS")
            demHS.save("DEM_HS.tif")
            Contour("DEM.tif", "DEM_Contours10cm.shp", contour_interval=0.1)

fcToShp(folderPath)