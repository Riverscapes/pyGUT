#  import required modules and extensions
import arcpy
import os
import config
import fnmatch
import math
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
    for root, dirs, files in os.walk(arcpy.env.workspace):
        for f in fnmatch.filter(files, os.path.join(outpath, 'Tier2*')):
            os.remove(os.path.join(root, f))

    #  import required rasters
    dem = Raster(config.inDEM)
    det = Raster(config.inDet)
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

    #  --area threshold function--

    #  calculates raster clusters (or groups)
    #  and their individual area.  Threshold
    #  based on bfw and area.th (area threshold;
    #  ratio of bfw).  All clusters that have
    #  an area < the (area.th*bfw) are set to
    #  no data.  All clusters that meet the
    #  threshold are set to a value of 1.

    def area_fn(ras, area_th):
        rGroup = RegionGroup(ras, 'FOUR')  # caclulate cell group (i.e., cluster)
        rArea = ZonalGeometry(rGroup, 'Value', 'AREA', '0.1')  # calculate indiv cluster area
        rAreaTh = SetNull(rArea, 1,
                          '"VALUE" <' + str(area_th * bfw))  # assign NA to clusters that don't meet area threshold
        return rAreaTh

    #  --membership function--

    #  counts the number of cells within window
    #  that have been classified as the given
    #  unit.  window size (based on ratio of
    #  bankfull width) and count threshold
    #  (percentage of count) are set by the user.
    #  all cells that don't meet threshold are
    #  set to no data.

    def mem_fn(ras, ws):
        ras2 = Con(IsNull(ras), 0, 1)  # set na cells to 0 for focal stats purposes
        wsCell = int(math.ceil((ws * bfw) / desc.meanCellWidth))  # convert neighborhood size from ratio of bfw to number of cells
        print 'Membership function window size: ' + str(wsCell) + ' x ' + str(wsCell) + ' cells'
        if int(math.ceil((ws * bfw) / desc.meanCellWidth)) < 3:
            wsCell = 3
        neigh = NbrRectangle(wsCell, wsCell, 'CELL')  # set neighborhood size
        rCount = FocalStatistics(ras2, neigh, 'SUM', 'DATA')  # calculate sum of cells
        rCountNorm = rCount / float(wsCell * wsCell)  # normalize by window size
        rCountNorm2 = Con(IsNull(rCountNorm), 0, rCountNorm)
        rMem = ExtractByMask(rCountNorm2, inCh)
        return rMem

    #  --tier 2 raster to polygon function--

    #  reads in all tier 2 rasters, creates
    #  transition zones (i.e., all unclassified
    #  cells/no data cells in the bf channel)
    #  and merges them into a single shapefile.
    #  attributes tier1 and tier2 names shapefile fields

    def ras2poly_fn(inChDEM):
        rasters = []
        for root, dirs, files in os.walk(arcpy.env.workspace):
            for f in fnmatch.filter(files, 'Tier2_*'):
                if f.endswith('.tif'):
                    if 'Membership' not in f:
                        rasters.append(os.path.join(root, f))
        arcpy.MosaicToNewRaster_management(rasters, arcpy.env.workspace, 'tmp_rasMosaic.tif', number_of_bands=1)
        rSetNull = Con(IsNull('tmp_rasMosaic.tif'), 1, SetNull('tmp_rasMosaic.tif', 1, '"VALUE" >= 0'))
        rTransition = ExtractByMask(rSetNull, inChDEM)
        rTransition.save(os.path.join(outpath, 'Tier2_InChannel_TransitionZone.tif'))
        rasters.append(os.path.join(outpath, 'Tier2_InChannel_TransitionZone.tif'))
        for raster in rasters:
            print raster
            fn = os.path.splitext(os.path.basename(raster))[0]
            t1Name = fn.split('_')[1]
            t2Name = fn.split('_')[2]
            tmp_poly = fn + '.shp'
            arcpy.RasterToPolygon_conversion(raster, tmp_poly, 'NO_SIMPLIFY', 'VALUE')
            if 'Transition' in tmp_poly:
                arcpy.Dissolve_management(tmp_poly, 'tmp_poly2.shp', ['GRIDCODE'])
                arcpy.Delete_management(tmp_poly)
                arcpy.CopyFeatures_management('tmp_poly2.shp', tmp_poly)
            # Add Tier 1 and Tier 2 Names to attribute table
            arcpy.AddField_management(tmp_poly, 'Tier1', 'TEXT', '', '', 20)
            arcpy.AddField_management(tmp_poly, 'Tier2', 'TEXT', '', '', 25)
            arcpy.AddField_management(tmp_poly, 'Forcing', 'TEXT', '', '', 25)
            # Populate fields
            fields = ['Tier1', 'Tier2', 'Forcing']
            with arcpy.da.UpdateCursor(tmp_poly, fields) as cursor:
                for row in cursor:
                    row[0] = t1Name
                    row[1] = t2Name
                    row[2] = 'NA'
                    cursor.updateRow(row)
            arcpy.Delete_management(raster)
        shps = []
        for root, dirs, files in os.walk(arcpy.env.workspace):
            for f in fnmatch.filter(files, 'Tier2_*'):
                if f.endswith('.shp'):
                    shps.append(os.path.join(root, f))
        arcpy.Merge_management(shps, os.path.join(outpath, 'Tier2_InChannel.shp'))
        arcpy.CopyFeatures_management(os.path.join(outpath, 'Tier2_InChannel.shp'), os.path.join(outpath, 'Tier2_InChannel_Raw.shp'))
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

    #  --mean detrended dem--
    if not os.path.exists(os.path.join(evpath, os.path.splitext(os.path.basename(config.inDet))[0] + '_mean.tif')):
        meanDetDEM = FocalStatistics(det, neigh, 'MEAN', 'DATA')  # calculate mean z
        outMeanDetDEM = ExtractByMask(meanDetDEM, det)  # clip output to input
        outMeanDetDEM.save(os.path.join(evpath, os.path.splitext(os.path.basename(config.inDet))[0] + '_mean.tif'))  # save output
    else:
        outMeanDetDEM = Raster(os.path.join(evpath, os.path.splitext(os.path.basename(config.inDet))[0] + '_mean.tif'))

    #  --in channel mean dem--
    if not os.path.exists(os.path.join(evpath, 'inCh_' + os.path.basename(config.inDEM) + '.tif')):
        inChDEM = inCh * meanDEM
        inChDEM.save(os.path.join(evpath, 'inCh_' + os.path.basename(config.inDEM) + '.tif'))  # save output
    else:
        inChDEM = Raster(os.path.join(evpath, 'inCh_' + os.path.basename(config.inDEM) + '.tif'))

    #  --in channel mean detrended--
    if not os.path.exists(os.path.join(evpath, 'inCh_' + os.path.basename(config.inDet) + '.tif')):
        inChDetDEM = inCh * meanDetDEM
        inChDetDEM.save(os.path.join(evpath, 'inCh_' + os.path.basename(config.inDet) + '.tif'))  # save output
    else:
        inChDetDEM = Raster(os.path.join(evpath, 'inCh_' + os.path.basename(config.inDet) + '.tif'))

    #  --residual topography--
    if not os.path.exists(os.path.join(evpath, 'resTopo.tif')):
        neigh2 = NbrRectangle(bfw, bfw, 'MAP')  # set neighborhood size
        smDEM = FocalStatistics(inChDEM, neigh2, 'MEAN', 'DATA')  # calculate mean z ('smoothed' DEM)
        resTopo = inChDEM - smDEM  # calculate residual topogaphy
        resTopo.save(os.path.join(evpath, 'resTopo.tif')) # save output
    else:
        resTopo = Raster(os.path.join(evpath, 'resTopo.tif'))

    #  --bf channel slope--
    if not os.path.exists(os.path.join(evpath, 'smDEMSlope.tif')):
        #  a. calculate slope
        bfSlope = Slope(inChDEM, 'DEGREE')
        #  b. save output
        bfSlope.save(os.path.join(evpath, 'smDEMSlope.tif'))
    else:
        bfSlope = Raster(os.path.join(evpath, 'smDEMSlope.tif'))

    #  --normalized fill--
    if not os.path.exists(os.path.join(evpath, 'normFill.tif')):
        #  a. fill dem
        rFill = Fill(inChDEM)
        #  b. difference with dem
        rDiff = (rFill - inChDEM)
        #  c. get min fill value
        rMinResult = arcpy.GetRasterProperties_management(rDiff, 'MINIMUM')
        rMin = float(rMinResult.getOutput(0))
        #  d. get max fill value
        rMaxResult = arcpy.GetRasterProperties_management(rDiff, 'MAXIMUM')
        rMax = float(rMaxResult.getOutput(0))
        #  e.  normalize fill values
        normFill = (rDiff - rMin) / (rMax - rMin)
        #  f. save output
        normFill.save(os.path.join(evpath, 'normFill.tif'))
    else:
        normFill = Raster(os.path.join(evpath, 'normFill.tif'))

    #  --channel margin--
    if not os.path.exists(os.path.join(evpath, 'chMargin.tif')):
        #  a. remove any wePoly parts < 5% of total area
        wPolyElim = arcpy.EliminatePolygonPart_management(config.wPolyShp, 'in_memory/tmp_wPolyElim', 'PERCENT', '', 5, 'ANY')
        #  b. erase wPolyElim from bankfull polygon
        polyErase = arcpy.Erase_analysis(config.bfPolyShp, wPolyElim, 'in_memory/tmp_polyErase', '')
        #  c. buffer the output by 10% of the integrated wetted width
        bufferDist = 0.1 * ww
        polyBuffer = arcpy.Buffer_analysis(polyErase, 'in_memory/tmp_polyBuffer', bufferDist, 'FULL')
        #  d. clip the output to the bankull polygon
        arcpy.Clip_analysis(polyBuffer, config.bfPolyShp, 'EvidenceLayers/chMargin.shp')
        #  e. convert the output to a raster
        arcpy.PolygonToRaster_conversion('EvidenceLayers/chMargin.shp', 'FID', 'tmp_outRas.tif', 'CELL_CENTER', 'NONE', '0.1')
        #  f. set all cells inside/outside the bankfull ratser to 1/0
        cm = Con(IsNull('tmp_outRas.tif'), 0, 1)
        #  g. save the ouput
        cm.save(os.path.join(evpath, 'chMargin.tif'))
    else:
        cm = Raster(os.path.join(evpath, 'chMargin.tif'))

    # ---------------------------------
    #  tier 2 classification
    #  ---------------------------------
    #  ---------------------------------
    #  convexities
    #  ---------------------------------

    print '...classifying convexities...'

    rawCX = SetNull(resTopo, 1, '"VALUE" <= 0')  # set all residual topo values > 0 to 1

    #  calculate bank slope threshold
    slopeMeanResult = arcpy.GetRasterProperties_management(bfSlope, 'MEAN')
    slopeMean = float(slopeMeanResult.getOutput(0))
    slopeSTDResult = arcpy.GetRasterProperties_management(bfSlope, 'STD')
    slopeSTD = float(slopeSTDResult.getOutput(0))
    slopeTh = slopeMean + slopeSTD

    #  segregate banks
    cm2 = SetNull(cm, 1, '"VALUE" <= 0')  # set all values outside channel margin to NA
    cmSlope = rawCX * cm2 * bfSlope  # isolate slope values for channel margin convexities
    rawBank = SetNull(cmSlope, 1, '"VALUE" <= ' + str(slopeTh))  # apply slope threshold
    bank = area_fn(rawBank, 0.25)  # apply area threshold
    bank.save(os.path.join(outpath, 'Tier2_InChannel_Convexity_Bank.tif')) # save output

    # segregate bars
    # rawBar = SetNull(cmSlope, 1, '"VALUE" > 12') # qualifying cells in channel margin
    rawBar = SetNull((rawCX - Con(IsNull(bank), 0, 1)) == 0, 1)
    memBar = mem_fn(rawBar, 0.1)
    memBar.save(os.path.join(outpath, 'Tier2_InChannel_Convexity_Bars_Membership.tif'))
    threshBar = SetNull(memBar, 1, '"VALUE" <' + str(config.memTh))  # assign NA to clusters that don't meet count threshold
    bar = area_fn(threshBar, 1.0)  # apply area threshold
    bar.save(os.path.join(outpath, 'Tier2_InChannel_Convexity_Bars.tif'))  # save output

    #  ---------------------------------
    #  concavities
    #  ---------------------------------

    print '...classifying concavities...'

    posNormFill = SetNull(normFill, 1, '"VALUE" <= 0')
    negResTopo = SetNull(resTopo, 1, '"VALUE" > 0')  # set all residual topo values > 0 to 1
    rawCV = posNormFill + negResTopo
    memCV = mem_fn(rawCV, 0.1)
    memCV.save(os.path.join(outpath, 'Tier2_InChannel_Concavity_Membership.tif'))
    threshCV = SetNull(memCV, 1, '"VALUE" <' + str(config.memTh))  # assign NA to clusters that don't meet count threshold
    cv = area_fn(threshCV, 0.25)  # apply area threshold
    cv.save(os.path.join(outpath, 'Tier2_InChannel_Concavity.tif'))

    #  ---------------------------------
    #  planar features
    #  ---------------------------------

    print '...classifying planar features...'

    #  candidate planar: all cells with neg residual topo + that weren't filled
    #  !NOTE!: fill in all 'holes' in candidate planar raster with an area < concavity filter
    #  bc even though these aren't strictly planar cells: i) they may have a concave
    #  or convex signal due to noise in the data that wasn't filtered out during the
    #  dem smooth process, and ii) some planar units (i.e., rapids, cascades) have
    #  small concave or convex features in them
    rCon = Con(negResTopo - Con(normFill <= 0, 1, 0) == 0, 1)
    rConInv = Con(IsNull(rCon), 1)
    rGroup2 = RegionGroup(rConInv, 'FOUR')  # caclulate cell group (i.e., cluster)
    rArea2 = ZonalGeometry(rGroup2, 'Value', 'AREA', '0.1')  # calculate indiv cluster area
    rArea2Th = SetNull(rArea2, 1, '"VALUE" > ' + str(0.25 * bfw))
    rawPF = Con(IsNull(rCon), rArea2Th, rCon)

    memPF = mem_fn(rawPF, 0.1)
    memPF.save(os.path.join(outpath, 'Tier2_InChannel_Planar_Membership.tif'))
    threshPF = SetNull(memPF, 1, '"VALUE" <' + str(config.memTh))  # assign NA to clusters that don't meet count threshold
    shrinkPF = Shrink(threshPF, 1, 1)  # shrink/expand by 1 cell to remove thin bands - likely transitions
    expandPF = Expand(shrinkPF, 1, 1)
    pf = area_fn(expandPF, 1.0)  # apply area threshold
    pf.save(os.path.join(outpath, 'Tier2_InChannel_Planar.tif'))

    #  ---------------------------------
    #  merge t2 units into single output *.shp
    #  ---------------------------------

    print '...merging into single output shapefile...'

    ras2poly_fn(inChDEM)

    # ----------------------------------------------------------
    # Remove temporary files

    print '...removing intermediary surfaces...'

    for root, dirs, files in os.walk(arcpy.env.workspace):
        for f in fnmatch.filter(files, 'tmp_*'):
            os.remove(os.path.join(root, f))

    print '...done with Tier 2 classification.'

if __name__ == '__main__':
    main()
