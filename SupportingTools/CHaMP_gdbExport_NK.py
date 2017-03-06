# Script name: CHaMP_gdbExport_NK.py
#
# Last updated: Feb/16/2017
# Created by: Sara Bangen (sara.bangen@gmail.com)
# Adapted by: Natalie Kramer (n.kramer.anderson@gmail.com)#
#
# Description:
#	- Outputs shapefiles and raster from geodatabase for inputs into GUT.
#
# Output:
#	- shapefile and rasters with same name as that in gdb
#
#
# Assumptions:
#   - *gdb is named 'SurveyGeoDatabase'
#
# The user will need to specify the function arguments
#
# Args:
#   INfolderPath:  Parent CHAMP directory folder.
#   OUTfolderPath:  Output GUT run directory.
# -----------------------------------
# Set user-defined  input parameters
# -----------------------------------

INfolderPath = r"E:\CHaMP\MonitoringData\2015\Wenatchee\LWIN0001-000041\VISIT_3275"
OUTfolderPath = r"E:\GUT\_Wenatchee"


# -----------------------------------
# Start of script

# Import required modules
# Check out the ArcGIS Spatial Analyst extension license
import arcpy, os, fnmatch
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension('Spatial')


def fcToShp(INfolderPath, OUTfolderPath): 
    # Set workspace
    # Set environment settings to overwrite output
    # arcpy.env.workspace = wd
    arcpy.env.overwriteOutput = True
    env.qualifiedFieldNames = False

    # Search Input folder for all polygon shapefiles that match searchName
    # Add to list
    for root, dirs, files in os.walk(INfolderPath):
        arcpy.env.workspace = INfolderPath
        for dir in fnmatch.filter(dirs, 'Topo'): 
            print INfolderPath
            dirPath = os.path.join(root, dir).replace("//", "/")
            print dirPath
            dirPathsplit=dirPath.split("\\")
            #outFolder = OUTfolderPath + "\\" + dirPathsplit[-3] + "\\"+ dirPathsplit[-2] + "\\"+ "Inputs"
            outFolder=os.path.join(OUTfolderPath, dirPathsplit[-3], dirPathsplit[-2], "Inputs").replace("//", "/")
            print outFolder
            if not os.path.exists(outFolder):
                os.makedirs(outFolder)
            gdbPath = os.path.join(dirPath, 'SurveyGDB','SurveyGeoDatabase.gdb').replace("//", "/")
            print gdbPath
            arcpy.env.workspace = gdbPath

            arcpy.CopyRaster_management("Detrended", os.path.join(outFolder, "Detrended.tif"))
            arcpy.CopyRaster_management("DEM", os.path.join(outFolder, "DEM.tif"))

            arcpy.env.workspace = os.path.join(gdbPath + 'Projected')
            arcpy.FeatureClassToShapefile_conversion(["Bankfull", "BankfullXS",  "BankfullCL", "Centerline",
                "Thalweg", "WaterExtent"], outFolder)

            arcpy.env.workspace = outFolder
            detHS = Hillshade("Detrended.tif", model_shadows="SHADOWS")
            detHS.save("Detrended_HS.tif")
            Contour("Detrended.tif", "Detrended_Contours10cm.shp", contour_interval=0.1)
            demHS = Hillshade("DEM.tif", model_shadows="SHADOWS")
            demHS.save("DEM_HS.tif")
            Contour("DEM.tif", "DEM_Contours10cm.shp", contour_interval=0.1)

fcToShp(INfolderPath, OUTfolderPath)
