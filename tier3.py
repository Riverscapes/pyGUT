#  import required modules and extensions
import arcpy
import config
import numpy
import os
import fnmatch
from arcpy.sa import *
arcpy.CheckOutExtension('Spatial')

#  low pass filter function
#     arguments:
#     ras = input raster
#     n = number of passes


def lpf_fn(ras, n):
    ct = 1
    fRas = ras
    while ct <= n:
        lpf = Filter(fRas, 'LOW', '')
        lpfClip = ExtractByMask(lpf, ras)
        fRas = lpfClip
        ct += 1
    return fRas


def main():

    print 'Starting Tier 3 classification...'

    #  environment settings
    arcpy.env.workspace = config.workspace  # set workspace to pf
    arcpy.env.overwriteOutput = True  # set to overwrite output

    #  clean up!
    #  search for existing tier 2 shapefiles or rasters
    #  if exist, delete from workspace otherwise will lead
    #  to errors in subsequent steps
    for root, dirs, files in os.walk(arcpy.env.workspace):
        for f in fnmatch.filter(files, 'Tier3*'):
            os.remove(os.path.join(root, f))

    arcpy.Delete_management('in_memory')

    #  import required rasters
    bf = Raster('EvidenceLayers/bfCh.tif')  # created in 'tier1' module
    cm = Raster('EvidenceLayers/chMargin.tif')
    dem = Raster(config.inDEM)

    #  set raster environment settings
    desc = arcpy.Describe(dem)
    arcpy.env.extent = desc.Extent
    arcpy.env.outputCoordinateSystem = desc.SpatialReference
    arcpy.env.cellSize = desc.meanCellWidth

    #  set output paths
    evpath = os.path.join(arcpy.env.workspace, 'EvidenceLayers')
    outpath = os.path.join(arcpy.env.workspace, 'Output')

    #  ---------------------------------
    #  tier 3 evidence rasters + polygons
    #  ---------------------------------

    print '...deriving evidence rasters...'

    #  --bankfull surface slope--

    print '...bankfull surface slope...'

    #  a. convert bankfull polygon to points
    if round(0.25 * config.bfw, 1) < float(desc.meanCellWidth):
        distance = desc.meanCellWidth
    else:
        distance = round(0.25 * config.bfw, 1)
    bfLine = arcpy.FeatureToLine_management(config.bfPolyShp, 'in_memory/tmp_bfLine')
    bfPts = arcpy.CreateFeatureclass_management('in_memory', 'tmp_bfPts', 'POINT', '', 'DISABLED', 'DISABLED', dem)
    arcpy.AddField_management(bfPts, 'UID', 'LONG')
    arcpy.AddField_management(bfPts, 'lineDist', 'FLOAT')

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
    arcpy.SelectLayerByLocation_management('tmp_bfPtsZ_lyr', 'WITHIN_A_DISTANCE', config.wePolyShp, str(desc.meanCellWidth) + ' Meters')
    if int(arcpy.GetCount_management('tmp_bfPtsZ_lyr').getOutput(0)) > 0:
        arcpy.DeleteFeatures_management('tmp_bfPtsZ_lyr')

    #  d. create bankfull elevation raster
    tmp_raw_bfe = NaturalNeighbor(bfPtsZ, 'demZ', 0.1)
    tmp_bfe = ExtractByMask(tmp_raw_bfe, config.bfPolyShp)

    #  e. create bfe slope raster
    bfSlope = Slope(tmp_bfe, 'DEGREE')
    bfSlope.save(os.path.join(evpath, 'bfeSlope.tif'))

    #  f. calculate mean bfe slope over bfw neighborhood
    neighborhood = NbrRectangle(config.bfw, config.bfw, 'MAP')
    slope_focal = FocalStatistics(bfSlope, neighborhood, 'MEAN')

    #  g. clip to bankfull polygon
    meanBFSlope = ExtractByMask(slope_focal, config.bfPolyShp)

    #  h. save output
    meanBFSlope.save(os.path.join(evpath, 'bfeSlope_meanBFW.tif'))

    #  i. delete intermediate fcs
    fcs = [bfPts, bfLine, bfPtsZ]
    for fc in fcs:
        arcpy.Delete_management(fc)

    #  --low flow relative roughness--

    if config.lowFlowRoughness == 'True':

        print '...low flow relative roughness...'

        #  a. attribute D84 to CHaMP channel unit polygons
        #     convert grain size csv to dbf table
        arcpy.TableToTable_conversion(config.champGrainSize, arcpy.env.workspace, 'tbl_d84.dbf')

        #  b. create copy of champ channel units
        cus = arcpy.CopyFeatures_management(config.champUnits, 'in_memory/tmp_cus')

        #  c. join aux D84 value to CHaMP channel unit shapefile
        arcpy.JoinField_management(cus, 'Unit_Numbe', 'tbl_d84.dbf', 'ChannelUni', 'D84')

        #  d. make sure D84 field is float
        #    (Arc Issue that converts field to type integer if first element is integer)
        arcpy.AddField_management(cus, 'D84_float', 'FLOAT')
        fields = ['D84', 'D84_float']
        with arcpy.da.UpdateCursor(cus, fields) as cursor:
            for row in cursor:
                row[1] = float(row[0])
                cursor.updateRow(row)

        #  e. convert to D84 raster
        arcpy.FeatureToRaster_conversion(cus, 'D84_float', 'd84.tif', 0.1)

        #  f. calculate low flow relative roughness raster
        #     in low flow relative roughness calculation, convert d84 (in mm) to m
        wd = Raster(config.inWaterD)
        lfr = (Raster('d84.tif') / 1000) / wd

        #  g. save the output
        lfr.save(os.path.join(evpath, 'lowFlowRoughess.tif'))

        #  h. delete intermediate fcs
        arcpy.Delete_management(cus)

    #  --channel edge polygon--

    print '...channel edge...'

    #  a. create copy of bfPoly and wPoly
    bfpoly = arcpy.CopyFeatures_management(config.bfPolyShp, 'in_memory/tmp_bfpoly')
    wpoly = arcpy.CopyFeatures_management(config.wePolyShp, 'in_memory/tmp_wpoly')

    #  b. remove small polygon parts from bfPoly wPoly
    #     threshold: < 5% of total area
    bfelim = arcpy.EliminatePolygonPart_management(bfpoly, 'in_memory/tmp_bfelim', 'PERCENT', '', 15, 'ANY')

    #  c. erase wPoly from bfPoly
    erase = arcpy.Erase_analysis(bfelim, wpoly, 'in_memory/tmp_erase', '')

    #  d. buffer output by one cell
    #     ensures there are no 'breaks' along the banks due to areas
    #     where bankfull and wetted extent were the same
    erasebuffer = arcpy.Buffer_analysis(erase, 'in_memory/tmp_buffer', 0.1, 'FULL')

    edge = arcpy.EliminatePolygonPart_management(erasebuffer, 'in_memory/tmp_edge', 'AREA', 3*config.bfw, '', 'ANY')

    #  e. merge multipart edge polgyons into single part polygon
    arcpy.MultipartToSinglepart_management(edge, 'EvidenceLayers/channelEdge.shp')

    #  f. attribute edge as being mid-channel or not
    arcpy.AddField_management('EvidenceLayers/channelEdge.shp', 'midEdge', 'TEXT')
    arcpy.MakeFeatureLayer_management('EvidenceLayers/channelEdge.shp', 'edge_lyr')

    bfLine2 = arcpy.PolygonToLine_management(bfelim, 'in_memory/tmp_bfLine')

    arcpy.SelectLayerByLocation_management('edge_lyr', 'INTERSECT', bfLine2, '', 'NEW_SELECTION')
    with arcpy.da.UpdateCursor('edge_lyr', 'midEdge') as cursor:
        for row in cursor:
            row[0] = 'N'
            cursor.updateRow(row)

    # if unit does not intersect thalweg assign 'N'
    arcpy.SelectLayerByAttribute_management('edge_lyr', 'SWITCH_SELECTION')
    with arcpy.da.UpdateCursor('edge_lyr', 'midEdge') as cursor:
        for row in cursor:
            row[0] = 'Y'
            cursor.updateRow(row)

    arcpy.SelectLayerByAttribute_management('edge_lyr', 'CLEAR_SELECTION')

    #  delete intermediate fcs
    fcs = [bfpoly, wpoly, bfelim, erase, erasebuffer, edge, bfLine2]
    for fc in fcs:
        arcpy.Delete_management(fc)

    #  --thalweg high points--

    print '...thalweg high points...'

    #  a. create thalweg points along thalweg polyline [distance == dem cell size]
    distance = float(desc.meanCellWidth)
    thalPts = arcpy.CreateFeatureclass_management('in_memory', 'tmp_thalPts', 'POINT', '', 'DISABLED', 'DISABLED', dem)
    arcpy.AddField_management(thalPts, 'UID', 'LONG')
    arcpy.AddField_management(thalPts, 'thalDist', 'FLOAT')

    search_fields = ['SHAPE@', 'OID@']
    insert_fields = ['SHAPE@', 'UID', 'thalDist']

    with arcpy.da.SearchCursor(config.thalwegShp, search_fields) as search:
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
    arcpy.AddField_management(thalPts, 'trResid', 'FLOAT')
    arcpy.AddField_management(thalPts, 'trStResid', 'FLOAT')
    arcpy.CalculateField_management(thalPts, 'trResid', '[demZ] - [trendZ]', 'VB')
    arr = arcpy.da.FeatureClassToNumPyArray(thalPts, ['trResid'])
    trResid_sd = arr['trResid'].std()
    arcpy.CalculateField_management(thalPts, 'trStResid', '[trResid] /' + str(trResid_sd), 'VB')
    arcpy.CopyFeatures_management(thalPts, 'EvidenceLayers/potentialRiffCrests.shp')

    #  d2d. remove any thalweg points where standardized residual < 1.0 sd
    with arcpy.da.UpdateCursor('EvidenceLayers/potentialRiffCrests.shp', 'trStResid') as cursor:
        for row in cursor:
            if row[0] < 1.0:
                cursor.deleteRow()

    #  e. delete intermediate fcs
    arcpy.Delete_management(thalPts)

    #  --meander bends--

    print '...meander bends...'

    #  a. isolate wet/dry bf channel
    bfWet = Con(bf == 1, 1)
    bfDry = Con(bf == 0, 1)

    #  b. delineate edge cells
    #  buffer bf channel by one cell using euclidean distance
    bfChDist = EucDistance(bfDry, float(desc.meanCellWidth), desc.meanCellWidth)
    #  define edge and assign value of 0
    bfEdgeRaw = Con(bfChDist > 0, 0)
    bfEdge = ExtractByMask(bfEdgeRaw, bfWet)

    #  c. for each edge cell, get count of number of wet and dry cells
    #  note: In most cases the CHaMP surveys don't extend that far from the bfWet channel.
    #  as such, we can't simply count and difference wet/dry cells (we could if the window
    #  size used fell fully within the survey area) bc the number of wet cells will always be greater
    #  than the number of dry cells resulting in most of the channel being classifies
    #  as the inside of a bend.  As a work around, here we indirectly extend
    #  the number of dry cells by first getting a count of the wet and then infer the remainder of
    #  cells in the window are dry cells. This results in some false positives at the ds and us
    #  extent of the reach.
    nCellWidth = round(config.bfw / desc.meanCellWidth)
    neigh = NbrRectangle(nCellWidth, nCellWidth, 'CELL')  # set neighborhood size
    ebfWet = Con(IsNull(bfEdge), bfWet, bfEdge)
    wetCount = Con(ebfWet == 0, FocalStatistics(ebfWet, neigh, 'SUM'))
    dryCount = (nCellWidth * nCellWidth) - wetCount

    #  d. for each edge cell, difference wet and dry cells to
    #  negative value = inside of bend
    #  positive values = outside of bend
    rawIndex = dryCount - wetCount
    rawIndexClip = ExtractByMask(rawIndex, bfEdge)

    #  e. run low pass filter to smooth output
    fIndex = lpf_fn(rawIndexClip, 5)

    #  f. normalize output as ratio of total (non-Edge) cells in window
    nIndex = fIndex / (nCellWidth * nCellWidth)

    #  g. covert to points
    nIndexPts = arcpy.RasterToPoint_conversion(nIndex, 'in_memory/tmp_nIndex', 'VALUE')

    #  h. interpolate points across entire surface using idw
    rawIDW = Idw(nIndexPts, 'GRID_CODE', desc.meanCellWidth)

    #  i. clip to in-channel
    mIndex = ExtractByMask(rawIDW, bfWet)
    mIndex.save(os.path.join(evpath, 'mIndex.tif'))

    #  j. delete intermediate fcs
    arcpy.Delete_management(nIndexPts)

    #  --width expansion ratio--

    print '...width expansion ratio...'

    #  in DS direction width ratios  </> 1 indicate channel constriction/expansion
    #  a. calculate xs width ratio (xs[n+1]length/xs[n]length) separately for the main channel and each side channel
    #  b. assign minimum and maximum width ratio to each channel unit polygon

    #  step 1: copy inputs to temporary *.shps
    bfxs = arcpy.CopyFeatures_management(config.bfXS, 'in_memory/tmp_bfxs')
    bfcl = arcpy.CopyFeatures_management(config.bfCL, 'in_memory/tmp_bfcl')

    #  step 2: add unique line identifier to centerlines [based on CL id and channel type]
    arcpy.AddField_management(bfcl, 'ChCLID', 'TEXT', '', '', 15)
    fields = ['Channel', 'CLID', 'ChCLID']
    with arcpy.da.UpdateCursor(bfcl, fields) as cursor:
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
    bfxs_join = arcpy.SpatialJoin_analysis(bfxs, bfcl, 'in_memory/tmp_bfxs_join', 'JOIN_ONE_TO_ONE', 'KEEP_ALL', '', 'INTERSECT')

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
    arcpy.Delete_management(bfcl)

    #  --channel nodes--

    print '...channel nodes...'

    chNodes_mpart = arcpy.Intersect_analysis(config.bfCL, 'in_memory/tmp_chNodes_multiPart', 'NO_FID', '', 'POINT')

    if arcpy.management.GetCount(chNodes_mpart)[0] != '0':

        arcpy.MultipartToSinglepart_management(chNodes_mpart, os.path.join(evpath, 'channelNodes.shp'))

        arcpy.AddField_management('EvidenceLayers/channelNodes.shp', 'ChNodeID', 'SHORT')
        arcpy.AddField_management('EvidenceLayers/channelNodes.shp', 'SideChID', 'TEXT', 10)
        arcpy.AddField_management('EvidenceLayers/channelNodes.shp', 'ChNodeType', 'TEXT', 10)

        fields = ['OID@', 'Channel', 'CLID', 'ChNodeID', 'SideChID']
        with arcpy.da.UpdateCursor('EvidenceLayers/channelNodes.shp', fields) as cursor:
            for row in cursor:
                if row[1] == 'Main':
                    cursor.deleteRow()
                else:
                    row[3] = row[0]
                    row[4] = row[1] + str(row[2])
                    cursor.updateRow(row)

        arcpy.MakeFeatureLayer_management(config.bfCL, 'mainCL_lyr', """ "Channel" = 'Main' """)
        mainCL = arcpy.CopyFeatures_management('mainCL_lyr', 'in_memory/tmp_mainCL')

        arcpy.AddField_management(mainCL, 'From_', 'DOUBLE')
        arcpy.AddField_management(mainCL, 'To_', 'DOUBLE')

        fields = ['SHAPE@LENGTH', 'From_', 'To_']
        with arcpy.da.UpdateCursor(mainCL, fields) as cursor:
            for row in cursor:
                row[1] = 0.0
                row[2] = row[0]
                cursor.updateRow(row)

        mainCL_Route = arcpy.CreateRoutes_lr(mainCL, 'CLID', 'in_memory/mainCL_Route', 'TWO_FIELDS', 'From_', 'To_')

        arcpy.LocateFeaturesAlongRoutes_lr('EvidenceLayers/channelNodes.shp', mainCL_Route, 'CLID', float(desc.meanCellWidth), 'tbl_Routes.dbf', 'RID POINT MEAS')

        arcpy.JoinField_management('EvidenceLayers/channelNodes.shp', 'ChNodeID', 'tbl_Routes.dbf', 'ChNodeID', ['MEAS'])

        arcpy.Statistics_analysis('EvidenceLayers/channelNodes.shp', 'tbl_chNodeMax.dbf', [['MEAS', 'MAX']], 'SideChID')

        arcpy.JoinField_management('EvidenceLayers/channelNodes.shp', 'SideChID', 'tbl_chNodeMax.dbf', 'SideChID', ['MAX_MEAS'])

        fields = ['MEAS', 'MAX_MEAS', 'ChNodeType']
        with arcpy.da.UpdateCursor('EvidenceLayers/channelNodes.shp', fields) as cursor:
            for row in cursor:
                if row[0] < row[1]:
                    row[2] = 'Diffluence'
                else:
                    row[2] = 'Confluence'
                cursor.updateRow(row)

        arcpy.Delete_management(chNodes_mpart)

    #  ---------------------------------
    #  tier 3 classification
    #  ---------------------------------

    print '...attributing each unit...'

    #  create copy of tier 2 shapefile
    units = arcpy.CopyFeatures_management('Output/Tier2_InChannel.shp', 'in_memory/tmp_tier3_inChannel')
    arcpy.MakeFeatureLayer_management(units, 'units_lyr')

    #  add attribute fields to tier 2 polygon shapefile
    nfields = [('Tier3', 'TEXT', '25'), ('unitID', 'SHORT', ''), ('Area', 'FLOAT', ''), ('Width', 'FLOAT', ''),('Length', 'FLOAT', ''), ('Position', 'TEXT', '20'),
               ('Thalweg', 'TEXT', '5'), ('SideCh', 'TEXT', '5'), ('Confluence', 'TEXT', '5'), ('Diffluence', 'TEXT', '5'), ('RiffCrest', 'TEXT', '5'), ('wRatioMin', 'FLOAT', ''),
               ('wRatioMax', 'FLOAT', ''), ('mIndexMean', 'FLOAT', ''), ('mBend', 'TEXT', '15'), ('BFESlope', 'FLOAT', ''), ('meanSlope', 'FLOAT', '')]


    for nfield in nfields:
        arcpy.AddField_management(units, nfield[0], nfield[1], '', '', nfield[2])

    #  create unit id field to make sure joins correctly execute
    fields = ['OID@', 'unitID']
    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    #  --calculate unit area--

    print '...unit area...'

    #  populate area attribute field
    fields = ['SHAPE@Area', 'Area']
    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    # # assign orientation
    # fields = ['Tier1', 'Tier2', 'Width', 'Length', 'Orient']
    # with arcpy.da.UpdateCursor(units, fields) as cursor:
    #     for row in cursor:
    #         if row[0] == 'InChannel':
    #             if row[2] > 0.0:
    #                 if row[2] / row[3] > 1.0:
    #                     row[4] = 'Transverse'
    #                 else:
    #                     row[4] = 'Streamwise'
    #             else:
    #                 row[4] = 'NA'
    #         else:
    #             row[4] = 'NA'
    #         cursor.updateRow(row)
    #

    #  elongation ratio - potential other means of calculating orientation
    #  step 5: create minimum bounding rectangles and attribute area and perimeter
    units_minBound = arcpy.MinimumBoundingGeometry_management(units, 'in_memory/tmp_units_minBound', 'RECTANGLE_BY_WIDTH')
    arcpy.AddGeometryAttributes_management(units_minBound, ['AREA', 'PERIMETER_LENGTH'])
    arcpy.AddField_management(units_minBound, 'ElongRatio', 'DOUBLE')
    arcpy.AddField_management(units_minBound, 'Orient', 'TEXT', '', '', '15')

    fields = ['POLY_AREA', 'PERIMETER', 'ElongRatio', 'Orient']
    with arcpy.da.UpdateCursor(units_minBound, fields) as cursor:
        for row in cursor:
            row[2] = (( row[1] /4)**2)/ row[0]
            if row[2] >= 1.05:
                row[3] = 'Streamwise'
            else:
                row[3] = 'Transverse'
            cursor.updateRow(row)

    arcpy.JoinField_management(units, 'unitID', units_minBound, 'unitID', ['Orient'])

    #  --calculate unit position--

    print '...unit position...'

    edge_units = arcpy.SpatialJoin_analysis('edge_lyr', units, 'in_memory/tmp_edge_units', 'JOIN_ONE_TO_MANY', '', '', 'WITHIN_A_DISTANCE', 0.1 * config.ww)
    arcpy.Frequency_analysis(edge_units, 'tbl_edge_units.dbf', ['unitID'])
    arcpy.AddField_management('tbl_edge_units.dbf', 'edgeCount', 'SHORT')
    arcpy.CalculateField_management('tbl_edge_units.dbf', 'edgeCount', '[FREQUENCY]')
    arcpy.JoinField_management(units, 'unitID', 'tbl_edge_units.dbf', 'unitID', ['edgeCount'])

    arcpy.SelectLayerByAttribute_management('edge_lyr', 'NEW_SELECTION', """ "midEdge" = 'Y' """)
    arcpy.SelectLayerByLocation_management('units_lyr', 'HAVE_THEIR_CENTER_IN', 'edge_lyr', '', 'NEW_SELECTION')
    arcpy.SelectLayerByAttribute_management('units_lyr', 'SUBSET_SELECTION', """ "Tier2" = 'Convexity' """)
    arcpy.SelectLayerByLocation_management('units_lyr', 'INTERSECT', 'edge_lyr', '', 'SUBSET_SELECTION')

    with arcpy.da.UpdateCursor('units_lyr', 'edgeCount') as cursor:
        for row in cursor:
            newCount = row[0] - 1
            row[0] = newCount
            cursor.updateRow(row)

    fields = ['edgeCount', 'Position']
    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            if row[0] <= 0:
                row[1] = 'Mid Channel'
            elif row[0] >= 2:
                row[1] = 'Channel Spanning'
            else:
                row[1] = 'Margin Attached'
            cursor.updateRow(row)

    #  --calculate thalweg intersection--

    print '...thalweg intersection...'

    # if unit intersects thalweg assign 'Y'
    arcpy.SelectLayerByLocation_management('units_lyr', 'INTERSECT', config.thalwegShp, '', 'NEW_SELECTION')
    with arcpy.da.UpdateCursor('units_lyr', 'Thalweg') as cursor:
        for row in cursor:
            row[0] = 'Y'
            cursor.updateRow(row)

    # if unit does not intersect thalweg assign 'N'
    arcpy.SelectLayerByAttribute_management('units_lyr', 'SWITCH_SELECTION')
    with arcpy.da.UpdateCursor('units_lyr', 'Thalweg') as cursor:
        for row in cursor:
            row[0] = 'N'
            cursor.updateRow(row)

    #  --calculate side channel intersection--

    print '...side channel intersection...'

    #  create separate layer for main and side channel cross sections
    arcpy.MakeFeatureLayer_management(config.bfXS, 'bfxs_side_lyr', """ "Channel" = 'Side' """)
    arcpy.MakeFeatureLayer_management(config.bfXS, 'bfxs_main_lyr', """ "Channel" = 'Main' """)

    #  attribute side channel cross section count/frequency to each unit
    bfxs_side_units = arcpy.SpatialJoin_analysis('bfxs_side_lyr', units, 'in_memory/tmp_bfxs_side_units', 'JOIN_ONE_TO_MANY', '', '', 'INTERSECTS')
    arcpy.Frequency_analysis(bfxs_side_units, 'tbl_bfxs_side_units.dbf', ['unitID'])
    arcpy.AddField_management('tbl_bfxs_side_units.dbf', 'sideXSCt', 'SHORT')
    arcpy.CalculateField_management('tbl_bfxs_side_units.dbf', 'sideXSCt', '[FREQUENCY]')
    arcpy.JoinField_management(units, 'unitID', 'tbl_bfxs_side_units.dbf', 'unitID', ['sideXSCt'])

    #  attribute main channel cross section count/frequency to each unit
    bfxs_main_units = arcpy.SpatialJoin_analysis('bfxs_main_lyr', units, 'in_memory/tmp_bfxs_main_units', 'JOIN_ONE_TO_MANY', '', '', 'INTERSECTS')
    arcpy.Frequency_analysis(bfxs_main_units, 'tbl_bfxs_main_units.dbf', ['unitID'])
    arcpy.AddField_management('tbl_bfxs_main_units.dbf', 'mainXSCt', 'SHORT')
    arcpy.CalculateField_management('tbl_bfxs_main_units.dbf', 'mainXSCt', '[FREQUENCY]')
    arcpy.JoinField_management(units, 'unitID', 'tbl_bfxs_main_units.dbf', 'unitID', ['mainXSCt'])

    #  attribute each unit as being in side channel or main channel
    #  if side channel cross section count > main channel cross section count, attribute 'SideCh' as 'Y' else as 'N'
    with arcpy.da.UpdateCursor(units, ['sideXSCt', 'mainXSCt', 'SideCh']) as cursor:
        for row in cursor:
            if row[0] > row[1]:
                row[2] = 'Y'
            else:
                row[2] = 'N'
            cursor.updateRow(row)

    #  delete unnecessary fields
    arcpy.DeleteField_management(units, ['sideXSCt', 'mainXSCt'])

    #start test
    #  --calculate unit length and width--
    print '...unit length and width...'

    #  create separate layer for main and side channel units
    arcpy.MakeFeatureLayer_management(units, 'units_side_lyr', """ "SideCh" = 'Y' """)
    arcpy.MakeFeatureLayer_management(units, 'units_main_lyr', """ "SideCh" = 'N' """)

    #  clip side/main xsecs to side/main units using intersect
    bfxs_side_clip = arcpy.Intersect_analysis(['bfxs_side_lyr', 'units_side_lyr'], 'in_memory/tmp_bfxs_side_clip', 'ONLY_FID')
    bfxs_main_clip = arcpy.Intersect_analysis(['bfxs_main_lyr', 'units_main_lyr'], 'in_memory/tmp_bfxs_main_clip', 'ONLY_FID')

    #  calculate xs part length
    arcpy.AddField_management(bfxs_side_clip, 'xsWid', 'FLOAT')
    fields = ['SHAPE@LENGTH', 'xsWid']
    with arcpy.da.UpdateCursor(bfxs_side_clip, fields) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    arcpy.AddField_management(bfxs_main_clip, 'xsWid', 'FLOAT')
    fields = ['SHAPE@LENGTH', 'xsWid']
    with arcpy.da.UpdateCursor(bfxs_main_clip, fields) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    #  spatial join bfxs with side/main unit polys and calculate max width
    unit_bfxs_side = arcpy.SpatialJoin_analysis('units_side_lyr', bfxs_side_clip, 'in_memory/tmp_unit_bfxs_side', 'JOIN_ONE_TO_MANY', '', '', 'CONTAINS')
    arcpy.Statistics_analysis(unit_bfxs_side, 'in_memory/tbl_unit_bfxs_side', [['xsWid', 'MEAN']], 'unitID')

    unit_bfxs_main = arcpy.SpatialJoin_analysis('units_main_lyr', bfxs_main_clip, 'in_memory/tmp_unit_bfxs_main', 'JOIN_ONE_TO_MANY', '', '', 'CONTAINS')
    arcpy.Statistics_analysis(unit_bfxs_main, 'in_memory/tbl_unit_bfxs_main', [['xsWid', 'MEAN']], 'unitID')

    arcpy.Merge_management(['in_memory/tbl_unit_bfxs_side','in_memory/tbl_unit_bfxs_main'], 'in_memory/tbl_unit_bfxs_merge')
    arcpy.JoinField_management(units, 'unitID', 'in_memory/tbl_unit_bfxs_merge', 'unitID', ['MEAN_xsWid'])

    #  calculate unit length and width
    fields = ['Tier1', 'Tier2', 'MEAN_xsWid', 'Width', 'Area', 'Length']
    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            if row[0] == 'InChannel':
                row[3] = row[2]
                if row[3] > 0.0:
                    row[5] = row[4] / row[3]
                else:
                    row[5] = -9999
            else:
                row[5] = -9999
            cursor.updateRow(row)

    arcpy.DeleteField_management(units, ['MEAN_xsWid'])
    #end test

    #  --calculate channel node intersection--

    print '...channel confluence/diffluence intersection...'

    if os.path.exists('EvidenceLayers/channelNodes.shp'):
        arcpy.MakeFeatureLayer_management('EvidenceLayers/channelNodes.shp', 'confluence_lyr', """ "ChNodeType" = 'Confluence' """)
        arcpy.MakeFeatureLayer_management('EvidenceLayers/channelNodes.shp', 'diffluence_lyr', """ "ChNodeType" = 'Diffluence' """)

        #  identify units that are in close proximity to channel confluence [assigning Y/N]
        arcpy.SelectLayerByLocation_management('units_lyr', 'WITHIN_A_DISTANCE', 'confluence_lyr', str(0.1 * config.bfw) + ' Meters', 'NEW_SELECTION')
        with arcpy.da.UpdateCursor('units_lyr', 'Confluence') as cursor:
            for row in cursor:
                row[0] = 'Y'
                cursor.updateRow(row)

        arcpy.SelectLayerByAttribute_management('units_lyr', 'SWITCH_SELECTION')
        with arcpy.da.UpdateCursor('units_lyr', 'Confluence') as cursor:
            for row in cursor:
                row[0] = 'N'
                cursor.updateRow(row)

        #  identify units that are in close proximity to channel diffluence [assigning Y/N]
        arcpy.SelectLayerByLocation_management('units_lyr', 'WITHIN_A_DISTANCE', 'diffluence_lyr', str(0.1 * config.bfw) + ' Meters', 'NEW_SELECTION')
        with arcpy.da.UpdateCursor('units_lyr', 'Diffluence') as cursor:
            for row in cursor:
                row[0] = 'Y'
                cursor.updateRow(row)

        arcpy.SelectLayerByAttribute_management('units_lyr', 'SWITCH_SELECTION')
        with arcpy.da.UpdateCursor('units_lyr', 'Diffluence') as cursor:
            for row in cursor:
                row[0] = 'N'
                cursor.updateRow(row)
    else:
        with arcpy.da.UpdateCursor('units_lyr', ['Confluence', 'Diffluence']) as cursor:
            for row in cursor:
                row[0] = 'N'
                row[1] = 'N'
                cursor.updateRow(row)

    #  --calculate thalweg high point intersection--

    print '...thalweg high point intersection...'

    #  if unit intersects channel node assign 'Y'
    arcpy.SelectLayerByLocation_management('units_lyr', 'INTERSECT', 'EvidenceLayers/potentialRiffCrests.shp', '', 'NEW_SELECTION')
    with arcpy.da.UpdateCursor('units_lyr', 'RiffCrest') as cursor:
        for row in cursor:
            row[0] = 'Y'
            cursor.updateRow(row)

    # if unit does not intersect channel node assign 'N'
    arcpy.SelectLayerByAttribute_management('units_lyr', 'SWITCH_SELECTION')
    with arcpy.da.UpdateCursor('units_lyr', 'RiffCrest') as cursor:
        for row in cursor:
            row[0] = 'N'
            cursor.updateRow(row)

    #  --calculate unit width ratio--

    print '...minimum and maximum width ratio...'

    units_bfxs2 = arcpy.SpatialJoin_analysis('units_lyr', bfxs_join, 'in_memory/tmp_units_bfxs2', 'JOIN_ONE_TO_MANY', '', '', 'INTERSECT')
    arcpy.Statistics_analysis(units_bfxs2, 'tbl_units_bfxs_stats2', [['widthRatio', 'MIN'],['widthRatio', 'MAX']], 'unitID')
    arcpy.JoinField_management('units_lyr', 'unitID', 'tbl_units_bfxs_stats2', 'unitID', ['MIN_widthRatio','MAX_widthRatio'])

    fields = ['MIN_widthRatio','MAX_widthRatio', 'wRatioMin', 'wRatioMax']
    with arcpy.da.UpdateCursor('units_lyr', fields) as cursor:
        for row in cursor:
            row[2] = row[0]
            row[3] = row[1]
            cursor.updateRow(row)

    arcpy.DeleteField_management(units, ['MIN_widthRatio','MAX_widthRatio'])

    #  --meander index--

    print '...meander index...'

    #  get mean value for each unit
    ZonalStatisticsAsTable(units, 'unitID', mIndex, 'tbl_mIndex.dbf', 'DATA', 'MEAN')
    #  join mean value back to units shp
    arcpy.JoinField_management(units, 'unitID', 'tbl_mIndex.dbf', 'unitID', 'MEAN')

    fields = ['MEAN', 'mIndexMean', 'mBend']
    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            row[1] = row[0]
            if row[0] <= -0.05:
                row[2] = 'Inside'
            elif row[0] >= 0.05:
                row[2] = 'Outside'
            else:
                row[2] = 'Straight'
            cursor.updateRow(row)

    arcpy.DeleteField_management(units, ['MEAN'])

    #  --calculate low flow relative roughness--

    if config.lowFlowRoughness == 'True':

        print '...low flow relative roughness...'

        arcpy.AddField_management(units, 'LFRR', 'FLOAT')

        #  get mean value for each unit
        ZonalStatisticsAsTable(units, 'unitID', lfr, 'tbl_lfr', 'DATA', 'MEAN')
        #  join mean value back to units shp
        arcpy.JoinField_management(units, 'unitID', 'tbl_lfr.dbf', 'unitID', 'MEAN')

        fields = ['MEAN', 'LFRR']
        with arcpy.da.UpdateCursor(units, fields) as cursor:
            for row in cursor:
                row[1] = row[0]
                cursor.updateRow(row)

        arcpy.DeleteField_management(units, ['MEAN'])

    # ----------------------------------------------------------
    # Attribute bankfull surface slope
    # TODO: May want to use meanBFSlope (bankfull slope averaged over bfw) rather than bfSlope
    print '...bankfull surface slope...'

    #  get mean value for each unit
    ZonalStatisticsAsTable(units, 'unitID', bfSlope, 'tbl_bfeSlope.dbf', 'DATA', 'MEAN')
    #  join mean value back to units shp
    arcpy.JoinField_management(units, 'unitID', 'tbl_bfeSlope.dbf', 'unitID', 'MEAN')

    fields = ['MEAN', 'BFESlope']
    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    arcpy.DeleteField_management(units, ['MEAN'])

    # ----------------------------------------------------------
    # Attribute mean slope

    print '...mean bed slope...'

    #  get mean value for each unit
    ZonalStatisticsAsTable(units, 'unitID', 'EvidenceLayers/smDEMSlope.tif', 'tbl_slope.dbf', 'DATA', 'MEAN')
    #  join mean value back to units shp
    arcpy.JoinField_management(units, 'unitID', 'tbl_slope.dbf', 'unitID', 'MEAN')

    fields = ['MEAN', 'meanSlope']
    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    arcpy.DeleteField_management(units, ['MEAN'])

    # ----------------------------------------------------------
    # Attribute tier 3 concavities

    print '...classifying tier 3 concavities...'

    fields = ['Tier2', 'Forcing', 'Position', 'Orient', 'Thalweg', 'Confluence', 'mBend', 'Tier3', 'Area']

    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            if row[0] == 'Concavity':
                if row[8] > 0.25 * config.bfw:
                    if row[1] == 'NA': # if not forced
                        if row[3] == 'Transverse':
                            if row[4] == 'Y': # intersects thalweg
                                row[7] = 'Plunge Pool'
                            else: # doesn't intersect thalweg
                                row[7] = 'Backwater Pool'
                        else: # if streamwise
                            if row[4] == 'N': # doesn't intersect thalweg
                                if row[2] != 'Channel Spanning':
                                    row[7] = 'Chute'
                                else:
                                    row[7] = 'Backwater Pool'
                            else: # if intersects thalweg
                                if row[5] == 'Y': # confluence node present
                                    row[7] = 'Confluence Pool'
                                else:
                                    if row[2] == 'Margin Attached' and row[6] == 'Outside':
                                        row[7] = 'Shallow Thalweg'
                                    else:
                                        row[7] = 'Bar Forced Pool'
                else:
                    row[0] = 'TransitionZone'

            cursor.updateRow(row)

    # ----------------------------------------------------------
    # Attribute tier 3 convexities

    print '...classifying tier 3 convexities...'

    arcpy.SelectLayerByLocation_management('units_lyr', 'INTERSECT', 'EvidenceLayers/chMargin.shp', '', 'NEW_SELECTION')
    with arcpy.da.UpdateCursor('units_lyr', ['Tier2', 'meanSlope', 'Tier3', 'Area']) as cursor:
        for row in cursor:
            if row[0] == 'Convexity':
                if row[3] > 0.25 * config.bfw:
                    if row[1] >= 12.0:
                        row[2] = 'Bank'
                else:
                    row[0] = 'TransitionZone'
            cursor.updateRow(row)

    arcpy.MakeFeatureLayer_management(units, 'chute_lyr', """ "Tier3" = 'Chute' """)

    fields = ['Tier2', 'Forcing', 'Position', 'Orient', 'mBend', 'Tier3', 'Area']

    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            if row[0] == 'Convexity' and row[5] != 'Bank':
                if row[6] > config.bfw:
                    if row[1] == 'NA':
                        if row[3] == 'Transverse':
                            if row[2] == 'Mid Channel':
                                row[5] = 'Expansion Bar'
                            elif row[2] == 'Channel Spanning':
                                row[5] = 'Riffle'
                            else:
                                row[5] = 'Unit Bar'
                        else:
                            if row[2] == 'Margin Attached':
                                if row[4] == 'Inside':
                                    row[5] = 'Point Bar'
                                else:
                                    row[5] = 'Lateral Bar'
                            elif row[2] == 'Mid Channel':
                                arcpy.SelectLayerByLocation_management('units_lyr', 'WITHIN_A_DISTANCE', 'chute_lyr', str(config.bfw * 0.25) + ' Meters', 'NEW_SELECTION')
                                row[5] = 'Diagonal Bar'
                                arcpy.SelectLayerByAttribute_management('units_lyr', 'SWITCH_SELECTION')
                                row[5] = 'Longitudinal Bar'
                            else:
                                row[5] = 'Unit Bar'
                else:
                    row[0] = 'TransitionZone'
            cursor.updateRow(row)

    # ----------------------------------------------------------
    # Attribute tier 3 planar features

    print '...classifying tier 3 planar features...'

    fields = ['Tier2', 'Forcing', 'Orient', 'RiffCrest', 'BFESlope', 'Tier3', 'Area', 'Length']

    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            if row[0] == 'Planar':
                if row[6] > config.bfw:
                    if row[1] == 'NA':  # if not forced
                        if row[2] == 'Transverse':
                            if row[3] == 'Y':
                                row[0] = 'Convexity'
                                row[5] = 'Riffle'
                            else:
                                row[0] = 'TransitionZone'
                        elif row[7] < config.bfw:
                            row[0] = 'TransitionZone'
                        else:  # if streamwise
                            if row[4] < 0.5:
                                row[5] = 'Glide'
                            elif row[4] < 2.0:
                                row[5] = 'Run'
                            elif row[4] < 4.0:
                                row[5] = 'Rapid'
                            else:
                                row[5] = 'Cascade'
                else:
                    row[0] = 'TransitionZone'
            cursor.updateRow(row)

    # ----------------------------------------------------------
    # Clean-up transition zones

    print '...cleaning up transition zones...'

    arcpy.SelectLayerByAttribute_management('units_lyr', 'NEW_SELECTION', """ "Tier2" = 'TransitionZone' """)
    transitionzone = arcpy.Dissolve_management('units_lyr', 'in_memory/tmp_TransitionZoneMerge', ['Tier2'])

    with arcpy.da.UpdateCursor(units, 'Tier2') as cursor:
        for row in cursor:
            if row[0] == 'TransitionZone':
                cursor.deleteRow()

    arcpy.Merge_management([units, transitionzone], os.path.join(outpath, 'Tier3_InChannel.shp'))

    fields = ['Tier1', 'Tier2', 'Tier3', 'SHAPE@Area', 'Area', 'OID@', 'unitID']

    with arcpy.da.UpdateCursor(os.path.join(outpath, 'Tier3_InChannel.shp'), fields) as cursor:
        for row in cursor:
            if row[1] == 'TransitionZone':
                row[0] = 'InChannel'
                row[2] = 'TransitionZone'
                row[4] = row[3]
                row[6] = row[5]
            cursor.updateRow(row)

    # ----------------------------------------------------------
    # Remove temporary files
    print '...removing intermediary surfaces...'

    for root, dirs, files in os.walk(config.workspace):
        for f in fnmatch.filter(files, 'tbl_*'):
            os.remove(os.path.join(root, f))

    arcpy.Delete_management('in_memory')

    print '...done with Tier 3 classification.'

if __name__ == '__main__':
    main()
