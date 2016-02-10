#!/usr/bin/python

import sys, os
import arcpy, config

arcpy.CheckOutExtension('Spatial')
arcpy.CheckOutExtension('3D')

# 1. Set GDN input folder (sys.argv[0])
# 2. Set output Dir (sys.argv[1])
print 'Number of arguments:', len(sys.argv), 'arguments.'
print 'Argument List:', str(sys.argv)
gdb_path = sys.argv[1]
output_path = sys.argv[2]

arcpy.env.workspace = gdb_path
arcpy.env.overwriteOutput = True

tableList = arcpy.ListTables()
datasetList = arcpy.ListDatasets()
ProjectedClassList = arcpy.ListFeatureClasses("*", "", datasetList[datasetList.index("Projected")])

# Retrieve site name (from #1)
# GET dem.img: Export surve GDB raster called Detrended to IMG file
# ---------------------------------------------------------------------------------------
def getDEM():
    dem = arcpy.Raster(gdb_path + r'\DEM')
    dem.save(output_path + r'\dem.img')

# GET detDEM.img: Export survey GDB raster called DEM to IMG file
# ---------------------------------------------------------------------------------------
def getDetDEM():
    detrendedDEM = arcpy.Raster(gdb_path + r'\Detrended')
    detrendedDEM.save(output_path + r'\detDEM.img', )

# GET waterDepth.img: Export survey GDB raster called Water_Depth to IMG file
# ---------------------------------------------------------------------------------------
def getWaterDepth():
    detrendedDEM = arcpy.Raster(gdb_path + r'\Projected\Water_Depth')
    detrendedDEM.save(output_path + r'\waterDepth.img', )


# GET bfPoints.shp: Make a selection in Survey GDB Topo_Points feature class of all features where Description = 'bf'
#       and then export the selection to shapefile
# ---------------------------------------------------------------------------------------
def getBFPoints():
    #DESCRIPTION is a keyword, to use it in a query it needs special delimeters
    field_with_delimeters = arcpy.AddFieldDelimiters(ProjectedClassList[ProjectedClassList.index('Topo_Points')], "DESCRIPTION")
    bfQuery = field_with_delimeters + "='bf'" #create query string

    #use query while creating in-memory layer (heads up this in-memory files can be used in virtually all processing and analysis)
    arcpy.MakeFeatureLayer_management(ProjectedClassList[ProjectedClassList.index('Topo_Points')], 'temp_layer', bfQuery)

    #create name to save in-memory layer file to disk
    arcpy.CopyFeatures_management('temp_layer', output_path + r'\bfPoints.shp') #save to disk
    arcpy.DeleteFeatures_management('temp_layer')


# GET bfPolygon.shp: Export survey GDB feature class called "Bankfull" to shapefile.
#       If shape file contains more than one feature, delete all but where ExtentType = 'Channel'
# ---------------------------------------------------------------------------------------
def getBFPoly():
    #DESCRIPTION is a keyword, to use it in a query it needs special delimeters
    index = ProjectedClassList.index('BankfullXS')
    fClass = ProjectedClassList[index]
    count = int(arcpy.GetCount_management(fClass).getOutput(0))
    if (count > 1):
        field_with_delimeters = arcpy.AddFieldDelimiters(fClass, "ExtentType")
        bfQuery = field_with_delimeters + "='Channel'" #create query string
        arcpy.MakeFeatureLayer_management(fClass, 'temp_layer', bfQuery)
    else:
        arcpy.MakeFeatureLayer_management(fClass, 'temp_layer')

    #create name to save in-memory layer file to disk
    arcpy.CopyFeatures_management('temp_layer', output_path + r'\bfPolygon.shp') #save to disk
    arcpy.DeleteFeatures_management('temp_layer')

# GET bfXS.shp: Export survey GDB feature class called 'BankfullXS' to shapefile. Delete features where IsValie = 0
# ---------------------------------------------------------------------------------------
def getBFXS():
    #DESCRIPTION is a keyword, to use it in a query it needs special delimeters
    index = ProjectedClassList.index('BankfullXS')
    fClass = ProjectedClassList[index]
    count = int(arcpy.GetCount_management(ProjectedClassList[index]).getOutput(0))

    field_with_delimeters = arcpy.AddFieldDelimiters(fClass, "IsValid")
    bfQuery = field_with_delimeters + "=1" #create query string
    arcpy.MakeFeatureLayer_management(fClass, 'temp_layer', bfQuery)

    #create name to save in-memory layer file to disk
    arcpy.CopyFeatures_management('temp_layer', output_path + r'\bfXS.shp') #save to disk
    arcpy.DeleteFeatures_management('temp_layer')

# GET wePoly.shp: Same as bankfull polygon except the source layer is WaterExtent
# ---------------------------------------------------------------------------------------
def getWePoly():
    #DESCRIPTION is a keyword, to use it in a query it needs special delimeters
    index = ProjectedClassList.index('WaterExtent')
    fClass = ProjectedClassList[index]
    count = int(arcpy.GetCount_management(fClass).getOutput(0))
    if (count > 1):
        field_with_delimeters = arcpy.AddFieldDelimiters(fClass, "ExtentType")
        bfQuery = field_with_delimeters + "='Channel'" #create query string
        arcpy.MakeFeatureLayer_management(fClass, 'temp_layer', bfQuery)
    else:
        arcpy.MakeFeatureLayer_management(fClass, 'temp_layer')

    #create name to save in-memory layer file to disk
    arcpy.CopyFeatures_management('temp_layer', output_path + r'\wePoly.shp') #save to disk
    arcpy.DeleteFeatures_management('temp_layer')

# GET channelUnitsClip.shp: Export survey GDB feature class called "Channel_Units" to shapefile
# ---------------------------------------------------------------------------------------
def getCHUnits():
    #DESCRIPTION is a keyword, to use it in a query it needs special delimeters
    index = ProjectedClassList.index('Channel_Units')
    fClass = ProjectedClassList[index]
    count = int(arcpy.GetCount_management(fClass).getOutput(0))
    arcpy.MakeFeatureLayer_management(fClass, 'temp_layer')

    #create name to save in-memory layer file to disk
    arcpy.CopyFeatures_management('temp_layer', output_path + r'\channelUnitsClip.shp') #save to disk
    arcpy.DeleteFeatures_management('temp_layer')



# GET champGrainSize.csv: ???
# GET champSubstrate.csv: ???
# get champLW.csv: ???


# EXECUTE Everything in order
# ---------------------------------------------------------------------------------------
getDEM()
getDetDEM()
getWaterDepth()
getBFPoints()
getBFPoly()
getBFXS()
getWePoly()
getCHUnits()