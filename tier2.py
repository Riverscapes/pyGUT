#  import required modules and extensions
import arcpy
import os
import config
import fnmatch
import math
import numpy
from arcpy.sa import *
arcpy.CheckOutExtension('Spatial')


def main():

    print 'Starting Tier 2 classification...'

    #  environment settings
    arcpy.env.workspace = config.workspace  # set workspace to pf
    arcpy.env.overwriteOutput = True  # set to overwrite output

    #  set output paths
    evpath = os.path.join(arcpy.env.workspace, 'EvidenceLayers')
    if config.runFolderName != 'Default' and config.runFolderName != '':
        outpath = os.path.join(arcpy.env.workspace, 'Output', config.runFolderName)
    else:
        runFolders = fnmatch.filter(next(os.walk(os.path.join(arcpy.env.workspace, 'Output')))[1], 'Run_*')
        runNum = int(max([i.split('_', 1)[1] for i in runFolders]))
        outpath = os.path.join(arcpy.env.workspace, 'Output', 'Run_%03d' % runNum)

    #  clean up!
    #  search for existing tier 2 shapefiles or rasters
    #  if exist, delete from workspace otherwise will lead
    #  to errors in subsequent steps
    for root, dirs, files in os.walk(outpath):
        for file in files:
            if 'Tier2' in file:
                os.remove(os.path.join(outpath, file))

    #  import required rasters
    dem = Raster(config.inDEM)
    bf = Raster('EvidenceLayers/bfCh.tif')  # created in 'tier1' module

    #  set raster environment settings
    desc = arcpy.Describe(dem)
    arcpy.env.extent = desc.Extent
    arcpy.env.outputCoordinateSystem = desc.SpatialReference
    arcpy.env.cellSize = desc.meanCellWidth

    #  ---------------------------------
    #  tier 2 functions
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

    #  --tier 2 raster to polygon function--

    def ras2poly_cn(Mound, Planar, Bowl, Trough):
        shps = []
        formDict = locals()
        for key, value in formDict.iteritems():
            if key in ['Mound', 'Planar', 'Bowl', 'Trough']:
                tmp_fn = 'in_memory/tmp_' + str(key)
                shps.extend([tmp_fn])
                arcpy.RasterToPolygon_conversion(value, tmp_fn, 'NO_SIMPLIFY', 'VALUE')
                arcpy.AddField_management(tmp_fn, 'Tier1', 'TEXT', '', '', 15)
                arcpy.AddField_management(tmp_fn, 'Tier2', 'TEXT', '', '', 15)
                arcpy.AddField_management(tmp_fn, 'Form', 'TEXT', '', '', 10)
                with arcpy.da.UpdateCursor(tmp_fn, ['Tier1', 'Tier2', 'Form']) as cursor:
                    for row in cursor:
                        row[0] = 'InChannel'
                        row[2] = str(key)
                        if row[2] == 'Planar':
                            row[1] = 'Planar'
                        elif row[2] == 'Mound':
                            row[1] = 'Convexity'
                        else:
                            row[1] = 'Concavity'
                        cursor.updateRow(row)

        tmp_units = arcpy.Merge_management(shps, 'in_memory/tmp_merge')
        arcpy.AddField_management(tmp_units, 'Area', 'DOUBLE')
        arcpy.AddField_management(tmp_units, 'UnitID', 'SHORT')
        with arcpy.da.UpdateCursor(tmp_units, ['OID@', 'UnitID', 'SHAPE@AREA', 'Area']) as cursor:
            for row in cursor:
                row[1] = row[0]
                row[3] = row[2]
                cursor.updateRow(row)
        arcpy.CopyFeatures_management(tmp_units, os.path.join(outpath, 'Tier2_InChannel_Raw.shp'))
        arcpy.CopyFeatures_management(tmp_units, os.path.join(outpath, 'Tier2_InChannel.shp'))

        # shps.extend([tmp_units])
        for shp in shps:
            arcpy.Delete_management(shp)

    #  ---------------------------------
    #  calculate integrated widths
    #  ---------------------------------

    bfw = intWidth_fn(config.bfPolyShp, config.bfCL)
    ww = intWidth_fn(config.wPolyShp, config.wCL)
    print 'Integrated bankfull width: ' + str(bfw) + ' m'
    print 'Integrated wetted width: ' + str(ww) + ' m'

    #  ---------------------------------
    #  tier 2 evidence rasters
    #  ---------------------------------
    inCh = SetNull(bf, 1, '"VALUE" = 0')

    print '...deriving evidence rasters...'

    #  --mean dem--
    if not os.path.exists(os.path.join(evpath, os.path.splitext(os.path.basename(config.inDEM))[0] + '_mean.tif')):
        neigh = NbrRectangle(round(math.ceil(bfw) * 0.1, 1), round(math.ceil(bfw) * 0.1, 1), 'MAP')  # set neighborhood size
        meanDEM = FocalStatistics(dem, neigh, 'MEAN', 'DATA')  # calculate mean z
        outMeanDEM = ExtractByMask(meanDEM, dem)  # clip output to input
        outMeanDEM.save(os.path.join(evpath, os.path.splitext(os.path.basename(config.inDEM))[0] + '_mean.tif'))  # save output
    else:
        outMeanDEM = Raster(os.path.join(evpath, os.path.splitext(os.path.basename(config.inDEM))[0] + '_mean.tif'))

    #  --in channel mean dem--
    if not os.path.exists(os.path.join(evpath, 'inCh_' + os.path.basename(config.inDEM))):
        inChDEM = inCh * outMeanDEM
        inChDEM.save(os.path.join(evpath, 'inCh_' + os.path.basename(config.inDEM)))  # save output
    else:
        inChDEM = Raster(os.path.join(evpath, 'inCh_' + os.path.basename(config.inDEM)))

    #  --residual topography--
    if not os.path.exists(os.path.join(evpath, 'resTopo.tif')):
        neigh2 = NbrRectangle(bfw, bfw, 'MAP')  # set neighborhood size
        smDEM = FocalStatistics(inChDEM, neigh2, 'MEAN', 'DATA')  # calculate mean z ('smoothed' DEM)
        resTopo = inChDEM - smDEM  # calculate residual topogaphy
        resTopo.save(os.path.join(evpath, 'resTopo.tif')) # save output
    else:
        resTopo = Raster(os.path.join(evpath, 'resTopo.tif'))

    #  --normalized fill--
    if not os.path.exists(os.path.join(evpath, 'normFill.tif')):
        #  a. fill dem
        rFill = Fill(inChDEM)
        #  b. difference with dem
        rDiff = (rFill - inChDEM)
        #  c. get min fill value
        rMinResult3 = arcpy.GetRasterProperties_management(rDiff, 'MINIMUM')
        rMin3 = float(rMinResult3.getOutput(0))
        #  d. get max fill value
        rMaxResult3 = arcpy.GetRasterProperties_management(rDiff, 'MAXIMUM')
        rMax3 = float(rMaxResult3.getOutput(0))
        #  e.  normalize fill values
        normFill = (rDiff - rMin3) / (rMax3 - rMin3)
        #  f. save output
        normFill.save(os.path.join(evpath, 'normFill.tif'))
    else:
        normFill = Raster(os.path.join(evpath, 'normFill.tif'))

    # #  --channel margin--
    # if not os.path.exists(os.path.join(evpath, 'chMargin.tif')):
    #     #  a. remove any wePoly parts < 5% of total area
    #     wPolyElim = arcpy.EliminatePolygonPart_management(config.wPolyShp, 'in_memory/tmp_wPolyElim', 'PERCENT', '', 5, 'ANY')
    #     #  b. erase wPolyElim from bankfull polygon
    #     polyErase = arcpy.Erase_analysis(config.bfPolyShp, wPolyElim, 'in_memory/tmp_polyErase', '')
    #     #  c. buffer the output by 10% of the integrated wetted width
    #     bufferDist = 0.1 * ww
    #     polyBuffer = arcpy.Buffer_analysis(polyErase, 'in_memory/tmp_polyBuffer', bufferDist, 'FULL')
    #     #  d. clip the output to the bankull polygon
    #     arcpy.Clip_analysis(polyBuffer, config.bfPolyShp, 'EvidenceLayers/chMargin.shp')
    #     #  e. convert the output to a raster
    #     arcpy.PolygonToRaster_conversion('EvidenceLayers/chMargin.shp', 'FID', 'tmp_outRas.tif', 'CELL_CENTER', 'NONE', '0.1')
    #     #  f. set all cells inside/outside the bankfull ratser to 1/0
    #     cm = Con(IsNull('tmp_outRas.tif'), 0, 1)
    #     #  g. save the ouput
    #     cm.save(os.path.join(evpath, 'chMargin.tif'))
    # else:
    #     cm = Raster(os.path.join(evpath, 'chMargin.tif'))

    # ---------------------------------
    #  tier 2 classification
    #  ---------------------------------

    # covert residual topo raster to numpy array
    arr = arcpy.RasterToNumPyArray(resTopo)
    desc2 = arcpy.Describe(resTopo)
    NDV = desc2.noDataValue
    arr[arr == NDV] = numpy.nan
    q25pos = numpy.percentile(arr[arr > 0], 25)
    q25neg = numpy.percentile(numpy.negative(arr[arr <= 0]), 25)
    q50neg = numpy.percentile(numpy.negative(arr[arr <= 0]), 50)

    print '...classifying forms...'

    mounds = SetNull(resTopo, 1, '"VALUE" < ' + str(q25pos))
    planar = SetNull(resTopo, 1, '"VALUE" >= ' + str(q25pos)) * SetNull(resTopo, 1, '"VALUE" <= -' + str(q25neg))
    bowls = SetNull(resTopo, 1, '"VALUE" > -' + str(q50neg)) * SetNull(normFill, 1, '"VALUE" <= 0')
    troughs = Con(IsNull(bowls), 1) * SetNull(resTopo, 1, '"VALUE" > -' + str(q25neg))
    ras2poly_cn(mounds, planar, bowls, troughs)
    #
    #
    # # ----------------------------------------------------------
    # # Remove temporary files
    #
    # print '...removing intermediary surfaces...'
    #
    # for root, dirs, files in os.walk(arcpy.env.workspace):
    #     for f in fnmatch.filter(files, 'tmp_*'):
    #         os.remove(os.path.join(root, f))
    #
    # print '...done with Tier 2 classification.'

if __name__ == '__main__':
    main()
