# ToDo: Change all oid fields used in cursors to iterative ct

#  import required modules and extensions
import time
import arcpy
import config
import numpy
import math
import os
import fnmatch
import tempfile
from arcpy.sa import *
arcpy.CheckOutExtension('Spatial')
arcpy.CheckOutExtension("3D")


def tier3():

    print 'Starting Tier 3 classification...'

    #  create temporary workspace
    tmp_dir = tempfile.mkdtemp()

    #  environment settings
    arcpy.env.workspace = tmp_dir # set workspace to pf
    arcpy.env.overwriteOutput = True  # set to overwrite output

    #  set output paths
    evpath = os.path.join(config.workspace, 'EvidenceLayers')
    if config.runFolderName != 'Default' and config.runFolderName != '':
        outpath = os.path.join(config.workspace, 'Output', config.runFolderName)
    else:
        runFolders = fnmatch.filter(next(os.walk(os.path.join(config.workspace, 'Output')))[1], 'Run_*')
        runNum = int(max([i.split('_', 1)[1] for i in runFolders]))
        outpath = os.path.join(config.workspace, 'Output', 'Run_%03d' % runNum)

    #  clean up!
    #  search for existing tier 2 shapefiles or rasters
    #  if exist, delete from workspace otherwise will lead
    #  to errors in subsequent steps
    for root, dirs, files in os.walk(outpath):
        for file in files:
            if 'Tier3' in file:
                os.remove(os.path.join(outpath, file))

    arcpy.Delete_management('in_memory')

    #  import required rasters
    bf = Raster(os.path.join(config.workspace, 'EvidenceLayers/bfCh.tif'))  # created in 'tier1' module
    dem = Raster(os.path.join(evpath, os.path.splitext(os.path.basename(os.path.join(config.workspace, config.inDEM)))[0] + '_mean.tif'))

    #  set raster environment settings
    desc = arcpy.Describe(dem)
    arcpy.env.extent = desc.Extent
    arcpy.env.outputCoordinateSystem = desc.SpatialReference
    arcpy.env.cellSize = desc.meanCellWidth

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

    bfw = intWidth_fn(os.path.join(config.workspace, config.bfPolyShp), os.path.join(config.workspace, config.bfCL))
    ww = intWidth_fn(os.path.join(config.workspace, config.wPolyShp), os.path.join(config.workspace, config.wCL))

    #  ---------------------------------------
    #  calculate reach gradient and sinuosity
    #  --------------------------------------

    tmp_thalweg = arcpy.CopyFeatures_management(os.path.join(config.workspace, config.thalwegShp), 'in_memory/tmp_thalweg')
    arcpy.AddField_management(tmp_thalweg, 'Length', 'DOUBLE')
    with arcpy.da.UpdateCursor(tmp_thalweg, ['SHAPE@LENGTH', 'Length']) as cursor:
        for row in cursor:
            row[1] = round(row[0], 3)
            cursor.updateRow(row)

    maxLength = round(arcpy.SearchCursor(tmp_thalweg, "", "", "", 'Length' + " D").next().getValue('Length'), 3)  # Get 1st row in descending cursor sort

    exp = "{0}={1}".format('Length', maxLength)
    thalweg_lyr = arcpy.MakeFeatureLayer_management(tmp_thalweg, 'thalweg_lyr', exp)

    thalweg_pts = arcpy.FeatureVerticesToPoints_management('thalweg_lyr', 'in_memory/thalweg_pts', "BOTH_ENDS")
    ExtractMultiValuesToPoints(thalweg_pts, [[dem, 'demZ']])
    arcpy.PointDistance_analysis(thalweg_pts, thalweg_pts, 'tbl_thalweg_dist.dbf')

    maxZ = round(arcpy.SearchCursor(thalweg_pts, "", "", "", 'demZ' + " D").next().getValue('demZ'), 3)
    minZ = round(arcpy.SearchCursor(thalweg_pts, "", "", "", 'demZ' + " A").next().getValue('demZ'), 3)
    gradient = round(((maxZ - minZ) / maxLength) * 100, 3)

    straightLength = round(arcpy.SearchCursor('tbl_thalweg_dist.dbf', "", "", "", 'DISTANCE' + " D").next().getValue('DISTANCE'), 3)
    sinuosity = round(maxLength / straightLength, 3)

    totalLength = sum((r[0] for r in arcpy.da.SearchCursor(tmp_thalweg, ['Length'])))
    thalwegRatio = round(totalLength / maxLength, 3)

    #  ---------------------------------
    #  tier 3 evidence rasters + polygons
    #  ---------------------------------

    print '...deriving evidence rasters...'

    #  --bankfull surface slope--

    if not os.path.exists(os.path.join(evpath, 'bfSlope_Smooth.tif')):
        print '...bankfull surface slope...'

        #  a. convert bankfull polygon to points
        if round(0.25 * bfw, 1) < float(desc.meanCellWidth):
            distance = desc.meanCellWidth
        else:
            distance = round(0.25 * bfw, 1)
        bfLine = arcpy.FeatureToLine_management(os.path.join(config.workspace, config.bfPolyShp), 'in_memory/tmp_bfLine')
        bfPts = arcpy.CreateFeatureclass_management('in_memory', 'tmp_bfPts', 'POINT', '', 'DISABLED', 'DISABLED', dem)
        arcpy.AddField_management(bfPts, 'UID', 'LONG')
        arcpy.AddField_management(bfPts, 'lineDist', 'DOUBLE')

        search_fields = ['SHAPE@', 'OID@']
        insert_fields = ['SHAPE@', 'UID', 'lineDist']

        with arcpy.da.SearchCursor(bfLine, search_fields) as search:
            with arcpy.da.InsertCursor(bfPts, insert_fields) as insert:
                for row in search:
                    try:
                        line_geom = row[0]
                        length = float(line_geom.length)
                        count = distance
                        oid = int(1)
                        start = arcpy.PointGeometry(line_geom.firstPoint)
                        end = arcpy.PointGeometry(line_geom.lastPoint)

                        insert.insertRow((start, 0, 0))

                        while count <= length:
                            point = line_geom.positionAlongLine(count, False)
                            insert.insertRow((point, oid, count))

                            oid += 1
                            count += distance

                        insert.insertRow((end, (oid + 1), length))

                    except Exception as e:
                        arcpy.AddMessage(str(e.message))

        #  b. extract dem Z value to bankfull polygon points
        bfPtsZ = arcpy.CopyFeatures_management(bfPts, 'in_memory/tmp_bfPtsZ')
        ExtractMultiValuesToPoints(bfPtsZ, [[dem, 'demZ']], 'NONE')

        #  c. remove points where demZ = -9999 (so, < 0) and where points
        #     intersect wePoly (this is to remove points at DS and US extent of reach)
        with arcpy.da.UpdateCursor(bfPtsZ, 'demZ') as cursor:
            for row in cursor:
                if row[0] <= 0.0:
                    cursor.deleteRow()

        arcpy.MakeFeatureLayer_management(bfPtsZ, 'tmp_bfPtsZ_lyr')
        arcpy.SelectLayerByLocation_management('tmp_bfPtsZ_lyr', 'WITHIN_A_DISTANCE', os.path.join(config.workspace, config.wPolyShp), str(desc.meanCellWidth) + ' Meters')
        if int(arcpy.GetCount_management('tmp_bfPtsZ_lyr').getOutput(0)) > 0:
            arcpy.DeleteFeatures_management('tmp_bfPtsZ_lyr')

        #  d. create bankfull elevation raster
        bfe_tin = arcpy.CreateTin_3d('bfe_tin', desc.SpatialReference, [[bfPtsZ, 'demZ', 'masspoints'], [os.path.join(config.workspace, config.bfPolyShp), '<None>', 'hardclip']])
        tmp_bfe = arcpy.TinRaster_3d(bfe_tin, 'in_memory/bfe_ras', data_type = 'FLOAT', method = 'NATURAL_NEIGHBORS', sample_distance = "CELLSIZE 0.1")

        #  e. create bfe slope raster
        bfSlope = Slope(tmp_bfe, 'DEGREE')
        bfSlope.save(os.path.join(evpath, 'bfSlope.tif'))

        #  f. calculate mean bfe slope over bfw neighborhood
        neighborhood = NbrRectangle(bfw, bfw, 'MAP')
        slope_focal = FocalStatistics(bfSlope, neighborhood, 'MEAN')

        #  g. clip to bankfull polygon
        bfSlope_Smooth = ExtractByMask(slope_focal, os.path.join(config.workspace, config.bfPolyShp))

        #  h. save output
        bfSlope_Smooth.save(os.path.join(evpath, 'bfSlope_Smooth.tif'))

        #  e. create bfe slope raster
        bfSlope2 = Slope(tmp_bfe, 'PERCENT_RISE')
        bfSlope2.save(os.path.join(evpath, 'bfSlope_Percent.tif'))

        #  f. calculate mean bfe slope over bfw neighborhood
        neighborhood = NbrRectangle(bfw, bfw, 'MAP')
        slope_focal2 = FocalStatistics(bfSlope2, neighborhood, 'MEAN')

        #  g. clip to bankfull polygon
        bfSlope_Smooth2 = ExtractByMask(slope_focal2, os.path.join(config.workspace, config.bfPolyShp))

        #  h. save output
        bfSlope_Smooth2.save(os.path.join(evpath, 'bfSlope_Percent_Smooth.tif'))

        #  i. delete intermediate fcs
        fcs = [bfPts, bfLine, bfPtsZ]
        for fc in fcs:
            arcpy.Delete_management(fc)
    else:
        bfSlope = Raster(os.path.join(evpath, 'bfSlope.tif'))
        bfSlope_Smooth = Raster(os.path.join(evpath, 'bfSlope_Smooth.tif'))

    #  --bf slope smoothed slope category thresholds--
    # VLow < 0.6 deg
    # Low = 0.6-2.3 deg
    # Mod = 2.3-4.3 deg
    # High = 4.3-11.3 deg
    # VHigh > 11.3 deg

    if not os.path.exists(os.path.join(evpath, 'bfSlope_Smooth_Cat.shp')):
        print '...bankfull surface slope categories...'
        bfSlope_SmoothCat_ras = Con(bfSlope_Smooth < 2.3, 1, Con(bfSlope_Smooth < 4.3, 2, Con(bfSlope_Smooth < 11.3, 3, 4)))
        bfSlope_Smooth_Cat = arcpy.RasterToPolygon_conversion(bfSlope_SmoothCat_ras, os.path.join(evpath, 'bfSlope_Smooth_Cat.shp'), 'NO_SIMPLIFY', 'VALUE')
        arcpy.AddField_management(bfSlope_Smooth_Cat, 'bfSlopeCat', 'TEXT', '', '', 10)
        with arcpy.da.UpdateCursor(bfSlope_Smooth_Cat, ['GRIDCODE', 'bfSlopeCat']) as cursor:
            for row in cursor:
                if row[0] == 1:
                    row[1] = 'Low'
                elif row[0] == 2:
                    row[1] = 'Moderate'
                elif row[0] == 3:
                    row[1] = 'High'
                elif row[0] == 4:
                    row[1] = 'Very High'
                else:
                    row[1] = 'NA'
                cursor.updateRow(row)
        arcpy.MakeFeatureLayer_management(os.path.join(evpath, 'bfSlope_Smooth_Cat.shp'), 'bfSlope_lyr')
    else:
        arcpy.MakeFeatureLayer_management(os.path.join(evpath, 'bfSlope_Smooth_Cat.shp'), 'bfSlope_lyr')

    #  --bf slope smoothed slope categories--

    if not os.path.exists(os.path.join(evpath, 'bedSlopeSD_Cat.shp')):
        print '...bedslope standard deviation...'
        #  f. calculate mean bfe slope over bfw neighborhood
        neighborhood = NbrRectangle(bfw, bfw, 'MAP')
        bedSlopeSD_raw = FocalStatistics(Raster(os.path.join(evpath, 'slope_inCh_' + os.path.basename(os.path.join(config.workspace, config.inDEM)))), neighborhood, 'STD')

        bedSlopeSD = ExtractByMask(bedSlopeSD_raw, os.path.join(config.workspace, config.bfPolyShp))

        #  h. save output
        bedSlopeSD.save(os.path.join(evpath, 'bedSlopeSD.tif'))


        bedSlopeSD_Cat_ras = Con(bedSlopeSD < 5.5, 1, 2)
        bedSlopeSD_Cat = arcpy.RasterToPolygon_conversion(bedSlopeSD_Cat_ras, os.path.join(evpath, 'bedSlopeSD_Cat.shp'), 'NO_SIMPLIFY', 'VALUE')
        arcpy.MakeFeatureLayer_management(os.path.join(evpath, 'bedSlopeSD_Cat.shp'), 'bedSlope_lyr')
    else:
        arcpy.MakeFeatureLayer_management(os.path.join(evpath, 'bedSlopeSD_Cat.shp'), 'bedSlope_lyr')

    #  --channel edge polygon--

    if not os.path.exists(os.path.join(evpath, 'channelEdge.shp')):
        print '...channel edge...'

        # calculate distance from main centerline end points
        bfCL = arcpy.CopyFeatures_management(os.path.join(config.workspace, config.bfCL), 'in_memory/tmp_bfCL')
        bfCL_lyr = arcpy.MakeFeatureLayer_management(bfCL, 'bfCL_lyr', """ "Channel" = 'Main' """)
        bfCL_pts = arcpy.FeatureVerticesToPoints_management(bfCL_lyr, 'in_memory/bfCL_pts', "BOTH_ENDS")
        bfCLDist = EucDistance(bfCL_pts, '', desc.meanCellWidth)

        outCh = Con(bf < 1, 1)
        inCh_buffer = Con(EucDistance(Con(bf > 0, 1), 2 * float(desc.meanCellWidth), desc.meanCellWidth) > 0, 1)
        outChEdgeRas = Con(bfCLDist > (0.5 * bfw), Con(IsNull(outCh), inCh_buffer, outCh), outCh)
        #arcpy.CopyRaster_management(outChEdgeRas, os.path.join(evpath, 'tmp_outChEdgeRas.tif'))

        outChEdge = arcpy.RasterToPolygon_conversion(outChEdgeRas, 'in_memory/outChEdge', 'NO_SIMPLIFY', 'VALUE')

        with arcpy.da.UpdateCursor(outChEdge, ['SHAPE@Area']) as cursor:
            for row in cursor:
                if row[0] < bfw:
                    cursor.deleteRow()

        # create edge id field
        arcpy.AddField_management(outChEdge, 'EdgeID', 'SHORT')
        ct = 1
        with arcpy.da.UpdateCursor(outChEdge, ['EdgeID']) as cursor:
            for row in cursor:
                row[0] = ct
                ct += 1
                cursor.updateRow(row)

        arcpy.EliminatePolygonPart_management(os.path.join(config.workspace, config.bfPolyShp), 'in_memory/bfelim', 'AREA', 10*bfw, '', 'CONTAINED_ONLY')
        arcpy.Erase_analysis('in_memory/bfelim', os.path.join(config.workspace, config.bfPolyShp), 'in_memory/tmp_erase')

        #  f. attribute edge as being mid-channel or not
        arcpy.AddField_management(outChEdge, 'midEdge', 'TEXT', '', '', 5)
        arcpy.MakeFeatureLayer_management(outChEdge, 'outChEdge_lyr')
        arcpy.SelectLayerByLocation_management('outChEdge_lyr', 'INTERSECT', 'in_memory/tmp_erase', '', 'NEW_SELECTION')
        with arcpy.da.UpdateCursor('outChEdge_lyr', 'midEdge') as cursor:
            for row in cursor:
                row[0] = 'Yes'
                cursor.updateRow(row)

        # if unit does not intersect thalweg assign 'No'
        arcpy.SelectLayerByAttribute_management('outChEdge_lyr', 'SWITCH_SELECTION')
        with arcpy.da.UpdateCursor('outChEdge_lyr', 'midEdge') as cursor:
            for row in cursor:
                row[0] = 'No'
                cursor.updateRow(row)

        # remove mid-edge polygons that are completely surrounded by a mound
        arcpy.SelectLayerByAttribute_management('outChEdge_lyr', 'NEW_SELECTION', """ "midEdge" = 'Yes' """)
        arcpy.MakeFeatureLayer_management(os.path.join(outpath, 'Tier2_InChannel_Transition.shp'), 'forms_lyr')

        edge_forms = arcpy.SpatialJoin_analysis('outChEdge_lyr', 'forms_lyr', 'in_memory/tmp_edge_forms', 'JOIN_ONE_TO_MANY', '', '', 'INTERSECT')
        edge_forms_tbl = arcpy.Frequency_analysis(edge_forms, 'tbl_edge_forms.dbf', ['EdgeID'])
        arcpy.AddField_management(edge_forms_tbl, 'formCount', 'SHORT')
        arcpy.CalculateField_management(edge_forms_tbl, 'formCount', '[FREQUENCY]')
        arcpy.JoinField_management('outChEdge_lyr', 'EdgeID', edge_forms_tbl, 'EdgeID', ['formCount'])

        arcpy.SelectLayerByAttribute_management('forms_lyr', 'NEW_SELECTION', """ "UnitForm" = 'Mound' """)
        edge_mounds = arcpy.SpatialJoin_analysis('outChEdge_lyr', 'forms_lyr', 'in_memory/tmp_edge_mounds', 'JOIN_ONE_TO_MANY', '', '', 'INTERSECT')
        edge_mounds_tbl = arcpy.Frequency_analysis(edge_mounds, 'tbl_edge_mounds.dbf', ['EdgeID'])
        arcpy.AddField_management(edge_mounds_tbl, 'moundCount', 'SHORT')
        arcpy.CalculateField_management(edge_mounds_tbl, 'moundCount', '[FREQUENCY]')
        arcpy.JoinField_management('outChEdge_lyr', 'EdgeID', edge_mounds_tbl, 'EdgeID', ['moundCount'])

        with arcpy.da.UpdateCursor('outChEdge_lyr', ['formCount', 'moundCount']) as cursor:
            for row in cursor:
                if row[0] == 1 and row[1] == 1:
                    cursor.deleteRow()

        arcpy.CopyFeatures_management(outChEdge, os.path.join(evpath, 'channelEdge.shp'))

        arcpy.MakeFeatureLayer_management(os.path.join(evpath, 'channelEdge.shp'), 'edge_lyr')

    else:
        arcpy.MakeFeatureLayer_management(os.path.join(evpath, 'channelEdge.shp'), 'edge_lyr')

    #  --thalweg high points--

    if not os.path.exists(os.path.join(evpath, 'potentialRiffCrests.shp')):
        print '...thalweg high points...'

        #  a. create thalweg points along thalweg polyline [distance == dem cell size]
        distance = float(desc.meanCellWidth)
        thalPts = arcpy.CreateFeatureclass_management('in_memory', 'tmp_thalPts', 'POINT', '', 'DISABLED', 'DISABLED', dem)
        arcpy.AddField_management(thalPts, 'UID', 'LONG')
        arcpy.AddField_management(thalPts, 'thalDist', 'DOUBLE')

        search_fields = ['SHAPE@', 'OID@']
        insert_fields = ['SHAPE@', 'UID', 'thalDist']

        with arcpy.da.SearchCursor(os.path.join(config.workspace, config.thalwegShp), search_fields) as search:
            with arcpy.da.InsertCursor(thalPts, insert_fields) as insert:
                for row in search:
                    try:
                        line_geom = row[0]
                        length = float(line_geom.length)
                        count = distance
                        oid = int(1)
                        start = arcpy.PointGeometry(line_geom.firstPoint)
                        end = arcpy.PointGeometry(line_geom.lastPoint)

                        insert.insertRow((start, 0, 0))

                        while count <= length:
                            point = line_geom.positionAlongLine(count, False)
                            insert.insertRow((point, oid, count))

                            oid += 1
                            count += distance

                        insert.insertRow((end, (oid + 1), length))

                    except Exception as e:
                        arcpy.AddMessage(str(e.message))

        #  b. extract dem value to thalweg points
        ExtractMultiValuesToPoints(thalPts, [[dem, 'demZ']])

        #  c. remove any thalweg points where DEM Z is < 0
        #     this assumes that no data/null values are assigned  -9999 during step b
        with arcpy.da.UpdateCursor(thalPts, 'demZ') as cursor:
            for row in cursor:
                if row[0] <= 0.0:
                    cursor.deleteRow()

        # #  d1. method 1: linear regression analysis
        # #  d1a. run regression on thalweg points using OLS
        # #       demZ ~ thalDist
        # arcpy.OrdinaryLeastSquares_stats(thalPts, 'UID', 'EvidenceLayers/thalwegPoints_OLS.shp', 'demZ', 'thalDist')
        # arcpy.CopyFeatures_management('EvidenceLayers/thalwegPoints_OLS.shp', 'EvidenceLayers/potentialRiffCrests_OLS.shp')
        #
        # #  d1b. remove any thalweg points where standardized residual < 1.0 sd
        # with arcpy.da.UpdateCursor('EvidenceLayers/thalwegPoints_OLS.shp', 'StdResid') as cursor:
        #     for row in cursor:
        #         if row[0] < 1.0:
        #             cursor.deleteRow()

        #  d2. method 2: 3rd order polynomial trend surface
        #  d2a. create trend surface using thalweg points
        outTrend = Trend(thalPts, 'demZ', 0.1, 3, 'LINEAR')
        #  d2b. extract trend DEM Z value to each thalweg point
        ExtractMultiValuesToPoints(thalPts, [[outTrend, 'trendZ']])

        #  d2c. calculate residual and standardized residual btwn DEM and trend DEM Z
        arcpy.AddField_management(thalPts, 'trResid', 'DOUBLE')
        arcpy.AddField_management(thalPts, 'trStResid', 'DOUBLE')
        arcpy.CalculateField_management(thalPts, 'trResid', '[demZ] - [trendZ]', 'VB')
        arr = arcpy.da.FeatureClassToNumPyArray(thalPts, ['trResid'])
        trResid_sd = arr['trResid'].std()
        arcpy.CalculateField_management(thalPts, 'trStResid', '[trResid] /' + str(trResid_sd), 'VB')

        #  d2d. remove any thalweg points where standardized residual < 1.0 sd
        with arcpy.da.UpdateCursor(thalPts, 'trStResid') as cursor:
            for row in cursor:
                if row[0] < 1.0:
                    cursor.deleteRow()

        arcpy.CopyFeatures_management(thalPts, os.path.join(evpath, 'potentialRiffCrests.shp'))
        #  e. delete intermediate fcs
        arcpy.Delete_management(thalPts)

    #  --meander bends--

    if not os.path.exists(os.path.join(evpath, 'mBendIndex.tif')):
        print '...meander bends...'

        #  a. smooth bankfull polygon
        bfElim2 = arcpy.EliminatePolygonPart_management(os.path.join(config.workspace, config.bfPolyShp), 'in_memory/bfelim2', 'AREA', 10*bfw, '', 'ANY')
        bfSmooth = arcpy.cartography.SmoothPolygon(bfElim2, 'in_memory/bfsmooth', "PAEK", round(bfw / 2))
        bfRaw = arcpy.PolygonToRaster_conversion(bfSmooth, 'FID', 'in_memory/bfRaw', 'CELL_CENTER')

        #  b. set cells inside/outside bankfull channel polygon to 1/0 and clip to dem
        bfRas = ExtractByMask(Con(IsNull(bfRaw), 0, 1), dem)

        #  c. isolate wet/dry bf channel
        bfWet = Con(bfRas == 1, 1)
        bfDry = Con(bfRas == 0, 1)

        #  d. delineate edge cells
        #  buffer bf channel by one cell using euclidean distance
        bfChDist = EucDistance(bfDry, float(desc.meanCellWidth), desc.meanCellWidth)


        #  define edge and assign value of 0
        bfEdgeRaw = ExtractByMask(Con(bfChDist > 0, 0), bfWet)

        # calculate distance from thalweg end points
        # set cells that are < 0.75*bfw to no data
        bfCL = arcpy.CopyFeatures_management(os.path.join(config.workspace, config.bfCL), 'in_memory/tmp_bfCL')
        bfCL_lyr = arcpy.MakeFeatureLayer_management(bfCL, 'bfCL_lyr', """ "Channel" = 'Main' """)
        bfCL_pts = arcpy.FeatureVerticesToPoints_management(bfCL_lyr, 'in_memory/bfCL_pts', "BOTH_ENDS")
        bfCLDist = EucDistance(bfCL_pts, '', desc.meanCellWidth)
        bfEdge = ExtractByMask(Con(bfCLDist >= (0.75 * bfw), 0), bfEdgeRaw)

        #  for each edge cell, get count of number of wet and dry cells
        #  note: In most cases the CHaMP surveys don't extend that far from the bfWet channel.
        #  as such, we can't simply count and difference wet/dry cells (we could if the window
        #  size used fell fully within the survey area) bc the number of wet cells will always be greater
        #  than the number of dry cells resulting in most of the channel being classifies
        #  as the inside of a bend.  As a work around, here we indirectly extend
        #  the number of dry cells by first getting a count of the wet and then infer the remainder of
        #  cells in the window are dry cells. This results in some false positives at the ds and us
        #  extent of the reach.
        nCellWidth = round(bfw / desc.meanCellWidth)
        neigh = NbrRectangle(nCellWidth, nCellWidth, 'CELL')  # set neighborhood size
        ebfWet = Con(IsNull(bfEdge), Con(IsNull(bfEdgeRaw), bfWet), bfEdge)
        wetCount = Con(ebfWet == 0, FocalStatistics(ebfWet, neigh, 'SUM'))
        dryCount = Con(bfEdge == 0, (nCellWidth * nCellWidth) - wetCount)

        # # count number of edge cells in each window
        bfEdgeCount = Con(bfEdge == 0, FocalStatistics(Con(bfEdgeRaw == 0, 1), neigh, 'SUM') - 1)

        #  for each edge cell, difference wet and dry cells to
        #  negative value = inside of bend
        #  positive values = outside of bend
        rawIndex = Con(bfEdge == 0, dryCount - wetCount - bfEdgeCount)

        #  normalize output as ratio of total (non-Edge) cells in window
        nIndex = rawIndex / (nCellWidth * nCellWidth)

        #  run mean filter to smooth output
        #  arguments:
        #       ras = input raster
        #       n = number of passes
        def mf_fn(ras, n):
            ct = 1
            fRas = ras
            while ct <= n:
                mf = FocalStatistics(fRas, neigh, 'MEAN')
                if ct < n:
                    mfClip = ExtractByMask(mf, bfEdge)
                    fRas = mfClip
                    ct += 1
                else:
                    mfClip = ExtractByMask(mf, bfEdgeRaw)
                    fRas = mfClip
                    ct += 1
            return fRas

        #  run mean filter to smooth output
        mIndex = mf_fn(nIndex, 3)
        #fIndex = mf_fn(rawIndex, bfEdgeRaw, 5)

        #  normalize output as ratio of total (non-Edge) cells in window
        #mIndex = fIndex / (nCellWidth * nCellWidth)
        mIndex.save(os.path.join(evpath, 'mBendIndex.tif'))

    else:
        mIndex = Raster((os.path.join(evpath, 'mBendIndex.tif')))

    #  --width expansion ratio--

    print '...width expansion ratio...'

    #  in DS direction width ratios  </> 1 indicate channel constriction/expansion
    #  a. calculate xs width ratio (xs[n+1]length/xs[n]length) separately for the main channel and each side channel
    #  b. assign minimum and maximum width ratio to each channel unit polygon

    #  step 1: copy inputs to temporary *.shps
    bfxs = arcpy.CopyFeatures_management(os.path.join(config.workspace, config.bfXS), 'in_memory/tmp_bfxs')
    bfCL = arcpy.CopyFeatures_management(os.path.join(config.workspace, config.bfCL), 'in_memory/tmp_bfCL')

    #  step 2: add unique line identifier to centerlines [based on CL id and channel type]
    arcpy.AddField_management(bfCL, 'ChCLID', 'TEXT', '', '', 15)

    fieldnames = [field.name for field in arcpy.ListFields(bfCL)]
    if 'CLID' not in fieldnames:
        ct = 1
        arcpy.AddField_management(bfCL, 'CLID', 'SHORT')
        with arcpy.da.UpdateCursor(bfCL, 'CLID') as cursor:
            for row in cursor:
                row[0] = ct
                ct += 1
                cursor.updateRow(row)

    fields = ['Channel', 'CLID', 'ChCLID']
    with arcpy.da.UpdateCursor(bfCL, fields) as cursor:
        for row in cursor:
            row[2] = row[0] + str(row[1])
            cursor.updateRow(row)

    #  step 3: delete non valid [i.e., 'IsValid == 0'] bankfull cross sections
    fields = ['IsValid']
    with arcpy.da.UpdateCursor(bfxs, fields) as cursor:
        for row in cursor:
            if row[0] != 1:
                cursor.deleteRow()

    #  step 4: join ChCLID field from bankfull centerline to cross sections
    bfxs_join = arcpy.SpatialJoin_analysis(bfxs, bfCL, 'in_memory/tmp_bfxs_join', 'JOIN_ONE_TO_ONE', 'KEEP_ALL', '', 'INTERSECT')

    #  step 5: add fields to bankfull cross sections
    arcpy.AddField_management(bfxs_join, 'width', 'DOUBLE')
    arcpy.AddField_management(bfxs_join, 'nwidth', 'DOUBLE')
    arcpy.AddField_management(bfxs_join, 'widthRatio', 'DOUBLE')

    #  step 6: use update cursor and width list to calculate widths and width ratio
    #          this is run separately for the main channel and each side channel (unique identifier: 'ChCLID')
    #          wList populated to use next DS cross section (or row) width in update cursor
    data = arcpy.da.TableToNumPyArray(bfxs_join, 'ChCLID')
    clids = numpy.unique(data['ChCLID'])

    fields = ['ChCLID', 'SHAPE@LENGTH', 'width', 'nwidth', 'widthRatio']

    for clid in clids:
        wList = []
        index = 0
        with arcpy.da.SearchCursor(bfxs_join, fields) as cursor:
            for row in cursor:
                if row[0] == clid:
                    wList.append(row[1])
        with arcpy.da.UpdateCursor(bfxs_join, fields) as cursor:
            for row in cursor:
                if row[0] == clid:
                    row[2] = row[1]
                    if index + 1 < len(wList):
                        row[3] = wList[index + 1]
                        row[4] = float(row[3] / row[2])
                    if index + 1 == len(wList):
                        row[3] = -9999
                        row[4] = -9999
                    index += 1
                    cursor.updateRow(row)

    with arcpy.da.UpdateCursor(bfxs_join, fields) as cursor:
        for row in cursor:
            if row[4] == -9999:
                cursor.deleteRow()

    # j. delete intermediate fcs
    arcpy.Delete_management(bfCL)

    #  --channel nodes--

    if not os.path.exists(os.path.join(evpath, 'channelNodes.shp')):
        print '...channel nodes...'

        tmp_thalwegs = arcpy.CopyFeatures_management(os.path.join(config.workspace, config.thalwegShp), 'in_memory/thalwegs')

        arcpy.AddField_management(tmp_thalwegs, 'ThalwegID', 'SHORT')
        ct = 1
        with arcpy.da.UpdateCursor(tmp_thalwegs, ['ThalwegID']) as cursor:
            for row in cursor:
                row[0] = ct
                ct += 1
                cursor.updateRow(row)

        chNodes_mp = arcpy.Intersect_analysis(tmp_thalwegs, 'in_memory/tmp_chNodes_multiPart', 'NO_FID', '', 'POINT')

        if arcpy.management.GetCount(chNodes_mp)[0] != '0':

            #chNodes_sp = arcpy.MultipartToSinglepart_management(chNodes_mp, 'in_memory/chNodes_sp')

            thalwegs_pts = arcpy.FeatureVerticesToPoints_management(tmp_thalwegs, 'in_memory/thalwegs_pts', "BOTH_ENDS")

            arcpy.AddField_management(thalwegs_pts, 'ChNodeID', 'SHORT')
            ct = 1
            with arcpy.da.UpdateCursor(thalwegs_pts, ['ChNodeID']) as cursor:
                for row in cursor:
                    row[0] = ct
                    ct += 1
                    cursor.updateRow(row)

            arcpy.AddField_management(tmp_thalwegs, 'From_', 'DOUBLE')
            arcpy.AddField_management(tmp_thalwegs, 'To_', 'DOUBLE')

            fields = ['SHAPE@LENGTH', 'From_', 'To_']
            with arcpy.da.UpdateCursor(tmp_thalwegs, fields) as cursor:
                for row in cursor:
                    row[1] = 0.0
                    row[2] = row[0]
                    cursor.updateRow(row)

            mainCL_Route = arcpy.CreateRoutes_lr(tmp_thalwegs, 'ThalwegID', 'in_memory/mainCL_Route', 'TWO_FIELDS', 'From_', 'To_')

            #arcpy.CopyFeatures_management(mainCL_Route, os.path.join(evpath, 'tmp_mainCL_Route.shp'))
            #arcpy.LocateFeaturesAlongRoutes_lr(thalwegs_pts, mainCL_Route, 'ThalwegID', float(desc.meanCellWidth), 'tbl_Routes.dbf', 'RID POINT MEAS')

            arcpy.LocateFeaturesAlongRoutes_lr(thalwegs_pts, mainCL_Route, 'ThalwegID', '', 'tbl_Routes.dbf', 'ThalwegID POINT MEAS', 'ALL')
            #arcpy.LocateFeaturesAlongRoutes_lr(thalwegs_pts, mainCL_Route, 'ThalwegID', '', 'tbl_Routes.dbf', 'RID POINT MEAS')

            with arcpy.da.UpdateCursor('tbl_Routes.dbf', ['ThalwegID', 'ThalwegID2']) as cursor:
                for row in cursor:
                    if row[0] != row[1]:
                        cursor.deleteRow()

            arcpy.JoinField_management(thalwegs_pts, 'ChNodeID', 'tbl_Routes.dbf', 'ChNodeID', ['MEAS'])

            arcpy.Statistics_analysis(thalwegs_pts, 'tbl_chNodeMax.dbf', [['MEAS', 'MAX']], 'ThalwegID')

            arcpy.JoinField_management(thalwegs_pts, 'ThalwegID', 'tbl_chNodeMax.dbf', 'ThalwegID', ['MAX_MEAS'])

            arcpy.CopyRows_management('tbl_chNodeMax.dbf', os.path.join(evpath, 'tbl_chNodeMax.dbf'))
            arcpy.CopyRows_management('tbl_Routes.dbf', os.path.join(evpath, 'tbl_Routes.dbf'))

            arcpy.AddField_management(thalwegs_pts, 'ChNodeType', 'TEXT', 10)
            arcpy.AddField_management(thalwegs_pts, 'ThNodeType', 'TEXT', 10)
            fields = ['MEAS', 'MAX_MEAS', 'ThNodeType']
            with arcpy.da.UpdateCursor(thalwegs_pts, fields) as cursor:
                for row in cursor:
                    if row[0] < row[1]:
                        row[2] = 'US'
                    else:
                        row[2] = 'DS'
                    cursor.updateRow(row)

            arcpy.MakeFeatureLayer_management(thalwegs_pts, 'thalwegs_pts_lyr')

            arcpy.SelectLayerByLocation_management('thalwegs_pts_lyr', 'INTERSECT', chNodes_mp)

            with arcpy.da.UpdateCursor('thalwegs_pts_lyr', ['ThNodeType', 'ChNodeType']) as cursor:
                for row in cursor:
                    if row[0] == 'US':
                        row[1] = 'Diffluence'
                    else:
                        row[1] = 'Confluence'
                    cursor.updateRow(row)

            arcpy.CopyFeatures_management('thalwegs_pts_lyr', os.path.join(evpath, 'channelNodes.shp'))

    else:
        tmp_thalwegs = arcpy.CopyFeatures_management(os.path.join(config.workspace, config.thalwegShp), 'in_memory/thalwegs')

        # gu attributes function

    def guAttributes(units):

        fields = arcpy.ListFields(units)
        keep = ['ValleyUnit', 'UnitShape', 'UnitForm', 'GU', 'GUKey', 'FlowUnit']
        drop = []
        for field in fields:
            if not field.required and field.name not in keep and field.type <> 'Geometry':
                drop.append(field.name)
        if len(drop) > 0:
            arcpy.DeleteField_management(units, drop)

        # add attribute fields to tier 2 polygon shapefile
        nfields = [('SubGU', 'TEXT', '35'), ('UnitID', 'SHORT', ''),
                   ('Channel', 'TEXT', '5'),
                   ('Forcing', 'TEXT', '25'), ('Perimeter', 'DOUBLE', ''), ('ElongRatio', 'DOUBLE', ''),
                   ('Morphology', 'TEXT', '20'),
                   ('Position', 'TEXT', '20'), ('Orient', 'DOUBLE', ''), ('OrientCat', 'TEXT', '15'),
                   ('bfSlope', 'DOUBLE', ''), ('bfSlopeSm', 'DOUBLE', ''),
                   ('bedSlope', 'DOUBLE', '')]

        for nfield in nfields:
            arcpy.AddField_management(units, nfield[0], nfield[1], '', '', nfield[2])

        if not 'Area' in [f.name for f in arcpy.ListFields(units)]:
            arcpy.AddField_management(units, 'Area', 'DOUBLE')

        if 'OnThalweg' in [f.name for f in arcpy.ListFields(units)]:
            arcpy.DeleteField_management(units, ['OnThalweg'])

        print "Calculating tier 3 GU attributes..."

        #  create unit id field to make sure joins correctly execute
        #  populate area, perimeter attribute fields
        print '...unit area, perimeter...'
        fields = ['OID@', 'UnitID', 'Forcing', 'SHAPE@Area', 'Area', 'SHAPE@LENGTH', 'Perimeter']
        with arcpy.da.UpdateCursor(units, fields) as cursor:
            for row in cursor:
                row[1] = row[0]
                row[2] = 'NA'
                row[4] = row[3]
                row[6] = row[5]
                cursor.updateRow(row)

        print "...unit length, width, length to width ratio and orientation..."

        #  calculate unit length, width, orientation (i.e., angle) using minimum bounding polygon
        ## Alternative width calculation: width = area / perimeter * 4
        unit_minbound = arcpy.MinimumBoundingGeometry_management(units, 'in_memory/units_minbound',
                                                                 'RECTANGLE_BY_WIDTH', '', '', 'MBG_FIELDS')
        arcpy.AddField_management(unit_minbound, 'Width', 'DOUBLE')
        arcpy.AddField_management(unit_minbound, 'Length', 'DOUBLE')
        arcpy.AddField_management(unit_minbound, 'LtoWRatio', 'DOUBLE')
        arcpy.AddField_management(unit_minbound, 'bfwRatio', 'DOUBLE')
        arcpy.AddField_management(unit_minbound, 'unitOrient', 'DOUBLE')
        fields = ['Area', 'MBG_Length', 'MBG_Orientation', 'Width', 'Length', 'unitOrient', 'LtoWRatio', 'bfwRatio']
        with arcpy.da.UpdateCursor(unit_minbound, fields) as cursor:
            for row in cursor:
                row[4] = row[1]
                row[3] = row[0] / row[4]
                row[6] = row[4] / row[3]
                if row[2] > 90.0:
                    row[5] = row[2] - 180
                else:
                    row[5] = row[2]
                row[7] = row[3] / bfw
                cursor.updateRow(row)
        arcpy.JoinField_management(units, 'UnitID', unit_minbound, 'UnitID',
                                   ['Length', 'Width', 'LtoWRatio', 'bfwRatio', 'unitOrient'])

        print "...unit orientation relative to centerline..."

        #  calculate centerline orientation for each unit

        #  a. create points at regular interval (bfw) along bankfull centerlines
        #     run seperatly for each centerline
        cl_pts = arcpy.CreateFeatureclass_management('in_memory', 'cl_pts', 'POINT', '', 'DISABLED', 'DISABLED', dem)
        arcpy.AddField_management(cl_pts, 'UID', 'LONG')
        arcpy.AddField_management(cl_pts, 'lineDist', 'DOUBLE')

        search_fields = ['SHAPE@', 'OID@']
        insert_fields = ['SHAPE@', 'UID', 'lineDist']
        distance = bfw
        with arcpy.da.SearchCursor(os.path.join(config.workspace, config.bfCL), search_fields) as search:
            with arcpy.da.InsertCursor(cl_pts, insert_fields) as insert:
                for row in search:
                    try:
                        line_geom = row[0]
                        length = float(line_geom.length)
                        count = distance
                        oid = int(1)

                        while count <= length:
                            point = line_geom.positionAlongLine(count, False)
                            insert.insertRow((point, oid, count))
                            oid += 1
                            count += distance

                    except Exception as e:
                        arcpy.AddMessage(str(e.message))

        # b. split bankfull centerline at centerline interval points
        bfcl_split = arcpy.SplitLineAtPoint_management(os.path.join(config.workspace, config.bfCL), cl_pts,
                                                       'in_memory/bfcl_split', '0.1 Meters')

        #  d. get centerline segment oreintation using minimum bounding geometry
        cl_minbound = arcpy.MinimumBoundingGeometry_management(bfcl_split, 'in_memory/cl_minbound',
                                                               'RECTANGLE_BY_WIDTH', '', '', 'MBG_FIELDS')
        arcpy.AddField_management(cl_minbound, 'clOrient', 'DOUBLE')
        fields = ['MBG_Orientation', 'clOrient']
        with arcpy.da.UpdateCursor(cl_minbound, fields) as cursor:
            for row in cursor:
                if row[0] > 90.0:
                    row[1] = row[0] - 180
                else:
                    row[1] = row[0]
                cursor.updateRow(row)
        arcpy.JoinField_management(bfcl_split, 'FID', cl_minbound, 'ORIG_FID', ['clOrient'])

        #  c. create unit polygon centroids
        unit_centroid = arcpy.FeatureToPoint_management(units, 'in_memory/unit_centroid', 'INSIDE')

        #  d. find centerline segment that is closest to unit centroid and join to unit polygon
        arcpy.Near_analysis(unit_centroid, bfcl_split)
        arcpy.JoinField_management(unit_centroid, 'NEAR_FID', bfcl_split, 'FID', ['clOrient'])
        arcpy.JoinField_management(units, 'FID', unit_centroid, 'ORIG_FID', ['clOrient'])

        #  e. find orientation of unit relative to centerline (unit orientation - centerline orientation)
        fields = ['unitOrient', 'clOrient', 'Orient']
        with arcpy.da.UpdateCursor(units, fields) as cursor:
            for row in cursor:
                row[2] = float(row[0]) - float(row[1])
                cursor.updateRow(row)

        arcpy.DeleteField_management(units, ['unitOrient', 'clOrient'])

        with arcpy.da.UpdateCursor(units, ['Orient', 'OrientCat']) as cursor:
            for row in cursor:
                if abs(row[0]) >= 75 and abs(row[0]) <= 105:
                    row[1] = 'Transverse'
                elif abs(row[0]) <= 15 or abs(row[0]) >= 165:
                    row[1] = 'Longitudinal'
                else:
                    row[1] = 'Diagonal'
                cursor.updateRow(row)

        # --calculate unit elongation ratio--

        print '...elongation ratio...'

        #  get long axis minimum bounding geometry using convex hull
        fields = ['Area', 'Length', 'ElongRatio', 'Morphology']
        with arcpy.da.UpdateCursor(units, fields) as cursor:
            for row in cursor:
                row[2] = (2 * (math.sqrt(row[0] / 3.14159))) / row[1]
                if row[2] < 0.6:
                    row[3] = 'Elongated'
                cursor.updateRow(row)

        # --calculate unit position--

        print '...unit position...'

        onEdge_buffer = arcpy.Buffer_analysis('edge_lyr', 'in_memory/onEdge_buffer', 0.05 * bfw)
        nearEdge_buffer = arcpy.Buffer_analysis('edge_lyr', 'in_memory/nearEdge_buffer', 0.1 * bfw)

        edge_units = arcpy.SpatialJoin_analysis(onEdge_buffer, units, 'in_memory/tmp_edge_units', 'JOIN_ONE_TO_MANY',
                                                '',
                                                '', 'INTERSECT')
        edge_tbl = arcpy.Frequency_analysis(edge_units, 'tbl_edge_units.dbf', ['UnitID'])
        arcpy.AddField_management(edge_tbl, 'onEdge', 'SHORT')
        arcpy.CalculateField_management(edge_tbl, 'onEdge', '[FREQUENCY]')
        arcpy.JoinField_management(units, 'UnitID', edge_tbl, 'UnitID', ['onEdge'])

        edge_units2 = arcpy.SpatialJoin_analysis(nearEdge_buffer, units, 'in_memory/tmp_edge_units', 'JOIN_ONE_TO_MANY',
                                                 '',
                                                 '', 'INTERSECT')
        edge_tbl2 = arcpy.Frequency_analysis(edge_units2, 'tbl_edge_units2.dbf', ['UnitID'])
        arcpy.AddField_management(edge_tbl2, 'nearEdge1', 'SHORT')
        arcpy.CalculateField_management(edge_tbl2, 'nearEdge1', '[FREQUENCY]')
        arcpy.JoinField_management(units, 'UnitID', edge_tbl2, 'UnitID', ['nearEdge1'])
        # arcpy.SelectLayerByAttribute_management('edge_lyr', 'NEW_SELECTION', """ "midEdge" = 'Yes' """)
        # arcpy.SelectLayerByLocation_management('units_lyr', 'INTERSECT', 'edge_lyr', '', 'NEW_SELECTION')
        #
        # with arcpy.da.UpdateCursor('units_lyr', ['onEdge', 'nearEdge1']) as cursor:
        #     for row in cursor:
        #         if row[0] > 0:
        #             row[0] = row[0] - 1
        #         if row[1] > 0:
        #             row[1] = row[1] - 1
        #         cursor.updateRow(row)

        arcpy.SelectLayerByAttribute_management('edge_lyr', 'CLEAR_SELECTION')
        arcpy.AddField_management(units, 'nearEdge', 'SHORT')
        with arcpy.da.UpdateCursor(units, ['onEdge', 'nearEdge1', 'nearEdge']) as cursor:
            for row in cursor:
                if row[0] < 1:
                    row[0] = 0
                if row[1] < 1:
                    row[1] = 0
                row[2] = abs(row[0] - row[1])
                cursor.updateRow(row)

        fields = ['onEdge', 'nearEdge', 'Position']
        with arcpy.da.UpdateCursor(units, fields) as cursor:
            for row in cursor:
                if row[0] == 1:
                    row[2] = 'Margin Attached'
                elif row[0] >= 2:
                    row[2] = 'Channel Spanning'
                elif row[1] == 1:
                    row[2] = 'Margin Detached'
                else:
                    row[2] = 'Mid Channel'
                cursor.updateRow(row)

        arcpy.DeleteField_management(units, ['onEdge', 'nearEdge1', 'nearEdge'])

        #  --calculate thalweg intersection--

        print '...thalweg intersection...'

        # Set fieldmapping
        fms = arcpy.FieldMappings()
        fms.addTable(units)
        fm = arcpy.FieldMap()
        fm.addInputField(tmp_thalwegs, 'Channel')
        field = fm.outputField
        field.name = 'allThalCh'
        field.type = 'String'
        field.length = 150
        fm.outputField = field
        fm.mergeRule = 'Join'
        field.isNullable = True
        fm.joinDelimiter = ', '
        fms.addFieldMap(fm)

        unit_thalweg_ch = arcpy.SpatialJoin_analysis(units, tmp_thalwegs, 'in_memory/unit_thalwegs_ch',
                                                     'JOIN_ONE_TO_ONE', '',
                                                     fms, 'INTERSECT')
        arcpy.JoinField_management(units, 'UnitID', unit_thalweg_ch, 'UnitID', ['allThalCh'])

        # Set fieldmapping
        fms = arcpy.FieldMappings()
        fms.addTable(units)
        fm = arcpy.FieldMap()
        fm.addInputField(tmp_thalwegs, 'ThalwegTyp')
        field = fm.outputField
        field.name = 'allThalTyp'
        field.type = 'String'
        field.length = 150
        fm.outputField = field
        fm.mergeRule = 'Join'
        field.isNullable = True
        fm.joinDelimiter = ', '
        fms.addFieldMap(fm)

        unit_thalweg = arcpy.SpatialJoin_analysis(units, tmp_thalwegs, 'in_memory/unit_thalwegs', 'JOIN_ONE_TO_ONE', '',
                                                  fms, 'INTERSECT')
        arcpy.JoinField_management(units, 'UnitID', unit_thalweg, 'UnitID', ['allThalTyp'])

        arcpy.AddField_management(units, 'ThalwegCh', 'TEXT', '', '', 50)
        arcpy.AddField_management(units, 'OnThalweg', 'TEXT', '', '', 50)

        with arcpy.da.UpdateCursor(units, ['allThalCh', 'ThalwegCh', 'allThalTyp', 'OnThalweg']) as cursor:
            for row in cursor:
                # print list(set(row[0].split(', ')))
                if not row[0] == None:
                    row[1] = ', '.join(set(row[0].split(', ')))
                    row[3] = ', '.join(set(row[2].split(', ')))
                else:
                    row[1] = 'None'
                    row[3] = 'None'
                cursor.updateRow(row)

        arcpy.DeleteField_management(units, ['allThalCh', 'allThalTyp'])

        # ----------------------------------------------------------
        # Attribute bankfull surface slope

        print '...bankfull surface slope...'

        #  get mean value for each unit
        ZonalStatisticsAsTable(units, 'UnitID', bfSlope, 'tbl_bfSlope.dbf', 'DATA', 'MEAN')
        #  join mean value back to units shp
        arcpy.JoinField_management(units, 'UnitID', 'tbl_bfSlope.dbf', 'UnitID', 'MEAN')

        fields = ['MEAN', 'bfSlope']
        with arcpy.da.UpdateCursor(units, fields) as cursor:
            for row in cursor:
                row[1] = row[0]
                cursor.updateRow(row)

        arcpy.DeleteField_management(units, ['MEAN'])

        # ----------------------------------------------------------
        # Attribute smoothed bankfull surface slope

        #  get mean value for each unit
        ZonalStatisticsAsTable(units, 'UnitID', bfSlope_Smooth, 'tbl_bfSlope_Smooth.dbf', 'DATA', 'MEAN')
        #  join mean value back to units shp
        arcpy.JoinField_management(units, 'UnitID', 'tbl_bfSlope_Smooth.dbf', 'UnitID', 'MEAN')

        fields = ['MEAN', 'bfSlopeSm']
        with arcpy.da.UpdateCursor(units, fields) as cursor:
            for row in cursor:
                row[1] = row[0]
                cursor.updateRow(row)

        arcpy.DeleteField_management(units, ['MEAN'])

        # ----------------------------------------------------------
        # Attribute mean slope

        print '...mean bed slope...'

        #  get mean value for each unit
        ZonalStatisticsAsTable(units, 'UnitID', os.path.join(evpath, 'slope_inCh_' + os.path.basename(
            os.path.join(config.workspace, config.inDEM))), 'tbl_slope.dbf', 'DATA', 'MEAN')
        #  join mean value back to units shp
        arcpy.JoinField_management(units, 'UnitID', 'tbl_slope.dbf', 'UnitID', 'MEAN')

        fields = ['MEAN', 'bedSlope']
        with arcpy.da.UpdateCursor(units, fields) as cursor:
            for row in cursor:
                row[1] = row[0]
                cursor.updateRow(row)

        arcpy.DeleteField_management(units, ['MEAN'])

        return (units)

    #  ---------------------------------
    #  tier 3 classification
    #  ---------------------------------

    #  split units by slope categories

    #  create copy of tier 2 shapefile and clean-up any tiny polygons (Area < cellsize) from manual editing
    units_t2 = arcpy.CopyFeatures_management(os.path.join(outpath, 'Tier2_InChannel_Transition.shp'), 'in_memory/tmp_tier2_inChannel')
    with arcpy.da.UpdateCursor(units_t2, ['SHAPE@Area', 'Area']) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)
    arcpy.MakeFeatureLayer_management(units_t2, 'units_t2_lyr')
    arcpy.SelectLayerByAttribute_management('units_t2_lyr', "NEW_SELECTION", """ "Area" < %s """ % str(desc.meanCellWidth))
    units_t2_elim = arcpy.Eliminate_management('units_t2_lyr', 'in_memory/units_t2_elim', 'AREA')

    arcpy.MakeFeatureLayer_management(units_t2_elim, 'units_t2_elim_lyr')
    arcpy.SelectLayerByAttribute_management('units_t2_elim_lyr', "NEW_SELECTION", """ "UnitForm" = 'Bowl Transition' """)
    bowltrans = arcpy.CopyFeatures_management('units_t2_elim_lyr', 'in_memory/bowl_trans')

    #  add attribute fields to tier 2 polygon shapefile
    nfields = [('GU', 'TEXT', '25'), ('GUKey', 'TEXT', '5')]

    for nfield in nfields:
        arcpy.AddField_management(bowltrans, nfield[0], nfield[1], '', '', nfield[2])

    guAttributes(bowltrans)

    # ----------------------------------------------------------
    # Attribute tier 3 bowl transition features
    arcpy.CopyFeatures_management(bowltrans, os.path.join(evpath, 'tmp_bowltrans_postgu.shp'))
    fields = ['UnitForm', 'bfSlopeSm', 'OnThalweg', 'Area', 'ElongRatio', 'SHAPE@', 'GU', 'GUKey']

    with arcpy.da.UpdateCursor(bowltrans, fields) as cursor:
        for row in cursor:
            if row[0] == 'Bowl Transition':
                    if row[2] == 'Cut-off' and row[3] > (0.25 * bfw) and row[4] < 0.4:
                        row[6] = 'Chute'
                        row[7] = 'Ch'
                    else:
                        if row[2] == 'Braid' and row[3] > (0.25 * bfw) and row[4] < 0.4:
                            row[6] = 'Chute'
                            row[7] = 'Ch'
            cursor.updateRow(row)

    with arcpy.da.UpdateCursor(bowltrans, fields) as cursor:
        for row in cursor:
            if row[6] != 'Chute':
                cursor.deleteRow()

    arcpy.CopyFeatures_management(bowltrans, os.path.join(evpath, 'tmp_bowltrans.shp'))

    arcpy.SelectLayerByAttribute_management('units_t2_elim_lyr', "NEW_SELECTION", """ "UnitForm" = 'Trough' OR "UnitForm" = 'Bowl Transition' """)
    arcpy.CopyFeatures_management('units_t2_elim_lyr', os.path.join(evpath, 'tmp_units_t2_elim_lyr_select.shp'))
    arcpy.SelectLayerByLocation_management('units_t2_elim_lyr', 'ARE_IDENTICAL_TO', bowltrans, '','REMOVE_FROM_SELECTION')
    arcpy.CopyFeatures_management('units_t2_elim_lyr', os.path.join(evpath, 'tmp_units_t2_elim_lyr_select2.shp'))
    bowltras_trough_dissolve = arcpy.Dissolve_management('units_t2_elim_lyr', 'in_memory/bowltras_trough_dissolve', ['ValleyUnit'], '', 'SINGLE_PART', 'UNSPLIT_LINES')
    units_update = arcpy.Update_analysis(units_t2_elim, bowltras_trough_dissolve, 'in_memory/units_update')
    with arcpy.da.UpdateCursor(units_update, ['SHAPE@Area', 'Area', 'UnitShape', 'UnitForm']) as cursor:
        for row in cursor:
            if row[3] == '':
                row[1] = row[0]
                row[2] = 'Concavity'
                row[3] = 'Trough'
            cursor.updateRow(row)

    arcpy.MakeFeatureLayer_management(units_update, 'troughplane_lyr')
    arcpy.SelectLayerByAttribute_management('troughplane_lyr', "NEW_SELECTION", """ "UnitForm" = 'Trough' OR "UnitForm" = 'Plane' """)

    #  at lower gradient sites split by bed slope standard deviation
    #  at higher gradient sites split by bankfull surface slope
    if gradient < 3.0:
        if sinuosity > 1.3 or thalwegRatio > 2.0:
            troughplane_slope_int = arcpy.Intersect_analysis(['troughplane_lyr', 'bedSlope_lyr'], 'in_memory/troughplane_slope_int')
        else:
            troughplane_slope_int = arcpy.Intersect_analysis(['troughplane_lyr', 'bfSlope_lyr'], 'in_memory/troughplane_slope_int')
    else:
        troughplane_slope_int = arcpy.Intersect_analysis(['troughplane_lyr', 'bfSlope_lyr'], 'in_memory/troughplane_slope_int')

    #  convert from multipart to singlpart features and calculate area
    troughplane_slope_sp = arcpy.MultipartToSinglepart_management(troughplane_slope_int, 'in_memory/troughplane_slope_sp')
    with arcpy.da.UpdateCursor(troughplane_slope_sp, ['SHAPE@Area', 'Area']) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    #  find trough features < 0.25 * bfw and merge with adjacent trough units
    trough_sp = arcpy.Select_analysis(troughplane_slope_sp, 'in_memory/trough_sp', """ "UnitForm" = 'Trough' """)
    arcpy.MakeFeatureLayer_management(trough_sp, 'trough_lyr')
    arcpy.SelectLayerByAttribute_management('trough_lyr', "NEW_SELECTION", """ "Area" < %s """ % str(0.25 * bfw))
    trough_elim = arcpy.Eliminate_management('trough_lyr', 'in_memory/trough_elim', 'LENGTH')


    #  find trough features < 0.25 * bfw and merge with adjacent trough units
    plane_sp = arcpy.Select_analysis(troughplane_slope_sp, 'in_memory/plane_sp', """ "UnitForm" = 'Plane' """)
    arcpy.MakeFeatureLayer_management(plane_sp, 'plane_lyr')
    arcpy.SelectLayerByAttribute_management('plane_lyr', "NEW_SELECTION", """ "Area" < %s """ % str(0.25 * bfw))
    plane_elim = arcpy.Eliminate_management('plane_lyr', 'in_memory/plane_elim', 'LENGTH')


    units_update2 = arcpy.Update_analysis(units_update, trough_elim, 'in_memory/units_update2')
    units = arcpy.Update_analysis(units_update2, plane_elim, 'in_memory/tmp_units')

    arcpy.MakeFeatureLayer_management(units, 'units_lyr')

    #  add attribute fields to tier 2 polygon shapefile
    nfields = [('GU', 'TEXT', '25'), ('GUKey', 'TEXT', '5')]

    for nfield in nfields:
        arcpy.AddField_management(units, nfield[0], nfield[1], '', '', nfield[2])


    def subGUAttributes(units):

        print "Calculating tier 3 subGU attributes..."

        print "...unit roundness, convexity, compactness, thickness, vertical compactness, platyness and sphericity..."

        #  calculate unit roundness and convexity using convex hull polygon
        #  calculate compactness, thickness, vertical compactness, platyness, and sphericity

        unit_convexhull = arcpy.MinimumBoundingGeometry_management(units, 'in_memory/units_convexhull', 'CONVEX_HULL', '', '', 'MBG_FIELDS')
        arcpy.AddField_management(unit_convexhull, 'chPerim', 'DOUBLE')
        with arcpy.da.UpdateCursor(unit_convexhull, ['SHAPE@Length', 'chPerim']) as cursor:
            for row in cursor:
                row[1] = row[0]
                cursor.updateRow(row)
        arcpy.JoinField_management(units, 'UnitID', unit_convexhull, 'UnitID', ['chPerim'])

        tbl_unit_elevRange = ZonalStatisticsAsTable(units, 'UnitID', dem, 'tbl_unit_elevRange.dbf', 'DATA', 'RANGE')
        arcpy.JoinField_management(units, 'UnitID', tbl_unit_elevRange, 'UnitID', ['RANGE'])

        nfields = [('ForceHyd', 'TEXT', '15'), ('RiffCrest', 'TEXT', '5'), ('wRatioMin', 'DOUBLE', ''), ('wRatioMax', 'DOUBLE', ''),
                   ('Roundness', 'DOUBLE', ''), ('Convexity', 'DOUBLE', ''), ('Compactness', 'DOUBLE', ''), ('Thickness', 'DOUBLE', ''),
                   ('VCompact', 'DOUBLE', ''), ('Platyness', 'DOUBLE', ''), ('Sphericity', 'DOUBLE', '')]
        for nfield in nfields:
            arcpy.AddField_management(units, nfield[0], nfield[1], '', '', nfield[2])

        fields = ['Area', 'Perimeter', 'Width', 'Length', 'RANGE', 'chPerim', 'Roundness', 'Convexity', 'Compactness', 'Thickness', 'VCompact', 'Platyness', 'Sphericity']
        with arcpy.da.UpdateCursor(units, fields) as cursor:
            for row in cursor:
                row[6] = row[0] / (row[5]**2)
                row[7] = row[5] / row[1]
                row[8] = ((4 * 3.14159) * row[0]) / (row[1]**2)
                row[9] = row[4]
                if row[4] > 0:
                    row[10] = row[4] / row[3]
                    row[11] = row[4] / row[2]
                    row[12] = ((row[2] * row[4]) / (row[3]**2))**.33
                cursor.updateRow(row)

        arcpy.DeleteField_management(units, ['RANGE', 'chPerim'])

        print "...profile and planform curvature..."

        Curvature(dem, '', 'in_memory/prof_curv', 'in_memory/plan_curv')

        tbl_unit_profCurv = ZonalStatisticsAsTable(units, 'UnitID', 'in_memory/prof_curv', 'tbl_unit_profCurv.dbf', 'DATA', 'MEAN')
        arcpy.AddField_management(tbl_unit_profCurv, 'ProfCurv', 'DOUBLE')
        with arcpy.da.UpdateCursor(tbl_unit_profCurv, ['MEAN', 'ProfCurv']) as cursor:
            for row in cursor:
                row[1] = row[0]
                cursor.updateRow(row)
        arcpy.JoinField_management(units, 'UnitID', tbl_unit_profCurv, 'UnitID', ['ProfCurv'])

        tbl_unit_planCurv = ZonalStatisticsAsTable(units, 'UnitID', 'in_memory/plan_curv', 'tbl_unit_planCurv.dbf', 'DATA', 'MEAN')
        arcpy.AddField_management(tbl_unit_planCurv , 'PlanCurv', 'DOUBLE')
        with arcpy.da.UpdateCursor(tbl_unit_planCurv , ['MEAN', 'PlanCurv']) as cursor:
            for row in cursor:
                row[1] = row[0]
                cursor.updateRow(row)
        arcpy.JoinField_management(units, 'UnitID', tbl_unit_planCurv , 'UnitID', ['PlanCurv'])

        #  --calculate side channel intersection--

        print '...side channel intersection...'

        #  create separate layer for main and side channel cross sections
        arcpy.MakeFeatureLayer_management(os.path.join(config.workspace, config.bfXS), 'bfxs_side_lyr', """ "Channel" = 'Side' """)
        arcpy.MakeFeatureLayer_management(os.path.join(config.workspace, config.bfXS), 'bfxs_main_lyr', """ "Channel" = 'Main' """)

        #  attribute side channel cross section count/frequency to each unit
        bfxs_side_units = arcpy.SpatialJoin_analysis('bfxs_side_lyr', units, 'in_memory/tmp_bfxs_side_units', 'JOIN_ONE_TO_MANY', '', '', 'INTERSECTS')
        arcpy.Frequency_analysis(bfxs_side_units, 'tbl_bfxs_side_units.dbf', ['UnitID'])
        arcpy.AddField_management('tbl_bfxs_side_units.dbf', 'sideXSCt', 'SHORT')
        arcpy.CalculateField_management('tbl_bfxs_side_units.dbf', 'sideXSCt', '[FREQUENCY]')
        arcpy.JoinField_management(units, 'UnitID', 'tbl_bfxs_side_units.dbf', 'UnitID', ['sideXSCt'])

        #  attribute main channel cross section count/frequency to each unit
        bfxs_main_units = arcpy.SpatialJoin_analysis('bfxs_main_lyr', units, 'in_memory/tmp_bfxs_main_units', 'JOIN_ONE_TO_MANY', '', '', 'INTERSECTS')
        arcpy.Frequency_analysis(bfxs_main_units, 'tbl_bfxs_main_units.dbf', ['UnitID'])
        arcpy.AddField_management('tbl_bfxs_main_units.dbf', 'mainXSCt', 'SHORT')
        arcpy.CalculateField_management('tbl_bfxs_main_units.dbf', 'mainXSCt', '[FREQUENCY]')
        arcpy.JoinField_management(units, 'UnitID', 'tbl_bfxs_main_units.dbf', 'UnitID', ['mainXSCt'])

        #  attribute each unit as being in side channel or main channel
        #  if side channel cross section count > main channel cross section count, attribute 'Side' else as 'Main'
        with arcpy.da.UpdateCursor(units, ['sideXSCt', 'mainXSCt', 'Channel']) as cursor:
            for row in cursor:
                if row[0] > row[1]:
                    row[2] = 'Side'
                else:
                    row[2] = 'Main'
                cursor.updateRow(row)

        #  delete unnecessary fields
        arcpy.DeleteField_management(units, ['sideXSCt', 'mainXSCt'])

        #  --calculate channel node intersection--

        print '...channel confluence/diffluence...'

        if os.path.exists(os.path.join(evpath, 'channelNodes.shp')):
            arcpy.MakeFeatureLayer_management(os.path.join(evpath, 'channelNodes.shp'), 'confluence_lyr', """ "ChNodeType" = 'Confluence' """)
            arcpy.MakeFeatureLayer_management(os.path.join(evpath, 'channelNodes.shp'), 'diffluence_lyr', """ "ChNodeType" = 'Diffluence' """)

            with arcpy.da.UpdateCursor(units, ['ForceHyd']) as cursor:
                for row in cursor:
                    row[0] = 'NA'
                    cursor.updateRow(row)

            arcpy.MakeFeatureLayer_management(units, 'units_lyr')

            #  identify units that are in close proximity to channel confluence [assigning Y/N]
            arcpy.SelectLayerByLocation_management('units_lyr', 'INTERSECT', 'confluence_lyr', '', 'NEW_SELECTION')
            #arcpy.CalculateField_management('units_lyr', "ForceHyd", "\"Confluence\"", "PYTHON")
            with arcpy.da.UpdateCursor('units_lyr', ['ForceHyd']) as cursor:
                for row in cursor:
                    row[0] = 'Confluence'
                    cursor.updateRow(row)

            #  identify units that are in close proximity to channel diffluence [assigning Y/N]
            arcpy.SelectLayerByLocation_management('units_lyr', 'INTERSECT', 'diffluence_lyr', '', 'NEW_SELECTION')
            with arcpy.da.UpdateCursor('units_lyr', ['ForceHyd']) as cursor:
                for row in cursor:
                    row[0] = 'Diffluence'
                    cursor.updateRow(row)
        else:
            with arcpy.da.UpdateCursor(units, ['ForceHyd']) as cursor:
                for row in cursor:
                    row[0] = 'NA'
                    cursor.updateRow(row)

        #  --calculate thalweg high point intersection--

        print '...thalweg high point intersection...'

        #  if unit intersects channel node assign 'Yes'
        arcpy.SelectLayerByLocation_management('units_lyr', 'INTERSECT', os.path.join(evpath, 'potentialRiffCrests.shp'), '', 'NEW_SELECTION')
        with arcpy.da.UpdateCursor('units_lyr', 'RiffCrest') as cursor:
            for row in cursor:
                row[0] = 'Yes'
                cursor.updateRow(row)

        # if unit does not intersect channel node assign 'No'
        arcpy.SelectLayerByAttribute_management('units_lyr', 'SWITCH_SELECTION')
        with arcpy.da.UpdateCursor('units_lyr', 'RiffCrest') as cursor:
            for row in cursor:
                row[0] = 'No'
                cursor.updateRow(row)

        #  --calculate unit width ratio--

        print '...minimum and maximum width ratio...'

        units_bfxs2 = arcpy.SpatialJoin_analysis(units, bfxs_join, 'in_memory/tmp_units_bfxs2', 'JOIN_ONE_TO_MANY', '', '', 'INTERSECT')
        arcpy.Statistics_analysis(units_bfxs2, 'tbl_units_bfxs_stats2', [['widthRatio', 'MIN'],['widthRatio', 'MAX']], 'UnitID')
        arcpy.JoinField_management(units, 'UnitID', 'tbl_units_bfxs_stats2', 'UnitID', ['MIN_widthRatio','MAX_widthRatio'])

        fields = ['MIN_widthRatio','MAX_widthRatio', 'wRatioMin', 'wRatioMax']
        with arcpy.da.UpdateCursor(units, fields) as cursor:
            for row in cursor:
                row[2] = row[0]
                row[3] = row[1]
                cursor.updateRow(row)

        arcpy.DeleteField_management(units, ['MIN_widthRatio','MAX_widthRatio'])

        #  --meander index--

        print '...meander index...'

        #  covert meander index to points
        mIndexPts = arcpy.RasterToPoint_conversion(mIndex, 'in_memory/mIndexPts')
        arcpy.AddField_management(mIndexPts, 'mBend', 'DOUBLE')
        with arcpy.da.UpdateCursor(mIndexPts, ['grid_code', 'mBend']) as cursor:
            for row in cursor:
                row[1] = row[0]
                cursor.updateRow(row)

        #  create unit polygon centroids
        unit_centroid2 = arcpy.FeatureToPoint_management(units, 'in_memory/unit_centroid2', 'INSIDE')

        #  find mIndex point that is closest to unit centroid and join to unit polygon
        arcpy.Near_analysis(unit_centroid2, mIndexPts)

        arcpy.JoinField_management(unit_centroid2, 'NEAR_FID', mIndexPts, 'OBJECTID', ['mBend'])
        arcpy.JoinField_management(units, 'FID', unit_centroid2, 'ORIG_FID', ['mBend'])

        arcpy.AddField_management(units, 'mBendCat', 'TEXT', '', '', '15')
        fields = ['mBend', 'mBendCat']
        with arcpy.da.UpdateCursor(units, fields) as cursor:
            for row in cursor:
                if row[0] <= -0.05:
                    row[1] = 'Inside'
                elif row[0] >= 0.05:
                    row[1] = 'Outside'
                else:
                    row[1] = 'Straight'
                cursor.updateRow(row)

        #arcpy.CopyFeatures_management(unit_centroid2, os.path.join(evpath, 'tmp_unit_centroids2.shp'))
        #arcpy.CopyFeatures_management(mIndexPts, os.path.join(evpath, 'tmp_mIndexPts.shp'))

        return(units)


    # ----------------------------------------------------------
    # Run tier 3 GU attributes function
    # ----------------------------------------------------------

    guAttributes(units)

    # ----------------------------------------------------------
    # Classify Tier 3 GU
    # ----------------------------------------------------------
    # classify tier 3 wall features

    print '...classifying tier 3 wall features...'

    arcpy.MakeFeatureLayer_management(units, 'mound_ma_lyr', """ "UnitForm" = 'Mound' AND "Position" = 'Margin Attached' """)
    arcpy.MakeFeatureLayer_management(units, 'mound_mc_lyr', """ "UnitForm" = 'Mound' AND "Position" = 'Mid Channel' """)

    fields = ['UnitForm', 'Position', 'SHAPE@', 'GU', 'GUKey']

    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            if row[0] == 'Wall':
                if row[1] == 'Margin Attached':
                    row[3] = 'Bank'
                    row[4] = 'Bk'
                else:
                    if int(arcpy.GetCount_management(arcpy.SelectLayerByLocation_management('mound_ma_lyr', 'WITHIN_A_DISTANCE', row[2], 0.2 * bfw, "NEW_SELECTION")).getOutput(0)) > 0:
                        row[3] = 'Margin Attached Bar'
                        row[4] = 'Br'
                    elif int(arcpy.GetCount_management(arcpy.SelectLayerByLocation_management('mound_mc_lyr', 'WITHIN_A_DISTANCE', row[2], 0.2 * bfw, "NEW_SELECTION")).getOutput(0)) > 0:
                        row[3] = 'Mid Channel Bar'
                        row[4] = 'Br'
                    else:
                        row[3] = 'NA'
                        row[4] = 'NA'
            cursor.updateRow(row)

    print '...classifying tier 3 concavities...'

    fields = ['UnitForm', 'Area', 'ThalwegCh', 'GU', 'GUKey']

    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            if row[0] == 'Bowl':
                if row[1] > (0.25 * bfw):
                    if row[2] == 'Backwater':
                        row[3] = 'Pond'
                        row[4] = 'Pd'
                    else:
                        row[3] = 'Pool'
                        row[4] = 'Po'
                else:
                    row[3] = 'Pocket Pool'
                    row[4] = 'Pk'
            cursor.updateRow(row)

    # ----------------------------------------------------------
    # Attribute tier 3 planar features

    print '...classifying tier 3 planar features...'

    fields = ['UnitForm', 'OrientCat', 'ElongRatio', 'GU', 'GUKey']

    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            if row[0] == 'Plane':
                if row[1] == 'Transverse' and row[2] < 0.6:
                    row[3] = 'Transition'
                    row[4] = 'Tr'
                    cursor.updateRow(row)

    arcpy.SelectLayerByAttribute_management('units_lyr', 'NEW_SELECTION', """ "GU" IS NULL AND "UnitForm" = 'Plane' """)
    plane_units = arcpy.CopyFeatures_management('units_lyr', 'in_memory/plane_units')
    planeflowtype = arcpy.Intersect_analysis([plane_units, os.path.join(outpath, 'Tier1.shp')], 'in_memory/planeflowtype')

    guAttributes(planeflowtype)

    fields = ['UnitForm', 'Position', 'bfSlopeSm', 'bfwRatio', 'ElongRatio', 'FlowUnit', 'Area', 'OnThalweg', 'GU', 'GUKey']

    with arcpy.da.UpdateCursor(planeflowtype, fields) as cursor:
        for row in cursor:
            if row[0] == 'Plane':
                if row[4] < 0.6 and row[3] < 0.17:
                    row[8] = 'Transition'
                    row[9] = 'Tr'
                elif row[5] == 'Emergent':
                    if row[1] == 'Margin Attached':
                        row[8] = 'Margin Attached Bar'
                        row[9] = 'Br'
                    else:
                        row[8] = 'Mid Channel Bar'
                        row[9] = 'Bc'
                elif row[7] == 'Cut-off' and row[4] < 0.4 and row[6] > (0.25 * bfw):
                        row[8] = 'Chute'
                        row[9] = 'Ch'
                elif row[7] == 'Braid' and row[4] < 0.4 and row[6] > (0.25 * bfw):
                        row[8] = 'Chute'
                        row[9] = 'Ch'
                else:
                    if row[2] < 2.3:
                        row[8] = 'Glide-Run'
                        row[9] = 'GR'
                    elif row[2] < 4.3:
                        row[8] = 'Rapid'
                        row[9] = 'Ra'
                    else:
                        row[8] = 'Cascade'
                        row[9] = 'Ca'
            cursor.updateRow(row)

    #     ----------------------------------------------------------
        # Attribute tier 3 trough features
        arcpy.MakeFeatureLayer_management(units, 'pond_lyr',""" "UnitForm" = 'Bowl' AND "GU" = 'Pond' """)

        print '...classifying tier 3 trough features...'

        fields = ['UnitForm', 'bfSlopeSm', 'OnThalweg', 'Area', 'ElongRatio', 'SHAPE@', 'GU', 'GUKey']

        with arcpy.da.UpdateCursor(units, fields) as cursor:
            for row in cursor:
                if row[0] == 'Trough':
                    if row[4] > 0.6 and int(arcpy.GetCount_management(arcpy.SelectLayerByLocation_management('pond_lyr', 'INTERSECT', row[5], '', "NEW_SELECTION")).getOutput(0)) > 0:
                        row[6] = 'Pond'
                        row[7] = 'Pd'
                    elif row[2] == 'None' and row[4] < 0.4:
                        row[6] = 'Transition'
                        row[7] = 'Tr'
                    else:
                        if row[2] == 'Cut-off' and row[3] > (0.25 * bfw) and row[4] < 0.4:
                            row[6] = 'Chute'
                            row[7] = 'Ch'
                        elif row[2] == 'Braid' and row[3] > (0.25 * bfw) and row[4] < 0.4:
                            row[6] = 'Chute'
                            row[7] = 'Ch'
                        else:
                            if row[1] < 2.3:
                                row[6] = 'Glide-Run'
                                row[7] = 'GR'
                            elif row[1] < 4.3:
                                row[6] = 'Rapid'
                                row[7] = 'Ra'
                            else:
                                row[6] = 'Cascade'
                                row[7] = 'Ca'
                cursor.updateRow(row)

        # ----------------------------------------------------------
        # Attribute tier 3 bowl transition features

        print '...classifying tier 3 bowl transition features...'

        fields = ['UnitForm', 'bfSlopeSm', 'OnThalweg', 'Area', 'ElongRatio', 'SHAPE@', 'GU', 'GUKey']

        with arcpy.da.UpdateCursor(units, fields) as cursor:
            for row in cursor:
                if row[0] == 'Bowl Transition':
                    if row[4] > 0.6 and int(arcpy.GetCount_management(arcpy.SelectLayerByLocation_management('pond_lyr', 'INTERSECT', row[5], '', "NEW_SELECTION")).getOutput(0)) > 0:
                        row[6] = 'Pond'
                        row[7] = 'Pd'
                    elif row[2] == 'None' and row[4] < 0.4:
                        row[6] = 'Transition'
                        row[7] = 'Tr'
                    else:
                        if row[2] == 'Cut-off' and row[3] > (0.25 * bfw) and row[4] < 0.4:
                            row[6] = 'Chute'
                            row[7] = 'Ch'
                        elif row[2] == 'Braid' and row[3] > (0.25 * bfw) and row[4] < 0.4:
                            row[6] = 'Chute'
                            row[7] = 'Ch'
                        else:
                            if row[1] < 2.3:
                                row[6] = 'Glide-Run'
                                row[7] = 'GR'
                            elif row[1] < 4.3:
                                row[6] = 'Rapid'
                                row[7] = 'Ra'
                            else:
                                row[6] = 'Cascade'
                                row[7] = 'Ca'
                cursor.updateRow(row)

        # ----------------------------------------------------------
        # Attribute tier 3 saddle features

        print '...classifying tier 3 saddle features...'

        fields = ['UnitForm', 'GU', 'GUKey']

        with arcpy.da.UpdateCursor(units, fields) as cursor:
            for row in cursor:
                if row[0] == 'Saddle':
                    row[1] = 'Riffle'
                    row[2] = 'Rf'
                cursor.updateRow(row)

    # ----------------------------------------------------------
    # Attribute tier 3 convexities

    print '...classifying Tier 3 mounds...'

    arcpy.MakeFeatureLayer_management(units, 'mound_lyr', """ "UnitForm" = 'Mound'""")

    fields = ['UnitForm', 'Position', 'OrientCat', 'Morphology', 'Width', 'SHAPE@', 'GU', 'GUKey']

    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            if row[0] == 'Mound':
                if row[2] == 'Diagonal' and int(arcpy.GetCount_management(arcpy.SelectLayerByLocation_management('mound_lyr', 'INTERSECT', row[5], '', "NEW_SELECTION")).getOutput(0)) >= 3:
                    row[6] = 'Riffle'
                    row[7] = 'Rf'
                elif row[1] != 'Margin Attached' and row[1] != 'Margin Detached':
                    row[6] = 'Mid Channel Bar'
                    row[7] = 'Bc'
                else:
                    if row[3] == 'Elongated' and row[4] < (0.05 * bfw):
                        if row[4] == 'Transverse':
                            row[6] = 'Transition'
                            row[7] = 'Tr'
                        else:
                            row[6] = 'Bank'
                            row[7] = 'Bk'
                    else:
                        row[6] = 'Margin Attached Bar'
                        row[7] = 'Br'
            cursor.updateRow(row)

        with arcpy.da.UpdateCursor(units, fields) as cursor:
            for row in cursor:
                if row[0] == 'Mound Transition':
                    row[6] = 'Transition'
                    row[7] = 'Tr'
                cursor.updateRow(row)

    # ---------------------------------------------------------------------------------------------------
    # Dissolve trough and planar units by UnitForm and GU if they share a border (cleans up slope breaks)
    # Re-run GU attributes
    units_plane_update = arcpy.Update_analysis(units, planeflowtype, 'in_memory/units_plane_update')
    units_dissolve = arcpy.Dissolve_management(units_plane_update, 'in_memory/units_dissolve', ['GU', 'GUKey'], '', 'SINGLE_PART', 'UNSPLIT_LINES')
    arcpy.AddField_management(units_dissolve, 'Area', 'DOUBLE')
    with arcpy.da.UpdateCursor(units_dissolve, ['SHAPE@Area', 'Area']) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)
    arcpy.MakeFeatureLayer_management(units_dissolve, 'units_dissolve_lyr')
    arcpy.SelectLayerByAttribute_management('units_dissolve_lyr', "NEW_SELECTION", """ "GU" = 'Transition' OR  "GU" = 'Glide-Run' OR "GU" = 'Rapid' OR "GU" = 'Cascade' """)
    arcpy.SelectLayerByAttribute_management('units_dissolve_lyr', "SUBSET_SELECTION", """ "Area" < %s """ % str(config.areaThresh * bfw))
    arcpy.SelectLayerByLocation_management('units_dissolve_lyr', 'INTERSECT', thalweg_pts, '', 'REMOVE_FROM_SELECTION')

    #units_elim2 = arcpy.Eliminate_management('units_dissolve_lyr', 'in_memory/units_elim2', 'LENGTH', """ "GU" = 'Pool' OR  "GU" = 'Pond' OR "GU" = 'Pocket Pool' """)
    units_elim2 = arcpy.Eliminate_management('units_dissolve_lyr', 'in_memory/units_elim2', 'LENGTH', """ "GU" = 'Bank' """)

    guAttributes(units_elim2)

    t3_units = units_elim2

    arcpy.CopyFeatures_management(t3_units, os.path.join(outpath, 'Tier3_InChannel_GU.shp'))
    arcpy.CopyFeatures_management(t3_units, os.path.join(outpath, 'Tier3_InChannel_GU_Raw.shp'))

    fields = arcpy.ListFields(units_t2)
    keep = ['ValleyUnit', 'UnitShape', 'UnitForm']
    drop = []
    for field in fields:
        if not field.required and field.name not in keep and field.type <> 'Geometry':
            drop.append(field.name)
    if len(drop) > 0:
        arcpy.DeleteField_management(units_t2, drop)

    t3_units_forms = arcpy.Intersect_analysis([t3_units, units_t2], 'in_memory/t3_units_forms')

    guAttributes(t3_units_forms)

    # ----------------------------------------------------------
    # Run tier 3 subGU attributes function
    # ----------------------------------------------------------
    subGUAttributes(t3_units_forms)

    fields = ['OID@', 'UnitID']
    with arcpy.da.UpdateCursor(t3_units_forms, fields) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    arcpy.CopyFeatures_management(t3_units_forms, os.path.join(outpath, 'Tier3_InChannel_GU_Form.shp'))
    arcpy.CopyFeatures_management(t3_units_forms, os.path.join(outpath, 'Tier3_InChannel_GU_Form_Raw.shp'))
    # ----------------------------------------------------------
    # Remove temporary files
    print '...removing intermediary surfaces...'

    for root, dirs, files in os.walk(config.workspace):
        for f in fnmatch.filter(files, 'tbl_*'):
            os.remove(os.path.join(root, f))

    arcpy.Delete_management('in_memory')

    print '...done with Tier 3 classification.'

if __name__ == '__main__':
    tier3()
