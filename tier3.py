#  import required modules and extensions
import arcpy
import config
import numpy
import os
import fnmatch
import tempfile
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
    dem = Raster(os.path.join(config.workspace, config.inDEM))

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

    #  ---------------------------------
    #  tier 3 evidence rasters + polygons
    #  ---------------------------------

    print '...deriving evidence rasters...'

    #  --bankfull surface slope--

    if not os.path.exists(os.path.join(evpath, 'bfeSlope_meanBFW.tif')):
        print '...bankfull surface slope...'

        #  a. convert bankfull polygon to points
        if round(0.25 * bfw, 1) < float(desc.meanCellWidth):
            distance = desc.meanCellWidth
        else:
            distance = round(0.25 * bfw, 1)
        bfLine = arcpy.FeatureToLine_management(os.path.join(config.workspace, config.bfPolyShp), 'in_memory/tmp_bfLine')
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
        arcpy.SelectLayerByLocation_management('tmp_bfPtsZ_lyr', 'WITHIN_A_DISTANCE', os.path.join(config.workspace, config.wPolyShp), str(desc.meanCellWidth) + ' Meters')
        if int(arcpy.GetCount_management('tmp_bfPtsZ_lyr').getOutput(0)) > 0:
            arcpy.DeleteFeatures_management('tmp_bfPtsZ_lyr')

        #  d. create bankfull elevation raster
        tmp_raw_bfe = NaturalNeighbor(bfPtsZ, 'demZ', 0.1)
        tmp_bfe = ExtractByMask(tmp_raw_bfe, os.path.join(config.workspace, config.bfPolyShp))

        #  e. create bfe slope raster
        bfSlope = Slope(tmp_bfe, 'DEGREE')
        bfSlope.save(os.path.join(evpath, 'bfeSlope.tif'))

        #  f. calculate mean bfe slope over bfw neighborhood
        neighborhood = NbrRectangle(bfw, bfw, 'MAP')
        slope_focal = FocalStatistics(bfSlope, neighborhood, 'MEAN')

        #  g. clip to bankfull polygon
        meanBFSlope = ExtractByMask(slope_focal, os.path.join(config.workspace, config.bfPolyShp))

        #  h. save output
        meanBFSlope.save(os.path.join(evpath, 'bfeSlope_meanBFW.tif'))

        #  i. delete intermediate fcs
        fcs = [bfPts, bfLine, bfPtsZ]
        for fc in fcs:
            arcpy.Delete_management(fc)
    else:
        bfSlope = Raster(os.path.join(evpath, 'bfeSlope.tif'))
        meanBFSlope = Raster(os.path.join(evpath, 'bfeSlope_meanBFW.tif'))

    #  --channel edge polygon--

    if not os.path.exists(os.path.join(evpath, 'channelEdge.shp')):
        print '...channel edge...'

        #  a. create copy of bfPoly and wPoly
        bfpoly = arcpy.CopyFeatures_management(os.path.join(config.workspace, config.bfPolyShp), 'in_memory/tmp_bfpoly')
        wpoly = arcpy.CopyFeatures_management(os.path.join(config.workspace, config.wPolyShp), 'in_memory/tmp_wpoly')

        #  b. remove small polygon parts from bfPoly wPoly
        #     threshold: < 5% of total area
        bfelim = arcpy.EliminatePolygonPart_management(bfpoly, 'in_memory/tmp_bfelim', 'PERCENT', '', 15, 'ANY')

        #  c. erase wPoly from bfPoly
        erase = arcpy.Erase_analysis(bfelim, wpoly, 'in_memory/tmp_erase', '')

        #  d. buffer output by one cell
        #     ensures there are no 'breaks' along the banks due to areas
        #     where bankfull and wetted extent were the same
        erasebuffer = arcpy.Buffer_analysis(erase, 'in_memory/tmp_buffer', 0.1, 'FULL')

        edge = arcpy.EliminatePolygonPart_management(erasebuffer, 'in_memory/tmp_edge', 'AREA', 3*bfw, '', 'ANY')

        #  e. merge multipart edge polgyons into single part polygon
        edge_sp = arcpy.MultipartToSinglepart_management(edge, 'in_memory/edge_sp')

        #  f. attribute edge as being mid-channel or not
        arcpy.AddField_management(edge_sp, 'midEdge', 'TEXT', '', '', 5)
        arcpy.MakeFeatureLayer_management(edge_sp, 'edge_lyr')

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

        arcpy.CopyFeatures_management(edge_sp, os.path.join(evpath, 'channelEdge.shp'))
    else:
        arcpy.MakeFeatureLayer_management(os.path.join(evpath, 'channelEdge.shp'), 'edge_lyr')

    #  --thalweg high points--

    if not os.path.exists(os.path.join(evpath, 'potentialRiffCrests.shp')):
        print '...thalweg high points...'

        #  a. create thalweg points along thalweg polyline [distance == dem cell size]
        distance = float(desc.meanCellWidth)
        thalPts = arcpy.CreateFeatureclass_management('in_memory', 'tmp_thalPts', 'POINT', '', 'DISABLED', 'DISABLED', dem)
        arcpy.AddField_management(thalPts, 'UID', 'LONG')
        arcpy.AddField_management(thalPts, 'thalDist', 'FLOAT')

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
        arcpy.AddField_management(thalPts, 'trResid', 'FLOAT')
        arcpy.AddField_management(thalPts, 'trStResid', 'FLOAT')
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

    if not os.path.exists(os.path.join(evpath, 'mIndex.tif')):
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
        nCellWidth = round(bfw / desc.meanCellWidth)
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
    else:
        mIndex = Raster((os.path.join(evpath, 'mIndex.tif')))

    #  --width expansion ratio--

    print '...width expansion ratio...'

    #  in DS direction width ratios  </> 1 indicate channel constriction/expansion
    #  a. calculate xs width ratio (xs[n+1]length/xs[n]length) separately for the main channel and each side channel
    #  b. assign minimum and maximum width ratio to each channel unit polygon

    #  step 1: copy inputs to temporary *.shps
    bfxs = arcpy.CopyFeatures_management(os.path.join(config.workspace, config.bfXS), 'in_memory/tmp_bfxs')
    bfcl = arcpy.CopyFeatures_management(os.path.join(config.workspace, config.bfCL), 'in_memory/tmp_bfcl')

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

    if not os.path.exists(os.path.join(evpath, 'channelNodes.shp')):
        print '...channel nodes...'

        chNodes_mp = arcpy.Intersect_analysis(os.path.join(config.workspace, config.bfCL), 'in_memory/tmp_chNodes_multiPart', 'NO_FID', '', 'POINT')

        if arcpy.management.GetCount(chNodes_mp)[0] != '0':

            chNodes_sp = arcpy.MultipartToSinglepart_management(chNodes_mp, 'in_memory/chNodes_sp')

            arcpy.AddField_management(chNodes_sp, 'ChNodeID', 'SHORT')
            arcpy.AddField_management(chNodes_sp, 'ChannelID', 'TEXT', 10)
            arcpy.AddField_management(chNodes_sp, 'ChNodeType', 'TEXT', 10)

            fields = ['OID@', 'Channel', 'CLID', 'ChNodeID', 'ChannelID']
            with arcpy.da.UpdateCursor(chNodes_sp, fields) as cursor:
                for row in cursor:
                    if row[1] == 'Main':
                        cursor.deleteRow()
                    else:
                        row[3] = row[0]
                        row[4] = row[1] + str(row[2])
                        cursor.updateRow(row)

            arcpy.MakeFeatureLayer_management(os.path.join(config.workspace, config.bfCL), 'mainCL_lyr', """ "Channel" = 'Main' """)
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

            arcpy.LocateFeaturesAlongRoutes_lr(chNodes_sp, mainCL_Route, 'CLID', float(desc.meanCellWidth), 'tbl_Routes.dbf', 'RID POINT MEAS')

            arcpy.JoinField_management(chNodes_sp, 'ChNodeID', 'tbl_Routes.dbf', 'ChNodeID', ['MEAS'])

            arcpy.Statistics_analysis(chNodes_sp, 'tbl_chNodeMax.dbf', [['MEAS', 'MAX']], 'ChannelID')

            arcpy.JoinField_management(chNodes_sp, 'ChannelID', 'tbl_chNodeMax.dbf', 'ChannelID', ['MAX_MEAS'])

            fields = ['MEAS', 'MAX_MEAS', 'ChNodeType']
            with arcpy.da.UpdateCursor(chNodes_sp, fields) as cursor:
                for row in cursor:
                    if row[0] < row[1]:
                        row[2] = 'Diffluence'
                    else:
                        row[2] = 'Confluence'
                    cursor.updateRow(row)

            arcpy.Delete_management(chNodes_mp)
            arcpy.CopyFeatures_management(chNodes_sp, os.path.join(evpath, 'channelNodes.shp'))

    #  ---------------------------------
    #  tier 3 classification
    #  ---------------------------------

    print '...classifying Tier 3 morphology...'

    #  create copy of tier 2 shapefile
    units = arcpy.CopyFeatures_management(os.path.join(outpath, 'Tier2_InChannel.shp'), 'in_memory/tmp_tier3_inChannel')
    arcpy.MakeFeatureLayer_management(units, 'units_lyr')

    #  add attribute fields to tier 2 polygon shapefile
    nfields = [('Morphology', 'TEXT', '25'), ('UnitID', 'SHORT', ''), ('Forcing', 'TEXT', '25'),('Width', 'FLOAT', ''), ('Length', 'FLOAT', ''), ('Position', 'TEXT', '20'),
               ('OnThalweg', 'TEXT', '5'), ('Channel', 'TEXT', '5'), ('Confluence', 'TEXT', '5'), ('Diffluence', 'TEXT', '5'), ('RiffCrest', 'TEXT', '5'), ('wRatioMin', 'FLOAT', ''),
               ('wRatioMax', 'FLOAT', ''), ('mIndexMean', 'FLOAT', ''), ('mBend', 'TEXT', '15'), ('BFESlope', 'FLOAT', ''), ('meanSlope', 'FLOAT', '')]


    for nfield in nfields:
        arcpy.AddField_management(units, nfield[0], nfield[1], '', '', nfield[2])

    #  create unit id field to make sure joins correctly execute
    fields = ['OID@', 'UnitID', 'Forcing']
    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            row[1] = row[0]
            row[2] = 'NA'
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
    # fields = ['Tier1', 'UnitForm', 'Width', 'Length', 'Orient']
    # with arcpy.da.UpdateCursor(units, fields) as cursor:
    #     for row in cursor:
    #         if row[0] == 'In-Channel':
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

    arcpy.JoinField_management(units, 'UnitID', units_minBound, 'UnitID', ['Orient'])

    #  --calculate unit position--

    print '...unit position...'

    edge_units = arcpy.SpatialJoin_analysis('edge_lyr', units, 'in_memory/tmp_edge_units', 'JOIN_ONE_TO_MANY', '', '', 'WITHIN_A_DISTANCE', 0.1 * ww)
    edge_tbl = arcpy.Frequency_analysis(edge_units, 'tbl_edge_units.dbf', ['UnitID'])
    arcpy.AddField_management(edge_tbl, 'edgeCount', 'SHORT')
    arcpy.CalculateField_management(edge_tbl, 'edgeCount', '[FREQUENCY]')
    arcpy.JoinField_management(units, 'UnitID', edge_tbl, 'UnitID', ['edgeCount'])

    arcpy.SelectLayerByAttribute_management('edge_lyr', 'NEW_SELECTION', """ "midEdge" = 'Y' """)
    #arcpy.SelectLayerByLocation_management('units_lyr', 'HAVE_THEIR_CENTER_IN', 'edge_lyr', '', 'NEW_SELECTION')
    #arcpy.SelectLayerByAttribute_management('units_lyr', 'SUBSET_SELECTION', """ "Morphology" = 'Mound' """)
    arcpy.SelectLayerByAttribute_management('units_lyr', 'NEW_SELECTION', """ "UnitForm" = 'Mound' """)
    mound_centroid = arcpy.FeatureToPoint_management('units_lyr', os.path.join(evpath, 'tmp_mound_centroid.shp'), "INSIDE")
    arcpy.MakeFeatureLayer_management(mound_centroid, 'centroid_lyr')
    arcpy.SelectLayerByLocation_management('centroid_lyr', 'INTERSECT', 'edge_lyr', '', 'NEW_SELECTION')
    arcpy.SelectLayerByLocation_management('units_lyr', 'INTERSECT', 'centroid_lyr', '', 'SUBSET_SELECTION')

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
    arcpy.SelectLayerByLocation_management('units_lyr', 'INTERSECT', os.path.join(config.workspace, config.thalwegShp), '', 'NEW_SELECTION')
    with arcpy.da.UpdateCursor('units_lyr', 'OnThalweg') as cursor:
        for row in cursor:
            row[0] = 'Y'
            cursor.updateRow(row)

    # if unit does not intersect thalweg assign 'N'
    arcpy.SelectLayerByAttribute_management('units_lyr', 'SWITCH_SELECTION')
    with arcpy.da.UpdateCursor('units_lyr', 'OnThalweg') as cursor:
        for row in cursor:
            row[0] = 'N'
            cursor.updateRow(row)

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

    #start test
    #  --calculate unit length and width--
    print '...unit length and width...'

    #  create separate layer for main and side channel units
    arcpy.MakeFeatureLayer_management(units, 'units_side_lyr', """ "Channel" = 'Side' """)
    arcpy.MakeFeatureLayer_management(units, 'units_main_lyr', """ "Channel" = 'Main' """)

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
    arcpy.Statistics_analysis(unit_bfxs_side, 'in_memory/tbl_unit_bfxs_side', [['xsWid', 'MEAN']], 'UnitID')

    unit_bfxs_main = arcpy.SpatialJoin_analysis('units_main_lyr', bfxs_main_clip, 'in_memory/tmp_unit_bfxs_main', 'JOIN_ONE_TO_MANY', '', '', 'CONTAINS')
    arcpy.Statistics_analysis(unit_bfxs_main, 'in_memory/tbl_unit_bfxs_main', [['xsWid', 'MEAN']], 'UnitID')

    arcpy.Merge_management(['in_memory/tbl_unit_bfxs_side','in_memory/tbl_unit_bfxs_main'], 'in_memory/tbl_unit_bfxs_merge')
    arcpy.JoinField_management(units, 'UnitID', 'in_memory/tbl_unit_bfxs_merge', 'UnitID', ['MEAN_xsWid'])

    #  calculate unit length and width
    fields = ['ValleyUnit', 'UnitForm', 'MEAN_xsWid', 'Width', 'Area', 'Length']
    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            if row[0] == 'In-Channel':
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

    if os.path.exists(os.path.join(evpath, 'channelNodes.shp')):
        arcpy.MakeFeatureLayer_management(os.path.join(evpath, 'channelNodes.shp'), 'confluence_lyr', """ "ChNodeType" = 'Confluence' """)
        arcpy.MakeFeatureLayer_management(os.path.join(evpath, 'channelNodes.shp'), 'diffluence_lyr', """ "ChNodeType" = 'Diffluence' """)

        #  identify units that are in close proximity to channel confluence [assigning Y/N]
        arcpy.SelectLayerByLocation_management('units_lyr', 'WITHIN_A_DISTANCE', 'confluence_lyr', str(0.1 * bfw) + ' Meters', 'NEW_SELECTION')
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
        arcpy.SelectLayerByLocation_management('units_lyr', 'WITHIN_A_DISTANCE', 'diffluence_lyr', str(0.1 * bfw) + ' Meters', 'NEW_SELECTION')
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
    arcpy.SelectLayerByLocation_management('units_lyr', 'INTERSECT', os.path.join(evpath, 'potentialRiffCrests.shp'), '', 'NEW_SELECTION')
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
    arcpy.Statistics_analysis(units_bfxs2, 'tbl_units_bfxs_stats2', [['widthRatio', 'MIN'],['widthRatio', 'MAX']], 'UnitID')
    arcpy.JoinField_management('units_lyr', 'UnitID', 'tbl_units_bfxs_stats2', 'UnitID', ['MIN_widthRatio','MAX_widthRatio'])

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
    ZonalStatisticsAsTable(units, 'UnitID', mIndex, 'tbl_mIndex.dbf', 'DATA', 'MEAN')
    #  join mean value back to units shp
    arcpy.JoinField_management(units, 'UnitID', 'tbl_mIndex.dbf', 'UnitID', 'MEAN')

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

    # ----------------------------------------------------------
    # Attribute bankfull surface slope
    # TODO: May want to use meanBFSlope (bankfull slope averaged over bfw) rather than bfSlope
    print '...bankfull surface slope...'

    #  get mean value for each unit
    ZonalStatisticsAsTable(units, 'UnitID', bfSlope, 'tbl_bfeSlope.dbf', 'DATA', 'MEAN')
    #  join mean value back to units shp
    arcpy.JoinField_management(units, 'UnitID', 'tbl_bfeSlope.dbf', 'UnitID', 'MEAN')

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
    ZonalStatisticsAsTable(units, 'UnitID', os.path.join(evpath, 'slope_inCh_' + os.path.basename(os.path.join(config.workspace, config.inDEM))), 'tbl_slope.dbf', 'DATA', 'MEAN')
    #  join mean value back to units shp
    arcpy.JoinField_management(units, 'UnitID', 'tbl_slope.dbf', 'UnitID', 'MEAN')

    fields = ['MEAN', 'meanSlope']
    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    arcpy.DeleteField_management(units, ['MEAN'])

    # ----------------------------------------------------------
    # Attribute tier 3 concavities

    print '...classifying tier 3 concavities...'

    fields = ['UnitForm', 'Forcing', 'Position', 'Orient', 'OnThalweg', 'Confluence', 'mBend', 'Morphology', 'Area']

    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            if row[0] == 'Bowl':
                if row[8] > 0.25 * bfw:
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
                    row[7] = 'Transition'

            cursor.updateRow(row)

    # ----------------------------------------------------------
    # Attribute tier 3 planar features

    print '...classifying tier 3 planar features...'

    fields = ['UnitForm', 'Forcing', 'Orient', 'RiffCrest', 'BFESlope', 'Morphology', 'Area', 'Length']

    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            if row[0] == 'Plane':
                if row[6] > bfw:
                    if row[1] == 'NA':  # if not forced
                        if row[2] == 'Transverse':
                            if row[3] == 'Y':
                                # row[0] = 'Convexity'
                                row[5] = 'Riffle'
                            else:
                                row[5] = 'Transition'
                        elif row[7] < bfw:
                            row[5] = 'Transition'
                        else:  # if streamwise
                            row[5] = 'Run'
                else:
                    row[5] = 'Transition'
            cursor.updateRow(row)

        # ----------------------------------------------------------
        # Attribute tier 3 trough features

        print '...classifying tier 3 trough features...'

        fields = ['UnitForm', 'Forcing', 'Orient', 'RiffCrest', 'BFESlope', 'Morphology', 'Area', 'Length', 'UnitShape']

        with arcpy.da.UpdateCursor(units, fields) as cursor:
            for row in cursor:
                if row[0] == 'Trough':
                    if row[6] > bfw:
                        if row[1] == 'NA':  # if not forced
                            if row[2] == 'Transverse':
                                if row[3] == 'Y':
                                    row[0] = 'Saddle'
                                    row[8] = 'Convexity'
                                    row[5] = 'Riffle'
                                else:
                                    row[5] = 'Transition'
                            elif row[7] < bfw:
                                row[5] = 'Transition'
                            else:  # if streamwise
                                if row[4] < 0.5:
                                    row[5] = 'Chute'
                                elif row[4] < 2.0:
                                    row[5] = 'Glide'
                                elif row[4] < 4.0:
                                    row[5] = 'Rapid'
                                else:
                                    row[5] = 'Cascade'
                    else:
                        row[5] = 'Transition'
                cursor.updateRow(row)

        # ----------------------------------------------------------
        # Attribute tier 3 saddle features

        print '...classifying tier 3 saddle features...'

        fields = ['UnitForm', 'Forcing', 'Morphology']

        with arcpy.da.UpdateCursor(units, fields) as cursor:
            for row in cursor:
                if row[0] == 'Saddle':
                    if row[1] == 'NA':  # if not forced
                        row[2] = 'Riffle'
                    else:
                        row[2] = 'Forced Riffle'
                cursor.updateRow(row)

    # ----------------------------------------------------------
    # Attribute tier 3 convexities

    print '...classifying Tier 3 mounds...'

    with arcpy.da.UpdateCursor(units, ['UnitForm', 'meanSlope', 'Morphology', 'Area']) as cursor:
        for row in cursor:
            if row[0] == 'Wall':
                # if row[3] > 0.25 * bfw:
                #     row[2] = 'Bank'
                row[2] = 'Bank'
                # else:
                #     row[2] = 'Transition'
            cursor.updateRow(row)

    arcpy.MakeFeatureLayer_management(units, 'chute_lyr', """ "Morphology" = 'Chute' """)

    fields = ['UnitForm', 'Forcing', 'Position', 'Orient', 'mBend', 'Morphology', 'Area']

    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            if row[0] == 'Mound' and row[5] != 'Bank':
                if row[6] > bfw:
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
                                arcpy.SelectLayerByLocation_management('units_lyr', 'WITHIN_A_DISTANCE', 'chute_lyr', str(bfw * 0.25) + ' Meters', 'NEW_SELECTION')
                                row[5] = 'Diagonal Bar'
                                arcpy.SelectLayerByAttribute_management('units_lyr', 'SWITCH_SELECTION')
                                row[5] = 'Longitudinal Bar'
                            else:
                                row[5] = 'Unit Bar'
                else:
                    row[5] = 'Transition'
            cursor.updateRow(row)

    # ----------------------------------------------------------
    # Clean-up transition zones

    print '...cleaning up transition zones...'

    #arcpy.SelectLayerByAttribute_management('units_lyr', 'NEW_SELECTION', """ "Morphology" = 'Transition' """)
    #arcpy.CopyFeatures_management('units_lyr', 'in_memory/tmp_Transition')
    #Transition = arcpy.Dissolve_management('units_lyr', 'in_memory/tmp_TransitionMerge', ['UnitForm'])
    #transitionzone = arcpy.Dissolve_management('in_memory/tmp_TransitionZone', 'in_memory/tmp_TransitionMerge', ['UnitForm'])

    # with arcpy.da.UpdateCursor(units, 'UnitForm') as cursor:
    #     for row in cursor:
    #         if row[0] == 'Transition':
    #             cursor.deleteRow()

    #arcpy.Merge_management([units, transitionzone], os.path.join(outpath, 'Tier3_InChannel.shp'))

    arcpy.CopyFeatures_management(units, os.path.join(outpath, 'Tier3_InChannel.shp'))

    fields = ['ValleyUnit', 'UnitForm', 'Morphology', 'SHAPE@Area', 'Area', 'OID@', 'UnitID']

    with arcpy.da.UpdateCursor(os.path.join(outpath, 'Tier3_InChannel.shp'), fields) as cursor:
        for row in cursor:
            if row[1] == 'Transition':
                row[0] = 'In-Channel'
                row[2] = 'Transition'
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
