#  import required modules and extensions
import arcpy
import config
import os
import fnmatch
import tempfile
from arcpy.sa import *
arcpy.CheckOutExtension('Spatial')


def main():

    print 'Starting Tier 1 classification...'

    #  create temporary workspace
    tmp_dir = tempfile.mkdtemp()

    #  environment settings
    arcpy.env.workspace = tmp_dir # set workspace to pf
    arcpy.env.overwriteOutput = True  # set to overwrite output

    #  import required rasters
    dem = Raster(os.path.join(config.workspace, config.inDEM))

    #  set raster environment settings
    desc = arcpy.Describe(dem)
    arcpy.env.extent = desc.Extent
    arcpy.env.outputCoordinateSystem = desc.SpatialReference
    arcpy.env.cellSize = desc.meanCellWidth

    #  if don't already exist, create evidence layer and output folders
    folder_list = ['EvidenceLayers', 'Output']
    for folder in folder_list:
        if not os.path.exists(os.path.join(config.workspace, folder)):
            os.makedirs(os.path.join(config.workspace, folder))

    if config.runFolderName != 'Default' and config.runFolderName != '':
        outpath = os.path.join(config.workspace, 'Output', config.runFolderName)
    else:
        runFolders = fnmatch.filter(next(os.walk(os.path.join(config.workspace, 'Output')))[1], 'Run_*')
        if len(runFolders) >= 1:
            runNum = int(max([i.split('_', 1)[1] for i in runFolders])) + 1
        else:
            runNum = 1
        outpath = os.path.join(config.workspace, 'Output', 'Run_%03d' % runNum)

    os.makedirs(outpath)

    #  set output paths
    evpath = os.path.join(config.workspace, 'EvidenceLayers')

    #  ---------------------------------
    #  calculate integrated widths
    #  ---------------------------------

    #  --integrated width function--

    #  calculates integrated width
    #  as: [polygon area] / [sum(centerline lengths)]

    def intWidth_fn(polygon, centerline):
        arrPoly = arcpy.da.FeatureClassToNumPyArray(polygon, ['SHAPE@AREA'])
        arrPolyArea = arrPoly['SHAPE@AREA'].sum()
        arrCL = arcpy.da.FeatureClassToNumPyArray(centerline, ['SHAPE@LENGTH'])
        arrCLLength = arrCL['SHAPE@LENGTH'].sum()
        intWidth = round(arrPolyArea / arrCLLength, 1)
        return intWidth

    bfw = intWidth_fn(os.path.join(config.workspace, config.bfPolyShp), os.path.join(config.workspace,config.bfCL))

    #  ---------------------------------
    #  tier 1 evidence raster
    #  ---------------------------------

    if not os.path.exists(os.path.join(evpath, 'bfCh.tif')):
        print '...deriving evidence rasters...'
        #  --bankfull polygon raster--
        #  a. convert bankfulll channel polygon to raster
        #arcpy.PolygonToRaster_conversion(config.bfPolyShp, 'FID', 'tmp_bfCh.tif', 'CELL_CENTER')
        bf_raw = arcpy.PolygonToRaster_conversion(os.path.join(config.workspace, config.bfPolyShp), 'FID', 'in_memory/tmp_bfCh', 'CELL_CENTER')
        #  b. set cells inside/outside bankfull channel polygon to 1/0
        #outCon = Con(IsNull('tmp_bfCh.tif'), 0, 1)
        outCon = Con(IsNull(bf_raw), 0, 1)
        #  c. clip to detrended DEM
        bf = ExtractByMask(outCon, dem)
        #  d. save output
        bf.save(os.path.join(evpath, 'bfCh.tif'))
    else:
        bf = Raster(os.path.join(evpath, 'bfCh.tif'))

    #  ---------------------------------
    #  tier 1 classification
    #  ---------------------------------

    print '...classifying in-channel vs out-of-channel units...'

    #  creates in channel vs out of channel
    #  breaks based on bankfull raster

    #  convert bankfull channel raster to polygon
    units = arcpy.RasterToPolygon_conversion(bf, 'in_memory/t1_units', 'NO_SIMPLIFY', 'VALUE')

    #  covert units from multipart to singlepart polygons
    units_sp = arcpy.MultipartToSinglepart_management(units, 'in_memory/t1_units_sp')

    #  create and attribute 'ValleyID' and 'ValleyUnit' fields
    arcpy.AddField_management(units_sp, 'ValleyID', 'SHORT')
    arcpy.AddField_management(units_sp, 'ValleyUnit', 'TEXT', '', '', 20)

    ct = 1
    with arcpy.da.UpdateCursor(units_sp, ['ValleyID', 'GRIDCODE', 'ValleyUnit']) as cursor:
        for row in cursor:
            row[0] = ct
            if row[1] == 0:
                row[2] = 'Out-of-Channel'
            else:
                row[2] = 'In-Channel'
            ct += 1
            cursor.updateRow(row)

    print '...classifying flow units...'

    #  add flow type and unique id to tier 1 units
    flowtype_raw = arcpy.CopyFeatures_management(units_sp, 'in_memory/flowtype_raw')
    arcpy.AddField_management(flowtype_raw, 'FlowUnit', 'TEXT', '', '', 12)

    with arcpy.da.UpdateCursor(flowtype_raw, ['ValleyUnit', 'FlowUnit']) as cursor:
        for row in cursor:
            if row[0] == 'Out-of-Channel':
                row[1] = 'High'
            else:
                row[1] = 'Emergent'
            cursor.updateRow(row)
    wPoly = arcpy.CopyFeatures_management(os.path.join(config.workspace, config.wPolyShp), 'in_memory/wPoly')
    arcpy.AddField_management(wPoly, 'FlowUnit', 'TEXT', '', '', 12)
    with arcpy.da.UpdateCursor(wPoly, ['FlowUnit']) as cursor:
        for row in cursor:
            row[0] = 'Submerged'
            cursor.updateRow(row)

    #  create flow type polygon
    flowtype = arcpy.Update_analysis(flowtype_raw, wPoly, 'in_memory/flowtype')
    #  intersect flow type polygon with tier 1 units
    flowtype_units_raw = arcpy.Intersect_analysis([units_sp, flowtype], 'in_memory/flowtype_units_raw', 'ALL')
    #  covert units from multipart to singlepart polygons
    flowtype_units_sp = arcpy.MultipartToSinglepart_management(flowtype_units_raw, 'in_memory/flowtype_units_sp')

    # calculate area
    arcpy.AddField_management(flowtype_units_sp, 'Area', 'DOUBLE')
    with arcpy.da.UpdateCursor(flowtype_units_sp, ['SHAPE@AREA', 'Area']) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    # find tiny units (area < 0.05 * bfw) and merge with unit that shares longest border
    flowtype_units_lyr = arcpy.MakeFeatureLayer_management(flowtype_units_sp, 'flowtype_units_lyr')
    arcpy.SelectLayerByAttribute_management(flowtype_units_lyr, 'NEW_SELECTION', '"Area" < ' + str(0.05 * bfw))
    flowtype_units = arcpy.Eliminate_management(flowtype_units_lyr, 'in_memory/flowtype_units_elim', "LENGTH")

    # add flow id field
    arcpy.AddField_management(flowtype_units, 'FlowID', 'SHORT')
    ct = 1
    with arcpy.da.UpdateCursor(flowtype_units, ['FlowID']) as cursor:
        for row in cursor:
            row[0] = ct
            ct += 1
            cursor.updateRow(row)

    # remove unnecessary fields
    fields = arcpy.ListFields(flowtype_units)
    keep = ['OBJECTID', 'Shape', 'ValleyID', 'ValleyUnit', 'FlowUnit', 'FlowID']
    drop = [x.name for x in fields if x.name not in keep]
    arcpy.DeleteField_management(flowtype_units, drop)

    arcpy.CopyFeatures_management(flowtype_units, os.path.join(outpath, 'Tier1.shp'))

    # ----------------------------------------------------------
    # remove temporary files

    print '...removing intermediary surfaces...'

    # arcpy.env.workspace = 'in_memory'
    # fcs = arcpy.ListFeatureClasses()
    arcpy.Delete_management("in_memory")
    arcpy.Delete_management(tmp_dir)
    #
    # for root, dirs, files in os.walk(arcpy.env.workspace):
    #     for f in fnmatch.filter(files, 'tmp_*'):
    #         os.remove(os.path.join(root, f))

    print '...done with Tier 1 classification.'

if __name__ == '__main__':
    main()
