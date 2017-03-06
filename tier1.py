#  import required modules and extensions
import arcpy
import config
import os
import fnmatch
from arcpy.sa import *
arcpy.CheckOutExtension('Spatial')


def main():

    print 'Starting Tier 1 classification...'

    #  environment settings
    arcpy.env.workspace = config.workspace # set workspace to pf
    arcpy.env.overwriteOutput = True  # set to overwrite output

    #  import required rasters
    dem = Raster(config.inDEM)

    #  set raster environment settings
    desc = arcpy.Describe(dem)
    arcpy.env.extent = desc.Extent
    arcpy.env.outputCoordinateSystem = desc.SpatialReference
    arcpy.env.cellSize = desc.meanCellWidth

    #  if don't already exist, create evidence layer and output folders
    folder_list = ['EvidenceLayers', 'Output']
    for folder in folder_list:
        if not os.path.exists(os.path.join(arcpy.env.workspace, folder)):
            os.makedirs(os.path.join(arcpy.env.workspace, folder))

    if config.runFolderName != 'Default' and config.runFolderName != '':
        outpath = os.path.join(arcpy.env.workspace, 'Output', config.runFolderName)
    else:
        runFolders = fnmatch.filter(next(os.walk(os.path.join(arcpy.env.workspace, 'Output')))[1], 'Run_*')
        if len(runFolders) >= 1:
            runNum = int(max([i.split('_', 1)[1] for i in runFolders])) + 1
        else:
            runNum = 1
        outpath = os.path.join(arcpy.env.workspace, 'Output', 'Run_%03d' % runNum)

    os.makedirs(outpath)

    #  set output paths
    evpath = os.path.join(arcpy.env.workspace, 'EvidenceLayers')

    #  ---------------------------------
    #  tier 1 evidence raster
    #  ---------------------------------

    if not os.path.exists(os.path.join(evpath, 'bfCh.tif')):
        print '...deriving evidence rasters...'
        #  --bankfull polygon raster--
        #  a. convert bankfulll channel polygon to raster
        arcpy.PolygonToRaster_conversion(config.bfPolyShp, 'FID', 'tmp_bfCh.tif', 'CELL_CENTER')
        #  b. set cells inside/outside bankfull channel polygon to 1/0
        outCon = Con(IsNull('tmp_bfCh.tif'), 0, 1)
        #  c. clip to detrended DEM
        bf = ExtractByMask(outCon, dem)
        #  d. save output
        bf.save(os.path.join(evpath, 'bfCh.tif'))
    else:
        bf = Raster(os.path.join(evpath, 'bfCh.tif'))

    #  ---------------------------------
    #  tier 1 classification
    #  ---------------------------------

    print '...classifying in-channel vs out-of-channel...'

    #  creates in channel vs out of channel
    #  breaks based on bankfull raster

    #  create out of channel channel raster
    #  convert to polygon and save output
    outCh = SetNull(bf, 1, '"VALUE" = 1')
    outChShp = os.path.join(outpath, 'Tier1_OutOfChannel.shp')
    arcpy.RasterToPolygon_conversion(outCh, outChShp, 'NO_SIMPLIFY', 'VALUE')

    #  create in channel channel raster
    #  convert to polygon and save output
    inCh = SetNull(bf, 1, '"VALUE" = 0')
    inChShp = os.path.join(outpath, 'Tier1_InChannel.shp')
    arcpy.RasterToPolygon_conversion(inCh, inChShp, 'NO_SIMPLIFY', 'VALUE')

    #  create and attribute 'Tier1' field
    arcpy.AddField_management(outChShp, 'Tier1', 'TEXT', 20)
    arcpy.AddField_management(inChShp, 'Tier1', 'TEXT', 20)

    fields = ['Tier1']

    with arcpy.da.UpdateCursor(outChShp, fields) as cursor:
        for row in cursor:
            row[0] = 'Out of Channel'
            cursor.updateRow(row)

    with arcpy.da.UpdateCursor(inChShp, fields) as cursor:
        for row in cursor:
            row[0] = 'In Channel'
            cursor.updateRow(row)

    # ----------------------------------------------------------
    # Remove temporary files

    print '...removing intermediary surfaces...'

    for root, dirs, files in os.walk(arcpy.env.workspace):
        for f in fnmatch.filter(files, 'tmp_*'):
            os.remove(os.path.join(root, f))

    print '...done with Tier 1 classification.'

if __name__ == '__main__':
    main()
