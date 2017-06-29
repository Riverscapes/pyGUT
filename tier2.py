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

    def ras2poly_cn(Mound, Planar, Bowl, Trough, Saddle, Wall):
        shps = []
        formDict = locals()
        for key, value in formDict.iteritems():
            if key in ['Mound', 'Planar', 'Bowl', 'Trough', 'Saddle', 'Wall']:
                tmp_fn = 'in_memory/' + str(key)
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
                        elif row[2] == 'Saddle':
                            row[1] = 'Convexity'
                        elif row[2] == 'Wall':
                            row[1] = 'Planar'
                        else:
                            row[1] = 'Concavity'
                        cursor.updateRow(row)

        #units_merge = arcpy.Merge_management(shps, 'in_memory/units_merge')
        units_merge = arcpy.Merge_management(['in_memory/Mound', 'in_memory/Planar', 'in_memory/Bowl', 'in_memory/Trough'], 'in_memory/units_merge')
        units_update = arcpy.Update_analysis('in_memory/units_merge', 'in_memory/Saddle', 'in_memory/units_update')
        tmp_units = arcpy.Update_analysis('in_memory/units_update', 'in_memory/Wall', 'in_memory/tmp_units')
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
    #  tier 2 evidence layers
    #  ---------------------------------
    inCh = SetNull(bf, 1, '"VALUE" = 0')

    print '...deriving evidence layers...'

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

    #  --in channel mean dem slope--
    print os.path.join(evpath, 'slope_inCh_' + os.path.basename(config.inDEM))
    if not os.path.exists(os.path.join(evpath, 'slope_inCh_' + os.path.basename(config.inDEM))):
        inChDEMSlope = Slope(inChDEM, 'DEGREE')
        inChDEMSlope.save(os.path.join(evpath, 'slope_inCh_' + os.path.basename(config.inDEM)))  # save output
    else:
        inChDEMSlope = Raster(os.path.join(evpath, 'slope_inCh_' + os.path.basename(config.inDEM)))

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

    #  --channel margin--
    if not os.path.exists(os.path.join(evpath, 'chMargin.tif')):
        #  a. remove any wePoly parts < 5% of total area
        wPolyElim = arcpy.EliminatePolygonPart_management(config.wPolyShp, 'in_memory/wPolyElim', 'PERCENT', '', 5, 'ANY')
        #  b. erase wPolyElim from bankfull polygon
        polyErase = arcpy.Erase_analysis(config.bfPolyShp, wPolyElim, 'in_memory/polyErase', '')
        #  c. buffer the output by 10% of the integrated wetted width
        bufferDist = 0.1 * ww
        polyBuffer = arcpy.Buffer_analysis(polyErase, 'in_memory/polyBuffer', bufferDist, 'FULL')
        #  d. clip the output to the bankull polygon
        arcpy.Clip_analysis(polyBuffer, config.bfPolyShp, 'in_memory/chMarginPoly')
        #  e. convert the output to a raster
        cm_raw = arcpy.PolygonToRaster_conversion('in_memory/chMarginPoly', 'FID', 'in_memory/chMargin_raw.tif', 'CELL_CENTER', 'NONE', '0.1')
        #  f. set all cells inside/outside the bankfull ratser to 1/0
        cm = Con(cm_raw, 1, "VALUE" >= 0)
        #  g. save the ouput
        cm.save(os.path.join(evpath, 'chMargin.tif'))
    else:
        cm = Raster(os.path.join(evpath, 'chMargin.tif'))

    # --saddle contours--
    if not os.path.exists(os.path.join(evpath, 'contourNodes.shp')):
        #  a. create contours
        if bfw < 12.0:
            contours = Contour(outMeanDEM, 'in_memory/contours', 0.1)
        else:
            contours = Contour(outMeanDEM, 'in_memory/contours', 0.2)
        #  b. clean up contours (i.e., fill contour gaps)
        #  clip contour shp to bankfull polygon
        contour_clip = arcpy.Clip_analysis(contours, config.bfPolyShp, 'in_memory/contours_clip')
        #  convert contour shp from multipart to singlepart feature
        contour_sp = arcpy.MultipartToSinglepart_management(contour_clip, 'in_memory/contours_sp')
        #  create feature layer from singlepart contours
        line_lyr = arcpy.MakeFeatureLayer_management(contour_sp, "contour_lyr")
        # delete very short contours
        with arcpy.da.UpdateCursor(line_lyr, "SHAPE@LENGTH") as cursor:
            for row in cursor:
                if row[0] <= 0.2:
                    cursor.deleteRow()
        #  convert bankfull polygon to line and merge with contours
        bankfull_line = arcpy.FeatureToLine_management([config.bfPolyShp], 'in_memory/bankfull_line')
        contours_bankfull_merge = arcpy.Merge_management([line_lyr, bankfull_line], 'in_memory/contours_bankfull_merge')
        #  create points at contour endpoints and assign unique 'endID' field using OID field
        end_points = arcpy.FeatureVerticesToPoints_management(contours_bankfull_merge, 'in_memory/contours_bankfull_merge_ends', 'BOTH_ENDS')
        arcpy.AddField_management(end_points, 'endID', 'SHORT')
        fields = ['OID@', 'endID']
        with arcpy.da.UpdateCursor(end_points, fields) as cursor:
            for row in cursor:
                row[1] = row[0]
                cursor.updateRow(row)
        #  delete end points that intersect > 1 contour line - only want points that fall on end of a line
        end_points_join = arcpy.SpatialJoin_analysis(end_points, contours_bankfull_merge, 'in_memory/end_points_join', 'JOIN_ONE_TO_ONE', 'KEEP_ALL', '', 'INTERSECT')
        with arcpy.da.UpdateCursor(end_points_join, ['Join_Count']) as cursor:
            for row in cursor:
                if row[0] > 1:
                    cursor.deleteRow()
        #  find nearest end point to each end point
        end_points_join2 = arcpy.SpatialJoin_analysis(end_points_join, end_points_join, 'in_memory/end_points_join2', 'JOIN_ONE_TO_ONE', 'KEEP_ALL', '', 'CLOSEST', '', 'nearDist')
        #  delete end points where near distance is 0 since these are 'false' end points on closed contours
        with arcpy.da.UpdateCursor(end_points_join2, ['nearDist']) as cursor:
            for row in cursor:
                if row[0] <= 0.0:
                    cursor.deleteRow()
        #  rename/calculate near end id field to logical name
        arcpy.AddField_management(end_points_join2, 'nearEndID', 'SHORT')
        arcpy.AddField_management(end_points_join2, 'strContour', 'TEXT')
        with arcpy.da.UpdateCursor(end_points_join2, ['endID_1', 'nearEndID', 'Contour', 'strContour']) as cursor:
            for row in cursor:
                row[1] = row[0]
                row[3] = str(row[2])
                cursor.updateRow(row)
        # remove unnecessary fields from previous join operations
        fields = arcpy.ListFields(end_points_join2)
        keep = ['OID', 'Shape','endID', 'Contour', 'nearEndID', 'nearDist', 'strContour']
        drop = [x.name for x in fields if x.name not in keep]
        arcpy.DeleteField_management(end_points_join2, drop)
        #  make end point feature layer for selection operations
        end_points_lyr = arcpy.MakeFeatureLayer_management(end_points_join2, 'end_points_lyr')
        #  group end point pairs that fall of contour gaps
        #  pair criteria:
        #   - must be nearest points to each other
        #   - must share the same contour value
        #   - can't be further than 1 meter from each other
        arcpy.AddField_management(end_points_lyr, 'endIDGroup', 'SHORT')
        groupIndex = 1
        with arcpy.da.UpdateCursor(end_points_lyr, ['SHAPE@', 'strContour', 'endID', 'nearEndID', 'endIDGroup', 'nearDist']) as cursor:
            for row in cursor:
                arcpy.SelectLayerByAttribute_management(end_points_lyr, "NEW_SELECTION", "endID = %s" % row[3])
                arcpy.SelectLayerByAttribute_management(end_points_lyr, "SUBSET_SELECTION", "strContour = '%s'" % row[1])
                arcpy.SelectLayerByAttribute_management(end_points_lyr, "ADD_TO_SELECTION", "endID = %s" % row[2])
                result = arcpy.GetCount_management(end_points_lyr)
                count = int(result.getOutput(0))
                if count > 1:
                    if row[4] > 0:
                        pass
                    elif row[5] > 1.0: # ToDo: This line skips points that are > 1.0 meters from nearest point.  May need to change threshold for really, really large sites
                        pass
                    else:
                        arcpy.CalculateField_management(end_points_lyr, 'endIDGroup', groupIndex)
                        groupIndex += 1
        #  delete end points that aren't part of group (i.e., that weren't on contour gap)
        with arcpy.da.UpdateCursor(end_points_join2, ['endIDGroup']) as cursor:
            for row in cursor:
                if row[0] <= 0.0:
                    cursor.deleteRow()
        #  create line connecting each end point pair
        gap_lines = arcpy.PointsToLine_management(end_points_join2, 'in_memory/gap_lines', 'endIDGroup')
        #  merge contour gap lines with contours
        contours_gap_merge = arcpy.Merge_management([line_lyr, gap_lines], 'in_memory/contours_gap_merge')
        #  dissolve all lines that are touching into single line
        contours_repaired = arcpy.Dissolve_management(contours_gap_merge, 'in_memory/contours_repaired', '', '', '', 'UNSPLIT_LINES')
        #  c. merge repaired lines with bankfull line
        contours_bankfull_merge2 = arcpy.Merge_management([contours_repaired, bankfull_line], 'in_memory/contours_bankfull_merge2')
        #  d. close contour lines by extending to bankfull line
        arcpy.ExtendLine_edit(contours_bankfull_merge2, "1.0 Meters", "EXTENSION")
        #  e. add unique contour line id field 'ContourID'
        arcpy.AddField_management(contours_bankfull_merge2, 'ContourID', 'SHORT')
        fields = ['OID@', 'ContourID']
        with arcpy.da.UpdateCursor(contours_bankfull_merge2, fields) as cursor:
            for row in cursor:
                row[1] = row[0]
                cursor.updateRow(row)
        #  f. convert contour lines to polygon and clip to bankfull polygon
        contour_poly_raw = arcpy.FeatureToPolygon_management(contours_bankfull_merge2, 'in_memory/raw_contour_poly')
        contour_poly_clip = arcpy.Clip_analysis(contour_poly_raw, config.bfPolyShp, 'in_memory/contour_polygons_clip')

        #  g. create nodes at contour [line] - thalweg intersection
        arcpy.CopyFeatures_management(config.thalwegShp, 'in_memory/thalweg')
        contour_nodes_mpart = arcpy.Intersect_analysis(['in_memory/thalweg', contours_bankfull_merge2], 'in_memory/contour_nodes_mpart', 'NO_FID', '', 'POINT')
        contour_nodes = arcpy.MultipartToSinglepart_management(contour_nodes_mpart, 'in_memory/contour_nodes')

        #  h. add unique node id field
        arcpy.AddField_management(contour_nodes, 'NodeID', 'SHORT')
        fields = ['OID@', 'NodeID']
        with arcpy.da.UpdateCursor(contour_nodes, fields) as cursor:
            for row in cursor:
                row[1] = row[0]
                cursor.updateRow(row)

        #  i. extract dem z values to contour nodes
        ExtractMultiValuesToPoints(contour_nodes, [[outMeanDEM, 'elev']], 'NONE')

        #  j. calculate flowline distance for each contour node
        arcpy.AddField_management('in_memory/thalweg', 'ThID', 'SHORT')
        arcpy.AddField_management('in_memory/thalweg', 'From_', 'DOUBLE')
        arcpy.AddField_management('in_memory/thalweg', 'To_', 'DOUBLE')
        fields = ['SHAPE@LENGTH', 'From_', 'To_', 'OID@', 'ThID']
        with arcpy.da.UpdateCursor('in_memory/thalweg', fields) as cursor:
            for row in cursor:
                row[1] = 0.0
                row[2] = row[0]
                row[4] = row[3]
                cursor.updateRow(row)
        arcpy.CreateRoutes_lr('in_memory/thalweg', 'ThID', 'in_memory/thalweg_route', 'TWO_FIELDS', 'From_', 'To_')
        arcpy.LocateFeaturesAlongRoutes_lr(contour_nodes, 'in_memory/thalweg_route', 'ThID', float(desc.meanCellWidth), 'tbl_Routes.dbf', 'RID POINT MEAS')
        arcpy.JoinField_management(contour_nodes, 'NodeID', 'tbl_Routes.dbf', 'NodeID', ['MEAS'])
        contour_nodes_join = arcpy.SpatialJoin_analysis(contour_nodes, contours, 'in_memory/contour_nodes_join', 'JOIN_ONE_TO_MANY', 'KEEP_ALL', '', 'INTERSECT')

        #  k. sort contour nodes by flowline distance (in downstream direction)
        contour_nodes_sort = arcpy.Sort_management(contour_nodes_join, 'in_memory/contour_nodes_sort', [['MEAS', 'DESCENDING']])
        #  l. re-calculate node id so they are in ascending order starting at upstream boundary
        with arcpy.da.UpdateCursor(contour_nodes_sort, ['OID@', 'NodeID']) as cursor:
            for row in cursor:
                row[1] = row[0]
                cursor.updateRow(row)

        #  m. calculate elevation difference btwn contour nodes in DS direction
        arcpy.AddField_management(contour_nodes_sort, 'adj_elev', 'DOUBLE')
        arcpy.AddField_management(contour_nodes_sort, 'diff_elev', 'DOUBLE')
        arcpy.AddField_management(contour_nodes_sort, 'riff_pair', 'SHORT')
        arcpy.AddField_management(contour_nodes_sort, 'riff_dir', 'TEXT', '', '', 5)

        fields = ['elev', 'adj_elev', 'diff_elev', 'riff_pair', 'riff_dir', 'ContourID']
        elevList = []
        contourList = []
        index = 0
        with arcpy.da.SearchCursor(contour_nodes_sort, fields) as cursor:
            for row in cursor:
                elevList.append(row[0])
                contourList.append(row[5])
        with arcpy.da.UpdateCursor(contour_nodes_sort, fields) as cursor:
            for row in cursor:
                if index + 1 < len(elevList):
                    row[1] = elevList[index + 1]
                    row[2] = float(row[1] - row[0])
                if index + 1 == len(elevList):
                    row[1] = -9999
                    row[2] = -9999
                index += 1
                cursor.updateRow(row)

        with arcpy.da.UpdateCursor(contour_nodes_sort, fields) as cursor:
            for row in cursor:
                if row[1] == -9999:
                    cursor.deleteRow()

        #  n. define riffle us/ds riffle pairs
        #  criteria:
        #   - can't be on same contour
        #   - us node:
        #        - elev diff btwn DS point ~ 0 [btwn 0.05 and -0.05]
        #        - DS point elev diff < 0 [DS decline in elev]
        #   - ds node:
        #        - point elev diff < 0 [DS decline in elev]
        #        - US point elev ~ 0 [btwn 0.05 and -0.05]
        elevDiffList = []
        nodeDirList = []
        index = 0
        with arcpy.da.SearchCursor(contour_nodes_sort, fields) as cursor:
            for row in cursor:
                elevDiffList.append(row[2])
        with arcpy.da.UpdateCursor(contour_nodes_sort, fields) as cursor:
            for row in cursor:
                if index + 1 < len(elevDiffList) and index > 1:
                    if row[5] != contourList[index + 1]:
                        if row[2] < 0.05 and row[2] > -0.05 and elevDiffList[index + 1] < 0 and elevDiffList[index - 1] > 0 and elevDiffList[index - 2] > 0:
                            row[4] = 'US'
                            row[3] = index
                    if row[5] != contourList[index - 1]:
                        if row[2] < 0 and elevDiffList[index - 1] > -0.05 and elevDiffList[index - 1] < 0.05 and elevDiffList[index - 2] > 0 and elevDiffList[index - 3] > 0:
                            row[4] = 'DS'
                            row[3] = index - 1
                nodeDirList.append(row[4])
                if index + 1 == len(elevDiffList) and str(nodeDirList[index - 1]) == 'US':
                    row[4] = 'DS'
                    row[3] = index - 1
                index += 1
                cursor.updateRow(row)

        #  o. snap contour nodes to contour polygon edge in case there was a slight shift in position during line to polygon conversion
        arcpy.Snap_edit(contour_nodes_sort, [[contour_poly_clip, "EDGE", "0.05 Meters"]])

        #  p. save contour polygons and contour nodes to evidence layer folder
        arcpy.CopyFeatures_management(contour_nodes_sort, os.path.join(evpath, 'contourNodes.shp'))
        arcpy.CopyFeatures_management(contour_poly_clip, os.path.join(evpath, 'contourPolygons.shp'))

    else:
        contour_nodes_sort = os.path.join(evpath, 'contourNodes.shp')
        contour_poly_clip = os.path.join(evpath, 'contourPolygons.shp')

    # ---------------------------------
    #  tier 2 classification
    #  ---------------------------------

    #  covert residual topo raster to numpy array
    arr = arcpy.RasterToNumPyArray(resTopo)
    desc2 = arcpy.Describe(resTopo)
    NDV = desc2.noDataValue
    arr[arr == NDV] = numpy.nan
    #  calculate residual topography quantiles to use in thresholding
    q25pos = numpy.percentile(arr[arr > 0], 25)
    q25neg = numpy.percentile(numpy.negative(arr[arr <= 0]), 25)
    q50neg = numpy.percentile(numpy.negative(arr[arr <= 0]), 50)

    print '...classifying tier 2 shapes and forms...'
    mounds = SetNull(resTopo, 1, '"VALUE" < ' + str(q25pos))
    planar = SetNull(resTopo, 1, '"VALUE" >= ' + str(q25pos)) * SetNull(resTopo, 1, '"VALUE" <= -' + str(q25neg))
    bowls = SetNull(resTopo, 1, '"VALUE" > -' + str(q50neg)) * SetNull(normFill, 1, '"VALUE" <= 0')
    troughs = Con(IsNull(bowls), 1) * SetNull(resTopo, 1, '"VALUE" > -' + str(q25neg))

    #  saddles
    #  a. select contour polgons that intersect riffle contour nodes
    arcpy.MakeFeatureLayer_management(contour_nodes_sort, 'downstream_lyr', """ "riff_dir" = 'DS' """)
    arcpy.MakeFeatureLayer_management(contour_nodes_sort, 'upstream_lyr', """ "riff_dir" = 'US' """)
    arcpy.MakeFeatureLayer_management(contour_poly_clip, 'contour_poly_lyr')
    arcpy.SelectLayerByLocation_management('contour_poly_lyr', 'INTERSECT', 'downstream_lyr', '', 'NEW_SELECTION')
    arcpy.SelectLayerByLocation_management('contour_poly_lyr', 'INTERSECT', 'upstream_lyr', '', 'SUBSET_SELECTION')
    riff_contour_raw = arcpy.CopyFeatures_management('contour_poly_lyr', 'in_memory/riffle_contour_raw')

    #  b. add unique riffle id field
    arcpy.AddField_management(riff_contour_raw, 'RiffleID', 'SHORT')
    with arcpy.da.UpdateCursor(riff_contour_raw, ['OID@', 'RiffleID']) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    #  c. clip thalweg to riffle contour
    thalweg_clip = arcpy.Intersect_analysis([config.thalwegShp, riff_contour_raw], 'in_memory/thalweg_clip', 'ALL', '', 'LINE')
    thalweg_clip_sp = arcpy.MultipartToSinglepart_management(thalweg_clip, 'in_memory/thalweg_clip_sp')
    arcpy.MakeFeatureLayer_management(thalweg_clip_sp, 'thalewg_lyr')
    arcpy.SelectLayerByLocation_management('thalewg_lyr', 'INTERSECT', 'downstream_lyr', '', 'NEW_SELECTION')
    arcpy.SelectLayerByLocation_management('thalewg_lyr', 'INTERSECT', 'upstream_lyr', '', 'SUBSET_SELECTION')
    thalweg_int = arcpy.CopyFeatures_management('thalewg_lyr', 'in_memory/thalweg_int')

    #  d. add clipped thalweg length field
    arcpy.AddField_management(thalweg_int, 'ThalLength', 'DOUBLE')
    arcpy.AddField_management(thalweg_int, 'BuffDist', 'DOUBLE')
    with arcpy.da.UpdateCursor(thalweg_int, ['SHAPE@Length', 'ThalLength', 'BuffDist']) as cursor:
        for row in cursor:
            row[1] = row[0]
            row[2] = 1.5 * row[1]
            cursor.updateRow(row)

    #  e. calculate clipped thalweg centroid
    thalweg_centroid = arcpy.FeatureVerticesToPoints_management(thalweg_int, 'in_memory/thalweg_centroid', 'MID')

    #  f. buffer thalweg centroid by 1.5 * length (where length equals distance between the riffle contour nodes
    thalweg_centroid_buffer = arcpy.Buffer_analysis(thalweg_centroid, 'in_memory/thalweg_centroid_buffer', 'BuffDist')

    #  g. clip riffle contour poly by thalweg centroid buffer
    riff_contour_clip = arcpy.Clip_analysis(riff_contour_raw, thalweg_centroid_buffer, 'in_memory/riff_contour_clip')
    #  h. convert clipped riffle contour to single part and select features that contain the thalweg centroid
    riff_contour_clip_sp = arcpy.MultipartToSinglepart_management(riff_contour_clip, 'in_memory/riff_contour_clip_sp')
    arcpy.MakeFeatureLayer_management(riff_contour_clip_sp, 'riff_contour_clip_sp_lyr')
    arcpy.SelectLayerByLocation_management('riff_contour_clip_sp_lyr', 'INTERSECT', thalweg_centroid, '', 'NEW_SELECTION')

    #  i. run negative and positive buffer (3*contour size) to remove 'thin' contour segments
    if bfw < 12.0:
        riff_contour_negbuffer = arcpy.Buffer_analysis('riff_contour_clip_sp_lyr', 'in_memory/riff_contour_negbuffer', '-0.3 Meters', 'FULL', 'FLAT')
        riff_contour_posbuffer = arcpy.Buffer_analysis(riff_contour_negbuffer, 'in_memory/riff_contour_posbuffer', '0.3 Meters', 'FULL', 'FLAT')
    else:
        riff_contour_negbuffer = arcpy.Buffer_analysis('riff_contour_clip_sp_lyr', 'in_memory/riff_contour_negbuffer', '-0.6 Meters', 'FULL', 'FLAT')
        riff_contour_posbuffer = arcpy.Buffer_analysis(riff_contour_negbuffer, 'in_memory/riff_contour_posbuffer', '0.6 Meters', 'FULL', 'FLAT')
    riff_poly = arcpy.MultipartToSinglepart_management(riff_contour_posbuffer, 'in_memory/riff_poly')

    #  j. snap contour nodes to positive buffer and re-select features that contain the thalweg centroid
    arcpy.Snap_edit(contour_nodes_sort, [[riff_poly, "EDGE", "0.4 Meters"]])
    arcpy.MakeFeatureLayer_management(riff_poly, 'riff_poly_lyr')
    arcpy.SelectLayerByLocation_management('riff_poly_lyr', 'INTERSECT', 'downstream_lyr', '', 'NEW_SELECTION')
    arcpy.SelectLayerByLocation_management('riff_poly_lyr', 'INTERSECT', 'upstream_lyr', '', 'SUBSET_SELECTION')
    saddles = arcpy.PolygonToRaster_conversion('riff_poly_lyr', 'RiffleID', 'in_memory/saddles_raw', 'CELL_CENTER', '', 0.1)

    #  walls/banks
    #  a. calculate bank slope threshold
    slopeMeanResult = arcpy.GetRasterProperties_management(inChDEMSlope, 'MEAN')
    slopeMean = float(slopeMeanResult.getOutput(0))
    slopeSTDResult = arcpy.GetRasterProperties_management(inChDEMSlope, 'STD')
    slopeSTD = float(slopeSTDResult.getOutput(0))
    slopeTh = slopeMean + slopeSTD
    print slopeTh

    #  b. segregate walls
    cmSlope = cm *inChDEMSlope  # isolate slope values for channel margin convexities
    walls = SetNull(cmSlope, 1, '"VALUE" <= ' + str(slopeTh))  # apply slope threshold

    ras2poly_cn(mounds, planar, bowls, troughs, saddles, walls)
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
