#!/usr/bin/python
# ---------------------------------------------------------------------------------------
# NOTE: We're abandoning this in favour of doign the work in CHAMP Topo Toolbar (to keep the code mode similar to GUT)
# so we repurposed config.py instead.
# I'm leaving this code here because it's full of cool pattern
# ---------------------------------------------------------------------------------------s
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
def yankRaster(path, rastername):
    arcpy.CopyRaster_management(gdb_path + r'\\' + path, output_path + r'\\' + rastername,"","","","","","32_BIT_FLOAT")

# GET bfPoints.shp: Make a selection in Survey GDB Topo_Points feature class of all features where Description = 'bf'
#       and then export the selection to shapefile
# ---------------------------------------------------------------------------------------
def getBFPoints():
    print "Getting the bankfull points raster..."
    #DESCRIPTION is a keyword, to use it in a query it needs special delimeters
    field_with_delimeters = arcpy.AddFieldDelimiters(ProjectedClassList[ProjectedClassList.index('Topo_Points')], "DESCRIPTION")
    bfQuery = field_with_delimeters + "='bf'" #create query string

    #use query while creating in-memory layer (heads up this in-memory files can be used in virtually all processing and analysis)
    arcpy.MakeFeatureLayer_management(ProjectedClassList[ProjectedClassList.index('Topo_Points')], 'temp_layer', bfQuery)

    #create name to save in-memory layer file to disk
    arcpy.CopyFeatures_management('temp_layer', output_path + r'\bfPoints.shp') #save to disk
    print "  Done"

# GET bfPolygon.shp: Export survey GDB feature class called "Bankfull" to shapefile.
#       If shape file contains more than one feature, delete all but where ExtentType = 'Channel'
# ---------------------------------------------------------------------------------------
def getBFPoly():
    print "Getting the bankfull polygon..."    
    #DESCRIPTION is a keyword, to use it in a query it needs special delimeters
    index = ProjectedClassList.index('Bankfull')
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
    print "  Done"

# GET bfXS.shp: Export survey GDB feature class called 'BankfullXS' to shapefile. Delete features where IsValie = 0
# ---------------------------------------------------------------------------------------
def getBFXS():
    print "Getting the BankfullXS polygon..."    
    #DESCRIPTION is a keyword, to use it in a query it needs special delimeters
    index = ProjectedClassList.index('BankfullXS')
    fClass = ProjectedClassList[index]
    count = int(arcpy.GetCount_management(ProjectedClassList[index]).getOutput(0))

    field_with_delimeters = arcpy.AddFieldDelimiters(fClass, "IsValid")
    bfQuery = field_with_delimeters + "=1" #create query string
    arcpy.MakeFeatureLayer_management(fClass, 'temp_layer', bfQuery)

    #create name to save in-memory layer file to disk
    arcpy.CopyFeatures_management('temp_layer', output_path + r'\bfXS.shp') #save to disk
    print "  Done"

# GET wePoly.shp: Same as bankfull polygon except the source layer is WaterExtent
# ---------------------------------------------------------------------------------------
def getWePoly():
    print "Getting the wePoly.shp polygon..."    
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
    print "  Done"

# GET channelUnitsClip.shp: Export survey GDB feature class called "Channel_Units" to shapefile
# ---------------------------------------------------------------------------------------
def getCHUnits():
    print "Getting the Channel Units Polygon..." 
    #DESCRIPTION is a keyword, to use it in a query it needs special delimeters
    index = ProjectedClassList.index('Channel_Units')
    fClass = ProjectedClassList[index]
    count = int(arcpy.GetCount_management(fClass).getOutput(0))
    arcpy.MakeFeatureLayer_management(fClass, 'temp_layer')

    #create name to save in-memory layer file to disk
    arcpy.CopyFeatures_management('temp_layer', output_path + r'\channelUnitsClip.shp') #save to disk
    print "  Done"

def getWaterDepth():
    print "Getting the Channel Units Polygon..." 
    dem = arcpy.Raster(gdb_path + r'\DEM')
    wsedem = arcpy.Raster(gdb_path + r'\WSEDEM')
    depth = wsedem - dem
    depth.save(output_path + r'\water_depth.img')
    print "  Done"


# EXECUTE Everything in order
# ---------------------------------------------------------------------------------------
yankRaster(r'DEM', 'dem.img')
yankRaster(r'Detrended', 'detDEM.img')
getWaterDepth()

getBFPoints()
getBFPoly()
getBFXS()
getWePoly()
getCHUnits()
