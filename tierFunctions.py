#  import required modules and extensions
import arcpy
import os
import math
import numpy
import fnmatch
import tempfile
from arcpy.sa import *
arcpy.CheckOutExtension('Spatial')
arcpy.CheckOutExtension('3D')


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



def guAttributes(units, bfw, dem, tmp_thalwegs, bfSlope, bfSlope_Smooth, evpath, **myVars):
    fields = arcpy.ListFields(units)
    keep = ['ValleyUnit', 'UnitShape', 'UnitForm', 'GU', 'GUKey', 'FlowUnit']
    drop = []
    for field in fields:
        if not field.required and field.name not in keep and field.type <> 'Geometry':
            drop.append(field.name)
    if len(drop) > 0:
        arcpy.DeleteField_management(units, drop)

    # add attribute fields to tier units shapefile
    nfields = [('UnitID', 'SHORT', ''), ('ForceType', 'TEXT', '25'), ('ForceElem', 'TEXT', '25'), ('ForceHyd', 'TEXT', '15'),
               ('Perimeter', 'DOUBLE', ''), ('ElongRatio', 'DOUBLE', ''), ('Morphology', 'TEXT', '20'),
               ('Position', 'TEXT', '20'), ('Orient', 'DOUBLE', ''), ('OrientCat', 'TEXT', '15'),
               ('bfSlope', 'DOUBLE', ''), ('bfSlopeSm', 'DOUBLE', ''), ('bedSlope', 'DOUBLE', '')]

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
    fields = ['OID@', 'UnitID', 'SHAPE@Area', 'Area', 'SHAPE@LENGTH', 'Perimeter', 'ForceType', 'ForceElem', 'ForceHyd']
    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            row[1] = row[0]
            row[3] = row[2]
            row[5] = row[4]
            row[6] = 'NA'
            row[7] = 'NA'
            row[8] = 'NA'
            cursor.updateRow(row)

    print "...unit length, width, length to width ratio and orientation..."

    #  calculate unit length, width, orientation (i.e., angle) using minimum bounding polygon
    unit_minbound = arcpy.MinimumBoundingGeometry_management(units, 'in_memory/units_minbound', 'RECTANGLE_BY_WIDTH', '', '', 'MBG_FIELDS')

    # add attribute fields to minimum bounding units
    nfields = [('Width', 'DOUBLE', ''), ('Length', 'DOUBLE', ''), ('LtoWRatio', 'DOUBLE', ''),
               ('bfwRatio', 'DOUBLE', ''), ('unitOrient', 'DOUBLE', '')]
    for nfield in nfields:
        arcpy.AddField_management(unit_minbound, nfield[0], nfield[1], '', '', nfield[2])

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
    arcpy.JoinField_management(units, 'UnitID', unit_minbound, 'UnitID', ['Length', 'Width', 'LtoWRatio', 'bfwRatio', 'unitOrient'])

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
    with arcpy.da.SearchCursor(os.path.join(myVars['workspace'], myVars['bfCL']), search_fields) as search:
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
    bfcl_split = arcpy.SplitLineAtPoint_management(os.path.join(myVars['workspace'], myVars['bfCL']), cl_pts, 'in_memory/bfcl_split', '0.1 Meters')

    #  d. get centerline segment oreintation using minimum bounding geometry
    cl_minbound = arcpy.MinimumBoundingGeometry_management(bfcl_split, 'in_memory/cl_minbound', 'RECTANGLE_BY_WIDTH', '', '', 'MBG_FIELDS')
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
    arcpy.CalculateField_management(edge_tbl, 'onEdge', '!FREQUENCY!', 'PYTHON_9.3')
    arcpy.JoinField_management(units, 'UnitID', edge_tbl, 'UnitID', ['onEdge'])

    edge_units2 = arcpy.SpatialJoin_analysis(nearEdge_buffer, units, 'in_memory/tmp_edge_units', 'JOIN_ONE_TO_MANY',
                                             '',
                                             '', 'INTERSECT')
    edge_tbl2 = arcpy.Frequency_analysis(edge_units2, 'tbl_edge_units2.dbf', ['UnitID'])
    arcpy.AddField_management(edge_tbl2, 'nearEdge1', 'SHORT')
    arcpy.CalculateField_management(edge_tbl2, 'nearEdge1', '!FREQUENCY!', 'PYTHON_9.3')
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

    unit_thalweg_ch = arcpy.SpatialJoin_analysis(units, tmp_thalwegs, 'in_memory/unit_thalwegs_ch', 'JOIN_ONE_TO_MANY', '', '', 'INTERSECT')

    channelDict = {}  # create a dictionary for unit/thalweg channel
    thalwegDict = {}  # create a dictionary for unit/thalweg type

    with arcpy.da.SearchCursor(unit_thalweg_ch, ['UnitID', 'Channel', 'ThalwegTyp']) as cursor:
        for row in cursor:
            unitid = row[0]
            channel = str(row[1])
            thalwegtype = str(row[2])
            if not row[1] == None:  # if channel field isn't blank/empty
                if unitid not in channelDict:  # if the unit id isn't in the dict, add it along with the channel
                    channelDict[unitid] = [channel]
                else:
                    if channel not in channelDict[unitid]:  # if the channel isn't in the dictionary with the unit id key, append to the list
                        channelDict[unitid].append(channel)
                if unitid not in thalwegDict:  # if the unit id isn't in the dict, add it along with the thalweg
                    thalwegDict[unitid] = [thalwegtype]
                else:
                    if thalwegtype not in thalwegDict[unitid]:  # if the channel isn't in the dictionary with the unit id key, append to the list
                        thalwegDict[unitid].append(thalwegtype)
            else:
                channelDict[unitid] = ['None']
                thalwegDict[unitid] = ['None']

    arcpy.AddField_management(units, 'ThalwegCh', 'TEXT', '', '', 50)
    arcpy.AddField_management(units, 'ThalwegTyp', 'TEXT', '', '', 50)

    with arcpy.da.UpdateCursor(units, ['UnitID', 'ThalwegCh', 'ThalwegTyp']) as cursor:
        for row in cursor:
            unitid = row[0]
            row[1] = ', '.join(channelDict[unitid])
            row[2] = ', '.join(thalwegDict[unitid])
            cursor.updateRow(row)

    thalweg_ct = arcpy.Statistics_analysis(unit_thalweg_ch, 'in_memory/thalweg_ct', 'Join_Count SUM', 'UnitID')
    arcpy.AddField_management(thalweg_ct, 'ThalwegCt', 'SHORT')
    with arcpy.da.UpdateCursor(thalweg_ct, ['SUM_Join_Count', 'ThalwegCt']) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    arcpy.JoinField_management(units, 'UnitID', thalweg_ct, 'UnitID', 'ThalwegCt')

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
        os.path.join(myVars['workspace'], myVars['inDEM']))), 'tbl_slope.dbf', 'DATA', 'MEAN')
    #  join mean value back to units shp
    arcpy.JoinField_management(units, 'UnitID', 'tbl_slope.dbf', 'UnitID', 'MEAN')

    fields = ['MEAN', 'bedSlope']
    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    arcpy.DeleteField_management(units, ['MEAN'])

    return (units)

#  --tier 1 function--

#  classifies tier 1 units
#  valley units: in-channel, out-of-channel
#  flow units: submerged, emergent, high


def tier1(**myVars):

    print 'Starting Tier 1 classification...'

    #  create temporary workspace
    tmp_dir = tempfile.mkdtemp()

    #  environment settings
    arcpy.env.workspace = tmp_dir # set workspace to temporary workspace
    arcpy.env.overwriteOutput = True  # set to overwrite output

    #  import required rasters
    dem = Raster(os.path.join(myVars['workspace'], myVars['inDEM']))

    #  define raster environment settings
    desc = arcpy.Describe(dem)
    arcpy.env.extent = desc.Extent
    arcpy.env.outputCoordinateSystem = desc.SpatialReference
    arcpy.env.cellSize = desc.meanCellWidth

    #  check if evidence layer and output folders exits, if not create them
    folder_list = ['EvidenceLayers', 'Output']
    for folder in folder_list:
        if not os.path.exists(os.path.join(myVars['workspace'], folder)):
            os.makedirs(os.path.join(myVars['workspace'], folder))

    #  create gut run folder and set output path
    if myVars['runFolderName'] != 'Default' and myVars['runFolderName'] != '':
        outpath = os.path.join(myVars['workspace'], 'Output', myVars['runFolderName'])
    else:
        runFolders = fnmatch.filter(next(os.walk(os.path.join(myVars['workspace'], 'Output')))[1], 'Run_*')
        if len(runFolders) >= 1:
            runNum = int(max([i.split('_', 1)[1] for i in runFolders])) + 1
        else:
            runNum = 1
        outpath = os.path.join(myVars['workspace'], 'Output', 'Run_%03d' % runNum)

    os.makedirs(outpath)

    #  set evidence layers output path
    evpath = os.path.join(myVars['workspace'], 'EvidenceLayers')

    #  ----------------------------------
    #    calculate reach-level metrics
    #  ----------------------------------

    #  --calculate integrated bankfull width--
    bfw = intWidth_fn(os.path.join(myVars['workspace'], myVars['bfPolyShp']), os.path.join(myVars['workspace'],myVars['bfCL']))

    #  --------------------------
    #    tier 1 evidence layers
    #  --------------------------
    print '...deriving evidence layers...'

    # --bankfull channel raster--
    if not os.path.exists(os.path.join(evpath, 'bfCh.tif')):
        print '...deriving bankfull channel raster...'
        bf_raw = arcpy.PolygonToRaster_conversion(os.path.join(myVars['workspace'], myVars['bfPolyShp']), 'FID', 'in_memory/tmp_bfCh', 'CELL_CENTER') #  convert bankfull channel polygon to raster
        outCon = Con(IsNull(bf_raw), 0, 1) #  set cells inside/outside bankfull channel polygon to 1/0
        bf = ExtractByMask(outCon, dem) #  clip to dem
        bf.save(os.path.join(evpath, 'bfCh.tif')) #  save output
    else:
        bf = Raster(os.path.join(evpath, 'bfCh.tif'))

    #  -------------------------
    #    tier 1 classifcation
    #  -------------------------
    print '...classifying valley  units...'

    #  convert bankfull channel raster to polygon
    valley_units = arcpy.RasterToPolygon_conversion(bf, 'in_memory/valley_units', 'NO_SIMPLIFY', 'VALUE')

    #  covert units from multipart to singlepart polygons
    valley_units_sp = arcpy.MultipartToSinglepart_management(valley_units, 'in_memory/valley_units_sp')

    #  create and attribute 'ValleyID' and 'ValleyUnit' fields
    arcpy.AddField_management(valley_units_sp, 'ValleyID', 'SHORT')
    arcpy.AddField_management(valley_units_sp, 'ValleyUnit', 'TEXT', '', '', 20)
    ct = 1
    with arcpy.da.UpdateCursor(valley_units_sp, ['ValleyID', 'GRIDCODE', 'ValleyUnit']) as cursor:
        for row in cursor:
            row[0] = ct
            if row[1] == 0:
                row[2] = 'Out-of-Channel'
            else:
                row[2] = 'In-Channel'
            ct += 1
            cursor.updateRow(row)

    print '...classifying flow units...'

    #  add flow type field and attribute high and emergent classes using valley unit shp
    flowtype_units_raw = arcpy.CopyFeatures_management(valley_units_sp, 'in_memory/flowtype_units_raw')
    arcpy.AddField_management(flowtype_units_raw, 'FlowUnit', 'TEXT', '', '', 12)
    with arcpy.da.UpdateCursor(flowtype_units_raw, ['ValleyUnit', 'FlowUnit']) as cursor:
        for row in cursor:
            if row[0] == 'Out-of-Channel':
                row[1] = 'High'
            else:
                row[1] = 'Emergent'
            cursor.updateRow(row)

    #  add flow type field and attribute submerged class using water extent shp
    wPoly = arcpy.CopyFeatures_management(os.path.join(myVars['workspace'], myVars['wPolyShp']), 'in_memory/wPoly')
    arcpy.AddField_management(wPoly, 'FlowUnit', 'TEXT', '', '', 12)
    with arcpy.da.UpdateCursor(wPoly, ['FlowUnit']) as cursor:
        for row in cursor:
            row[0] = 'Submerged'
            cursor.updateRow(row)

    #  create flow type polygon by updating/merging shps
    flowtype_units = arcpy.Update_analysis(flowtype_units_raw, wPoly, 'in_memory/flowtype_units')

    #  intersect flow type polygon with valley units
    t1_units_raw = arcpy.Intersect_analysis([valley_units_sp, flowtype_units], 'in_memory/t1_units_raw', 'ALL')

    #  covert units from multipart to singlepart polygons
    t1_units_sp = arcpy.MultipartToSinglepart_management(t1_units_raw, 'in_memory/t1_units_sp')

    #  add and calculate unit area field
    arcpy.AddField_management(t1_units_sp, 'Area', 'DOUBLE')
    with arcpy.da.UpdateCursor(t1_units_sp, ['SHAPE@AREA', 'Area']) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    #  find tiny units (area < 0.05 * bfw) and merge with unit that shares longest border
    t1_units_sp_lyr = arcpy.MakeFeatureLayer_management(t1_units_sp, 't1_units_sp_lyr')
    arcpy.SelectLayerByAttribute_management(t1_units_sp_lyr, 'NEW_SELECTION', '"Area" < ' + str(0.05 * bfw))
    t1_units = arcpy.Eliminate_management(t1_units_sp_lyr, 'in_memory/t1_units', "LENGTH")

    #  add and populate flow unit id field
    arcpy.AddField_management(t1_units, 'FlowID', 'SHORT')
    ct = 1
    with arcpy.da.UpdateCursor(t1_units, ['FlowID']) as cursor:
        for row in cursor:
            row[0] = ct
            ct += 1
            cursor.updateRow(row)

    #  remove unnecessary fields
    fields = arcpy.ListFields(t1_units)
    keep = ['OBJECTID', 'Shape', 'ValleyID', 'ValleyUnit', 'FlowUnit', 'FlowID', 'Area']
    drop = [x.name for x in fields if x.name not in keep]
    arcpy.DeleteField_management(t1_units, drop)

    #  save tier 1 output
    arcpy.CopyFeatures_management(t1_units, os.path.join(outpath, 'Tier1.shp'))

    #  clear temporary workspace
    print '...removing intermediary surfaces...'

    arcpy.Delete_management("in_memory")
    arcpy.Delete_management(tmp_dir)

    print '...done with Tier 1 classification.'

#  --tier 2 function--

#  classifies tier 2 units
#  unit shape: concavity, planar, convexity
#  unit form: bowl, bowl transition, trough, plane, mound transition, mound, wall


def tier2(**myVars):

    print 'Starting Tier 2 classification...'

    #  clear temporary workspace
    arcpy.Delete_management("in_memory")

    #  create temporary workspace
    tmp_dir = tempfile.mkdtemp()

    #  environment settings
    arcpy.env.workspace = tmp_dir # set workspace to temporary workspace
    arcpy.env.overwriteOutput = True  # set to overwrite output

    #  set evidence layers output path
    evpath = os.path.join(myVars['workspace'], 'EvidenceLayers')

    #  set gut run output path
    if myVars['runFolderName'] != 'Default' and myVars['runFolderName'] != '':
        outpath = os.path.join(myVars['workspace'], 'Output', myVars['runFolderName'])
    else:
        runFolders = fnmatch.filter(next(os.walk(os.path.join(myVars['workspace'], 'Output')))[1], 'Run_*')
        runNum = int(max([i.split('_', 1)[1] for i in runFolders]))
        outpath = os.path.join(myVars['workspace'], 'Output', 'Run_%03d' % runNum)

    #  import required rasters
    dem = Raster(os.path.join(myVars['workspace'], myVars['inDEM']))
    bf = Raster(os.path.join(myVars['workspace'], 'EvidenceLayers/bfCh.tif'))  # created in 'tier1' module

    #  define raster environment settings
    desc = arcpy.Describe(dem)
    arcpy.env.extent = desc.Extent
    arcpy.env.outputCoordinateSystem = desc.SpatialReference
    arcpy.env.cellSize = desc.meanCellWidth

    #  check thalweg shp to see if it contains 'Channel' and 'ThalwegType' fields
    #  if not, add fields and attribute both as 'Main'
    if not 'Channel' in [f.name for f in arcpy.ListFields(os.path.join(myVars['workspace'], myVars['thalwegShp']))]:
        arcpy.AddField_management(os.path.join(myVars['workspace'], myVars['thalwegShp']), 'Channel', 'TEXT', '', '', 15)
        with arcpy.da.UpdateCursor(os.path.join(myVars['workspace'], myVars['thalwegShp']), 'Channel') as cursor:
            for row in cursor:
                row[0] = 'Main'
                cursor.updateRow(row)

    if not 'ThalwegTyp' in [f.name for f in arcpy.ListFields(os.path.join(myVars['workspace'], myVars['thalwegShp']))]:
        arcpy.AddField_management(os.path.join(myVars['workspace'], myVars['thalwegShp']), 'ThalwegTyp', 'TEXT', '', '', 15)
        with arcpy.da.UpdateCursor(os.path.join(myVars['workspace'], myVars['thalwegShp']), 'ThalwegTyp') as cursor:
            for row in cursor:
                row[0] = 'Main'
                cursor.updateRow(row)

    #  check bankfull centerline shp to see if it contains 'Channel' field
    #  if not, add field and attribute as 'Main' also add 'CLID' field a populate iteratively
    if not 'Channel' in [f.name for f in arcpy.ListFields(os.path.join(myVars['workspace'], myVars['bfCL']))]:
        arcpy.AddField_management(os.path.join(myVars['workspace'], myVars['bfCL']), 'Channel', 'TEXT', '', '', 15)
        arcpy.AddField_management(os.path.join(myVars['workspace'], myVars['bfCL']), 'CLID', 'SHORT')
        ct = 1
        with arcpy.da.UpdateCursor(os.path.join(myVars['workspace'], myVars['bfCL']), ['Channel', 'CLID']) as cursor:
            for row in cursor:
                row[0] = 'Main'
                row[1] = ct
                ct += 1
                cursor.updateRow(row)

    #  ----------------------------------
    #    calculate reach-level metrics
    #  ----------------------------------

    #  --calculate integrated bankfull and wetted widths--
    bfw = intWidth_fn(os.path.join(myVars['workspace'], myVars['bfPolyShp']), os.path.join(myVars['workspace'], myVars['bfCL']))
    ww = intWidth_fn(os.path.join(myVars['workspace'], myVars['wPolyShp']), os.path.join(myVars['workspace'], myVars['wCL']))
    print '...integrated bankfull width: ' + str(bfw) + ' m...'
    print '...integrated wetted width: ' + str(ww) + ' m...'

    #  --calculate gradient, sinuosity, thalweg ratio--

    #  check thalweg to see if it contains 'Length' field if not add field
    tmp_thalweg = arcpy.CopyFeatures_management(os.path.join(myVars['workspace'], myVars['thalwegShp']), 'in_memory/tmp_thalweg')
    if not 'Length' in [f.name for f in arcpy.ListFields(tmp_thalweg)]:
        arcpy.AddField_management(tmp_thalweg, 'Length', 'DOUBLE')

    #  calculate/re-calculate length field
    with arcpy.da.UpdateCursor(tmp_thalweg, ['SHAPE@LENGTH', 'Length']) as cursor:
        for row in cursor:
            row[1] = round(row[0], 3)
            cursor.updateRow(row)

    #  create feature layer for 'Main' thalweg
    arcpy.MakeFeatureLayer_management(tmp_thalweg, 'thalweg_lyr', """ "ThalwegTyp" = 'Main' """)

    #  get 'Main' thalweg length
    maxLength = float([row[0] for row in arcpy.da.SearchCursor('thalweg_lyr', ("Length"))][0])

    #  convert thalweg ends to points
    thalweg_pts = arcpy.FeatureVerticesToPoints_management('thalweg_lyr', 'in_memory/thalweg_pts', "BOTH_ENDS")

    #  calculate straight line distance between thalweg end points
    arcpy.PointDistance_analysis(thalweg_pts, thalweg_pts, 'tbl_thalweg_dist.dbf')
    straightLength = round(arcpy.SearchCursor('tbl_thalweg_dist.dbf', "", "", "", 'DISTANCE' + " D").next().getValue('DISTANCE'), 3)

    #  extract demZ values for each thalweg end point
    ExtractMultiValuesToPoints(thalweg_pts, [[dem, 'demZ']])
    maxZ = round(arcpy.SearchCursor(thalweg_pts, "", "", "", 'demZ' + " D").next().getValue('demZ'), 3)
    minZ = round(arcpy.SearchCursor(thalweg_pts, "", "", "", 'demZ' + " A").next().getValue('demZ'), 3)

    #  sum lengths of all thalwegs in thalweg shp
    totalLength = sum((row[0] for row in arcpy.da.SearchCursor(tmp_thalweg, ['Length'])))

    #  calculate gradient,sinuosity, and thalweg ratio
    gradient = round(((maxZ - minZ) / maxLength) * 100, 3)
    sinuosity = round(maxLength / straightLength, 3)
    thalwegRatio = round(totalLength / maxLength, 3)

    print '...reach gradient: ' + str(gradient) + ' percent...'
    print '...reach sinuosity: ' + str(sinuosity) + '...'
    print '...thalweg ratio: ' + str(thalwegRatio) + '...'

    #  -----------------------------
    #    tier 2 functions
    #  -----------------------------

    #  --tier 2 raster to polygon function--

    #  takes each form raster, converts to polygon, adds/populates fields
    #  filters by area, and merges into single shapefile


    def ras2poly_fn(Mound, Plane, Bowl, Trough, Saddle, Wall, **kwargs):
        shpList = []
        formDict = locals()
        formDict.update(kwargs)
        for key, value in formDict.iteritems():
            if key in ['Mound', 'Plane', 'Bowl', 'Trough', 'Saddle', 'Wall', 'MoundPlane', 'TroughBowl']:
                if int(arcpy.GetRasterProperties_management(value, "ALLNODATA").getOutput(0)) < 1:
                    tmp_fn = 'in_memory/' + str(key) + '_raw'
                    arcpy.RasterToPolygon_conversion(value, tmp_fn, 'NO_SIMPLIFY', 'VALUE')
                    arcpy.AddField_management(tmp_fn, 'ValleyUnit', 'TEXT', '', '', 20)
                    arcpy.AddField_management(tmp_fn, 'UnitShape', 'TEXT', '', '', 15)
                    arcpy.AddField_management(tmp_fn, 'UnitForm', 'TEXT', '', '', 20)
                    with arcpy.da.UpdateCursor(tmp_fn, ['ValleyUnit', 'UnitShape', 'UnitForm']) as cursor:
                        for row in cursor:
                            row[0] = 'In-Channel'
                            row[2] = str(key)
                            if row[2] == 'Plane':
                                row[1] = 'Planar'
                            elif row[2] == 'Mound':
                                row[1] = 'Convexity'
                            elif row[2] == 'Saddle':
                                row[1] = 'Convexity'
                            elif row[2] == 'Wall':
                                row[1] = 'Planar'
                            elif row[2] == 'Bowl':
                                row[1] = 'Concavity'
                            elif row[2] == 'MoundPlane':
                                row[1] = 'Convexity'
                                row[2] = 'Mound Transition'
                            elif row[2] == 'TroughBowl':
                                row[1] = 'Concavity'
                                row[2] = 'Bowl Transition'
                            else:
                                row[1] = 'Planar'
                            cursor.updateRow(row)
                    shp_fn = 'in_memory/' + str(key)
                    arcpy.Dissolve_management(tmp_fn, shp_fn, ['ValleyUnit', 'UnitShape', 'UnitForm'], '', 'SINGLE_PART', 'UNSPLIT_LINES')
                    shpList.append(shp_fn)

        #  merge all forms except saddles and walls (we want to 'stamp' these on top)
        mergeList = [i for i in shpList if i not in ('in_memory/Saddle', 'in_memory/Wall')]
        units_merge = arcpy.Merge_management(mergeList, 'in_memory/units_merge')

        #  update merged units with saddles (if classified) and walls
        if 'in_memory/Saddle' in shpList:
            units_update = arcpy.Update_analysis(units_merge, 'in_memory/Saddle', 'in_memory/units_update')
            units_update2 = arcpy.Update_analysis('in_memory/units_update', 'in_memory/Wall', 'in_memory/units_update2')
            units_sp = arcpy.MultipartToSinglepart_management(units_update2, 'in_memory/units_sp')
        else:
            units_update = arcpy.Update_analysis(units_merge, 'in_memory/Wall', 'in_memory/units_update2')
            units_sp = arcpy.MultipartToSinglepart_management(units_update, 'in_memory/units_sp')

        #  add and calculate area field
        arcpy.AddField_management(units_sp, 'Area', 'DOUBLE')
        with arcpy.da.UpdateCursor(units_sp, ['SHAPE@AREA', 'Area']) as cursor:
            for row in cursor:
                row[1] = row[0]
                cursor.updateRow(row)

        #  filter out tiny units (area < 0.1 * bfw) by merging with unit that shares longest border  #ToDo: Ask NK/JW if we want to use the oonfig area thresh here instead
        #  run 2x
        units_sp_lyr = arcpy.MakeFeatureLayer_management(units_sp, 'units_sp_lyr')
        arcpy.SelectLayerByAttribute_management(units_sp_lyr, 'NEW_SELECTION', """ ("UnitForm" IN ('Bowl', 'Trough', 'Plane', 'Mound', 'Saddle', 'Wall') AND  "Area" < """ + str(0.1 * bfw) + """) OR ("UnitForm" IN ('Bowl Transition', 'Mound Transition') AND "Area" <= 0.1) """)
        units_elim = arcpy.Eliminate_management(units_sp_lyr, 'in_memory/units_elim', "LENGTH")
        units_elim_lyr = arcpy.MakeFeatureLayer_management(units_elim, 'units_elim_lyr')
        arcpy.SelectLayerByAttribute_management(units_elim_lyr, 'NEW_SELECTION', """ ("UnitForm" IN ('Bowl', 'Trough', 'Plane', 'Mound', 'Saddle', 'Wall') AND  "Area" < """ + str(0.1 * bfw) + """) OR ("UnitForm" IN ('Bowl Transition', 'Mound Transition') AND "Area" <= 0.1) """)
        tmp_units = arcpy.Eliminate_management(units_elim_lyr, 'in_memory/tmp_units', "LENGTH")

        #  create form and unit id fields and update area field
        arcpy.AddField_management(tmp_units, 'FormID', 'SHORT')
        arcpy.AddField_management(tmp_units, 'UnitID', 'SHORT')
        ct = 1
        with arcpy.da.UpdateCursor(tmp_units, ['FormID', 'SHAPE@AREA', 'Area', 'UnitID']) as cursor:
            for row in cursor:
                row[0] = ct
                row[2] = row[1]
                row[3] = row[0]
                ct += 1
                cursor.updateRow(row)

        #  remove unnecessary fields
        fields = arcpy.ListFields(tmp_units)
        keep = ['ValleyUnit', 'UnitShape', 'UnitForm', 'Area', 'FormID', 'UnitID']
        drop = []
        for field in fields:
            if not field.required and field.name not in keep and field.type <> 'Geometry':
                drop.append(field.name)
        if len(drop) > 0:
            arcpy.DeleteField_management(tmp_units, drop)

        #  save tier 2 output
        if 'in_memory/MoundPlane' in shpList:
            arcpy.CopyFeatures_management(tmp_units, os.path.join(outpath, 'Tier2_InChannel.shp'))
        else:
            arcpy.CopyFeatures_management(tmp_units, os.path.join(outpath, 'Tier2_InChannel_Discrete.shp'))

        #  remove temporary form sps
        shpList.extend([tmp_units])
        for shp in shpList:
            arcpy.Delete_management(shp)

    #  ---------------------------------
    #  tier 2 evidence layers
    #  ---------------------------------

    print '...deriving evidence layers...'

    #  --mean dem--
    if not os.path.exists(os.path.join(evpath, os.path.splitext(os.path.basename(os.path.join(myVars['workspace'], myVars['inDEM'])))[0] + '_mean.tif')):
        neigh = NbrRectangle(bfw * 0.1, bfw * 0.1, 'MAP')  # set neighborhood size
        meanDEM = FocalStatistics(dem, neigh, 'MEAN', 'DATA')  # calculate mean z
        outMeanDEM = ExtractByMask(meanDEM, dem)  # clip focal result to dem
        outMeanDEM.save(os.path.join(evpath, os.path.splitext(os.path.basename(os.path.join(myVars['workspace'], myVars['inDEM'])))[0] + '_mean.tif'))  # save output
    else:
        outMeanDEM = Raster(os.path.join(evpath, os.path.splitext(os.path.basename(os.path.join(myVars['workspace'], myVars['inDEM'])))[0] + '_mean.tif'))

    #  --in channel mean dem--
    if not os.path.exists(os.path.join(evpath, 'inCh_' + os.path.basename(os.path.join(myVars['workspace'], myVars['inDEM'])))):
        inCh = SetNull(bf, 1, '"VALUE" = 0') #  set cells outside the bankfull channel to null
        inChDEM = inCh * outMeanDEM #  multiply be mean (smoothed) dem
        inChDEM.save(os.path.join(evpath, 'inCh_' + os.path.basename(os.path.join(myVars['workspace'], myVars['inDEM']))))  # save output
    else:
        inChDEM = Raster(os.path.join(evpath, 'inCh_' + os.path.basename(os.path.join(myVars['workspace'], myVars['inDEM']))))

    #  --in channel mean dem slope--
    if not os.path.exists(os.path.join(evpath, 'slope_inCh_' + os.path.basename(os.path.join(myVars['workspace'], myVars['inDEM'])))):
        inChDEMSlope = Slope(inChDEM, 'DEGREE') # calculate slope (in degrees) for in-channel portion of the dem
        inChDEMSlope.save(os.path.join(evpath, 'slope_inCh_' + os.path.basename(os.path.join(myVars['workspace'], myVars['inDEM']))))  # save output
    else:
        inChDEMSlope = Raster(os.path.join(evpath, 'slope_inCh_' + os.path.basename(os.path.join(myVars['workspace'], myVars['inDEM']))))

    #  --residual topography--
    if not os.path.exists(os.path.join(evpath, 'resTopo.tif')):
        neigh2 = NbrRectangle(bfw, bfw, 'MAP')  # set neighborhood size
        trendDEM = FocalStatistics(inChDEM, neigh2, 'MEAN', 'DATA')  # calculate mean z for smoothed dem
        resTopo = inChDEM - trendDEM  # calculate difference between in channel dem and the trend dem
        resTopo.save(os.path.join(evpath, 'resTopo.tif')) # save output
    else:
        resTopo = Raster(os.path.join(evpath, 'resTopo.tif'))

    #  --normalized fill--
    if not os.path.exists(os.path.join(evpath, 'resDepth.tif')):
        rFill = Fill(inChDEM) #  fill the in-channel dem
        resDepth = (rFill - inChDEM) #  difference fill and in-channel dem
        resDepth.save(os.path.join(evpath, 'resDepth.tif')) #  save output
    else:
        resDepth = Raster(os.path.join(evpath, 'resDepth.tif'))

    #  --channel margin--
    if not os.path.exists(os.path.join(evpath, 'chMargin.tif')):
        #  remove any water extent polygons < 5% of the total polygon area
        wPolyElim = arcpy.EliminatePolygonPart_management(os.path.join(myVars['workspace'], myVars['wPolyShp']), 'in_memory/wPolyElim', 'PERCENT', '', 5, 'ANY')
        #  erase (exclude) water extent polygon from bankfull polygon
        polyErase = arcpy.Erase_analysis(os.path.join(myVars['workspace'], myVars['bfPolyShp']), wPolyElim, 'in_memory/polyErase', '')
        #  buffer the output by 10% of the integrated wetted width
        polyBuffer = arcpy.Buffer_analysis(polyErase, 'in_memory/polyBuffer', 0.1 * ww, 'FULL')
        #  clip the output to the bankfull polygon
        arcpy.Clip_analysis(polyBuffer, os.path.join(myVars['workspace'], myVars['bfPolyShp']), 'in_memory/chMarginPoly')
        #  convert the output to a raster
        cm_raw = arcpy.PolygonToRaster_conversion('in_memory/chMarginPoly', 'FID', 'in_memory/chMargin_raw', 'CELL_CENTER', 'NONE')
        #  set all cells to value of 1
        cm = Con(cm_raw, 1, "VALUE" >= 0)
        #  save the output
        cm.save(os.path.join(evpath, 'chMargin.tif'))
    else:
        cm = Raster(os.path.join(evpath, 'chMargin.tif'))

    print '...saddle contours...'
    # --saddle contours--
    if myVars['createSaddles'] == 'Yes':
        thalweg_basename = os.path.splitext(os.path.basename(os.path.join(myVars['workspace'], myVars['thalwegShp'])))[0]
        if not os.path.exists(os.path.join(evpath, 'contourNodes_' + thalweg_basename + '.shp')):
            #  create contours
            #
            if bfw < 12.0:
                contours = Contour(outMeanDEM, 'in_memory/contours', 0.1)
            else:
                contours = Contour(outMeanDEM, 'in_memory/contours', 0.2)
            #  b. clean up contours (i.e., fill contour gaps)
            #  clip contour shp to bankfull polygon
            contour_clip = arcpy.Clip_analysis(contours, os.path.join(myVars['workspace'], myVars['bfPolyShp']), 'in_memory/contours_clip')
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
            bankfull_line = arcpy.FeatureToLine_management([os.path.join(myVars['workspace'], myVars['bfPolyShp'])], 'in_memory/bankfull_line')
            contours_bankfull_merge = arcpy.Merge_management([line_lyr, bankfull_line], 'in_memory/contours_bankfull_merge')
            #  create points at contour endpoints
            end_points = arcpy.FeatureVerticesToPoints_management(contours_bankfull_merge, 'in_memory/contours_bankfull_merge_ends', 'BOTH_ENDS')
            #  delete end points that intersect > 1 contour line - only want points that fall on end of a line
            end_points_join = arcpy.SpatialJoin_analysis(end_points, contours_bankfull_merge, 'in_memory/end_points_join', 'JOIN_ONE_TO_ONE', 'KEEP_ALL', '', 'INTERSECT')
            with arcpy.da.UpdateCursor(end_points_join, ['Join_Count']) as cursor:
                for row in cursor:
                    if row[0] > 1:
                        cursor.deleteRow()
            #  find and delete end points that are identical since these are 'false' end point on closed contours
            identical_tbl = arcpy.FindIdentical_management(end_points_join, 'in_memory/identical_tbl', ['Shape'], '', '', 'ONLY_DUPLICATES')
            identical_list = [row[0] for row in arcpy.da.SearchCursor(identical_tbl, ['IN_FID'])]
            oid_fn = arcpy.Describe(end_points_join).OIDFieldName
            with arcpy.da.UpdateCursor(end_points_join, [oid_fn]) as cursor:
                for row in cursor:
                    if row[0] in identical_list:
                        cursor.deleteRow()
            #  assign unique 'endID' field
            arcpy.AddField_management(end_points_join, 'endID', 'SHORT')
            fields = ['endID']
            ct = 1
            with arcpy.da.UpdateCursor(end_points_join, fields) as cursor:
                for row in cursor:
                    row[0] = ct
                    ct += 1
                    cursor.updateRow(row)
            #  find nearest end point to each end point
            arcpy.Near_analysis(end_points_join, end_points_join)
            endDict = {}  # create end point dictionary

            with arcpy.da.SearchCursor(end_points_join, [oid_fn, 'endID']) as cursor:
                for row in cursor:
                    endDict[row[0]] = row[1]
            #  rename/calculate near end id field to logical name
            arcpy.AddField_management(end_points_join, 'nearEndID', 'SHORT')
            arcpy.AddField_management(end_points_join, 'nearDist', 'DOUBLE')
            arcpy.AddField_management(end_points_join, 'strContour', 'TEXT')
            with arcpy.da.UpdateCursor(end_points_join, ['NEAR_FID', 'nearEndID', 'Contour', 'strContour', 'NEAR_DIST', 'nearDist']) as cursor:
                for row in cursor:
                    row[1] = endDict[row[0]]
                    row[3] = str(row[2])
                    row[5] = row[4]
                    cursor.updateRow(row)
            # remove unnecessary fields from previous join operations
            fields = arcpy.ListFields(end_points_join)
            keep = ['endID', 'Contour', 'nearEndID', 'nearDist', 'strContour']
            drop = []
            for field in fields:
                if not field.required and field.name not in keep and field.type <> 'Geometry':
                    drop.append(field.name)
            arcpy.DeleteField_management(end_points_join, drop)
            #  make end point feature layer for selection operations
            end_points_lyr = arcpy.MakeFeatureLayer_management(end_points_join, 'end_points_lyr')
            #  group end point pairs that fall on contour gaps
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
                        elif row[5] > 0.25 * bfw: # ToDo: May want to expose this threshold or set as some multiple of cell size
                            pass
                        else:
                            arcpy.CalculateField_management(end_points_lyr, 'endIDGroup', groupIndex, 'PYTHON_9.3')
                            groupIndex += 1
            #  delete end points that aren't part of group (i.e., that weren't on contour gap)
            with arcpy.da.UpdateCursor(end_points_join, ['endIDGroup']) as cursor:
                for row in cursor:
                    if row[0] <= 0.0:
                        cursor.deleteRow()
            #  create line connecting each end point pair
            gap_lines = arcpy.PointsToLine_management(end_points_join, 'in_memory/gap_lines', 'endIDGroup')
            #  merge contour gap lines with contours
            contours_gap_merge = arcpy.Merge_management([line_lyr, gap_lines], 'in_memory/contours_gap_merge')
            #  dissolve all lines that are touching into single line
            contours_repaired = arcpy.Dissolve_management(contours_gap_merge, 'in_memory/contours_repaired', '', '', '', 'UNSPLIT_LINES')
            arcpy.CopyFeatures_management(contours_repaired, os.path.join(evpath, 'DEM_Contours.shp'))
            #  c. merge repaired lines with bankfull line
            contours_bankfull_merge2 = arcpy.Merge_management([contours_repaired, bankfull_line], 'in_memory/contours_bankfull_merge2')
            #  d. close contour lines by extending to bankfull line
            arcpy.ExtendLine_edit(contours_bankfull_merge2, "1.0 Meters", "EXTENSION")
            #  e. add unique contour line id field 'ContourID'
            arcpy.AddField_management(contours_bankfull_merge2, 'ContourID', 'SHORT')
            ct = 1
            with arcpy.da.UpdateCursor(contours_bankfull_merge2, ['ContourID']) as cursor:
                for row in cursor:
                    row[0] = ct
                    ct += 1
                    cursor.updateRow(row)
            #  f. convert contour lines to polygon and clip to bankfull polygon
            contour_poly_raw = arcpy.FeatureToPolygon_management(contours_bankfull_merge2, 'in_memory/raw_contour_poly')
            contour_poly_clip = arcpy.Clip_analysis(contour_poly_raw, os.path.join(myVars['workspace'], myVars['bfPolyShp']), 'in_memory/contour_polygons_clip')

            #  g. create nodes at contour [line] - thalweg intersection
            arcpy.CopyFeatures_management(os.path.join(myVars['workspace'], myVars['thalwegShp']), 'in_memory/thalweg')
            contour_nodes_mpart = arcpy.Intersect_analysis(['in_memory/thalweg', contours_bankfull_merge2], 'in_memory/contour_nodes_mpart', 'NO_FID', '', 'POINT')
            contour_nodes = arcpy.MultipartToSinglepart_management(contour_nodes_mpart, 'in_memory/contour_nodes')

            #  h. add unique node id field
            arcpy.AddField_management(contour_nodes, 'NodeID', 'SHORT')
            ct = 1
            with arcpy.da.UpdateCursor(contour_nodes, 'NodeID') as cursor:
                for row in cursor:
                    row[0] = ct
                    ct += 1
                    cursor.updateRow(row)

            #  i. extract dem z values to contour nodes
            ExtractMultiValuesToPoints(contour_nodes, [[outMeanDEM, 'elev']], 'NONE')

            #  j. calculate flowline distance for each contour node
            arcpy.AddField_management('in_memory/thalweg', 'ThID', 'SHORT')
            arcpy.AddField_management('in_memory/thalweg', 'From_', 'DOUBLE')
            arcpy.AddField_management('in_memory/thalweg', 'To_', 'DOUBLE')
            fields = ['SHAPE@LENGTH', 'From_', 'To_', 'ThID']
            ct = 1
            with arcpy.da.UpdateCursor('in_memory/thalweg', fields) as cursor:
                for row in cursor:
                    row[1] = 0.0
                    row[2] = row[0]
                    row[3] = ct
                    ct += 1
                    cursor.updateRow(row)
            arcpy.CreateRoutes_lr('in_memory/thalweg', 'ThID', 'in_memory/thalweg_route', 'TWO_FIELDS', 'From_', 'To_')
            route_tbl = arcpy.LocateFeaturesAlongRoutes_lr(contour_nodes, 'in_memory/thalweg_route', 'ThID', float(desc.meanCellWidth), os.path.join(evpath, 'tbl_Routes.dbf'), 'RID POINT MEAS')
            arcpy.JoinField_management(contour_nodes, 'NodeID', route_tbl, 'NodeID', ['MEAS'])
            arcpy.JoinField_management(contour_nodes, 'NodeID', route_tbl, 'NodeID', ['RID'])
            contour_nodes_join = arcpy.SpatialJoin_analysis(contour_nodes, contours, 'in_memory/contour_nodes_join', 'JOIN_ONE_TO_MANY', 'KEEP_ALL', '', 'INTERSECT')

            #  k. sort contour nodes by flowline distance (in downstream direction)
            contour_nodes_sort = arcpy.Sort_management(contour_nodes_join, 'in_memory/contour_nodes_sort', [['RID', 'DESCENDING'],['MEAS', 'DESCENDING']])
            #  l. re-calculate node id so they are in ascending order starting at upstream boundary
            ct = 1
            with arcpy.da.UpdateCursor(contour_nodes_sort, ['NodeID']) as cursor:
                for row in cursor:
                    row[0] = ct
                    ct += 1
                    cursor.updateRow(row)

            #  m. calculate elevation difference btwn contour nodes in DS direction
            arcpy.AddField_management(contour_nodes_sort, 'adj_elev', 'DOUBLE')
            arcpy.AddField_management(contour_nodes_sort, 'diff_elev', 'DOUBLE')
            arcpy.AddField_management(contour_nodes_sort, 'dist', 'DOUBLE')
            arcpy.AddField_management(contour_nodes_sort, 'riff_pair', 'SHORT')
            arcpy.AddField_management(contour_nodes_sort, 'riff_dir', 'TEXT', '', '', 5)

            #idList = [row[0] for row in arcpy.da.SearchCursor(contour_nodes_sort, ['RID'])]
            ridList = set(row[0] for row in arcpy.da.SearchCursor(contour_nodes_sort, ['RID']))

            for rid in ridList:
                contour_nodes_lyr = arcpy.MakeFeatureLayer_management(contour_nodes_sort, 'contour_nodes_sort_lyr')
                arcpy.SelectLayerByAttribute_management(contour_nodes_lyr, "NEW_SELECTION", "RID = %s" % str(rid))
                fields = ['elev', 'adj_elev', 'diff_elev', 'riff_pair', 'riff_dir', 'ContourID', 'MEAS', 'dist']
                distList = []
                elevList = []
                contourList = []
                index = 0
                with arcpy.da.SearchCursor(contour_nodes_lyr, fields) as cursor:
                    for row in cursor:
                        distList.append(row[6])
                        elevList.append(row[0])
                        contourList.append(row[5])
                with arcpy.da.UpdateCursor(contour_nodes_lyr, fields) as cursor:
                    for row in cursor:
                        if index + 1 < len(elevList):
                            row[1] = elevList[index + 1]
                            row[2] = float(row[1] - row[0])
                            row[7] = row[6] - distList[index + 1]
                        if index + 1 == len(elevList):
                            row[1] = -9999
                            row[2] = -9999
                            row[7] = -9999
                        index += 1
                        cursor.updateRow(row)

                with arcpy.da.UpdateCursor(contour_nodes_lyr, fields) as cursor:
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
                with arcpy.da.SearchCursor(contour_nodes_lyr, fields) as cursor:
                    for row in cursor:
                        elevDiffList.append(row[2])
                with arcpy.da.UpdateCursor(contour_nodes_lyr, fields) as cursor:
                    for row in cursor:
                        if index + 1 < len(elevDiffList) and index > 1:
                            if row[5] != contourList[index + 1]:
                                if row[2] < 0.05 and row[2] > -0.05 and elevDiffList[index + 1] < 0 and elevDiffList[index - 1] > 0 and elevDiffList[index - 2] > 0 and row[7] < (1.5 * bfw):
                                    row[4] = 'US'
                                    row[3] = index
                            if row[5] != contourList[index - 1]:
                                if row[2] < 0 and elevDiffList[index - 1] > -0.05 and elevDiffList[index - 1] < 0.05 and elevDiffList[index - 2] > 0 and elevDiffList[index - 3] > 0 and str(nodeDirList[index - 1]) == 'US':
                                    row[4] = 'DS'
                                    row[3] = index - 1
                        nodeDirList.append(row[4])
                        if index + 1 == len(elevDiffList) and str(nodeDirList[index - 1]) == 'US':
                            row[4] = 'DS'
                            row[3] = index - 1
                        index += 1
                        cursor.updateRow(row)

            arcpy.SelectLayerByAttribute_management(contour_nodes_lyr, "CLEAR_SELECTION")
            #  o. snap contour nodes to contour polygon edge in case there was a slight shift in position during line to polygon conversion
            arcpy.Snap_edit(contour_nodes_sort, [[contour_poly_clip, "EDGE", "0.1 Meters"]])

            # remove unnecessary fields
            fields = arcpy.ListFields(contour_nodes_sort)
            keep = ['RID', 'Channel', 'ThalwegTyp', 'NodeID', 'elev', 'adj_elev', 'diff_elev', 'riff_pair', 'riff_dir', 'dist']
            drop = []
            for field in fields:
                if not field.required and field.name not in keep and field.type <> 'Geometry':
                    drop.append(field.name)
            if len(drop) > 0:
                arcpy.DeleteField_management(contour_nodes_sort, drop)

            #  p. save contour polygons and contour nodes to evidence layer folder
            os.path.join(evpath, 'contourNodes_' + thalweg_basename + '.shp')
            arcpy.CopyFeatures_management(contour_nodes_sort, os.path.join(evpath, 'contourNodes_' + thalweg_basename + '.shp'))
            arcpy.CopyFeatures_management(contour_poly_clip, os.path.join(evpath, 'contourPolygons_' + thalweg_basename + '.shp'))

        else:
            contour_nodes_sort = os.path.join(evpath, 'contourNodes_' + thalweg_basename + '.shp')
            contour_poly_clip = os.path.join(evpath, 'contourPolygons_' + thalweg_basename + '.shp')

    # ---------------------------------
    #  tier 2 classification
    #  ---------------------------------

    print '...classifying Tier 2 shapes and forms...'

    arr = arcpy.RasterToNumPyArray(resTopo) #  convert residual topo raster to numpy array
    NDV = arcpy.Describe(resTopo).noDataValue #  get residual topo raster no data value
    arr[arr == NDV] = numpy.nan  # set array no data to raster no data value
    arr = arr[~numpy.isnan(arr)]  # remove no data from array

    #  calculate residual topography quantiles to use in thresholding
    #  transition forms
    mound_lb = numpy.percentile(arr[arr > 0], myVars['moundPercentile'][0])
    moundtrans_ub = numpy.percentile(arr[arr > 0], myVars['moundTransitionPercentile'][1])
    moundtrans_lb = numpy.percentile(arr[arr > 0], myVars['moundTransitionPercentile'][0])
    plane_ub = numpy.percentile(arr[arr > 0], myVars['planePercentile'][1])
    plane_lb = numpy.percentile(numpy.negative(arr[arr <= 0]), myVars['planePercentile'][0]*-1)
    trough_lb = numpy.percentile(numpy.negative(arr[arr <= 0]), myVars['troughPercentile'][0]*-1)
    trough_ub = numpy.percentile(numpy.negative(arr[arr <= 0]), myVars['troughPercentile'][1]*-1)
    bowl_lb = numpy.percentile(numpy.negative(arr[arr <= 0]), myVars['bowlPercentile'][0]*-1)

    mound = SetNull(resTopo, 1, '"VALUE" < ' + str(mound_lb))
    moundtrans = SetNull(resTopo, 1, '"VALUE" >= ' + str(moundtrans_ub)) * SetNull(resTopo, 1, '"VALUE" < ' + str(moundtrans_lb))
    plane = SetNull(resTopo, 1, '"VALUE" >= ' + str(plane_ub)) * SetNull(resTopo, 1, '"VALUE" <= -' + str(plane_lb))
    bowl = SetNull(resTopo, 1, '"VALUE" >= -' + str(bowl_lb)) * SetNull(resDepth, 1, '"VALUE" <= 0')
    trough = SetNull(resTopo, 1, '"VALUE" > -' + str(trough_lb)) * SetNull(resTopo, 1, '"VALUE" < -' + str(trough_ub))
    bowltrans = SetNull(resTopo, 1, '"VALUE" >= -' + str(bowl_lb)) * SetNull(resDepth, 1, '"VALUE" > 0')

    #  discrete forms
    perDiff = (myVars['moundPercentile'][0] - myVars['planePercentile'][1]) / 2.0
    mound_discrete_lb = numpy.percentile(arr[arr > 0], myVars['moundPercentile'][0] - perDiff)
    plane_discrete_ub = numpy.percentile(arr[arr > 0], myVars['planePercentile'][1] + perDiff)

    mound_discrete = SetNull(resTopo, 1, '"VALUE" < ' + str(mound_discrete_lb))
    plane_discrete = SetNull(resTopo, 1, '"VALUE" >= ' + str(plane_discrete_ub)) * SetNull(resTopo, 1, '"VALUE" <= -' + str(plane_lb))
    bowl_discrete = SetNull(resTopo, 1, '"VALUE" > -' + str(bowl_lb)) * SetNull(resDepth, 1, '"VALUE" <= 0')
    trough_discrete = Con(IsNull(bowl_discrete), 1) * SetNull(resTopo, 1, '"VALUE" > -' + str(trough_lb))

    #  saddles
    #  a. select contour polgons that intersect riffle contour nodes
    if myVars['createSaddles'] == 'Yes':
        arcpy.MakeFeatureLayer_management(contour_nodes_sort, 'downstream_lyr', """ "riff_dir" = 'DS' """)
        arcpy.MakeFeatureLayer_management(contour_nodes_sort, 'upstream_lyr', """ "riff_dir" = 'US' """)
        arcpy.MakeFeatureLayer_management(contour_poly_clip, 'contour_poly_lyr')
        arcpy.SelectLayerByLocation_management('contour_poly_lyr', 'INTERSECT', 'downstream_lyr', '', 'NEW_SELECTION')
        arcpy.SelectLayerByLocation_management('contour_poly_lyr', 'INTERSECT', 'upstream_lyr', '', 'SUBSET_SELECTION')
        riff_contour_raw = arcpy.CopyFeatures_management('contour_poly_lyr', 'in_memory/riffle_contour_raw')

        if int(arcpy.GetCount_management(riff_contour_raw).getOutput(0)) > 0:
            #  b. add unique riffle id field
            arcpy.AddField_management(riff_contour_raw, 'RiffleID', 'SHORT')
            ct = 1
            with arcpy.da.UpdateCursor(riff_contour_raw, ['RiffleID']) as cursor:
                for row in cursor:
                    row[0] = ct
                    ct += 1
                    cursor.updateRow(row)

            #  c. clip thalweg to riffle contour
            thalweg_clip = arcpy.Intersect_analysis([os.path.join(myVars['workspace'], myVars['thalwegShp']), riff_contour_raw], 'in_memory/thalweg_clip', 'ALL', '', 'LINE')
            thalweg_clip_sp = arcpy.MultipartToSinglepart_management(thalweg_clip, 'in_memory/thalweg_clip_sp')
            arcpy.MakeFeatureLayer_management(thalweg_clip_sp, 'thalewg_lyr')
            arcpy.SelectLayerByLocation_management('thalewg_lyr', 'INTERSECT', 'downstream_lyr', '', 'NEW_SELECTION')
            arcpy.SelectLayerByLocation_management('thalewg_lyr', 'INTERSECT', 'upstream_lyr', '', 'SUBSET_SELECTION')
            if int(arcpy.GetCount_management('thalewg_lyr').getOutput(0)) > 0:
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
                buffer_lyr = arcpy.MakeFeatureLayer_management(thalweg_centroid_buffer, 'thalweg_centroid_buffer_lyr')
                riff_lyr = arcpy.MakeFeatureLayer_management(riff_contour_raw, 'riff_lyr')

                shpList = []
                ct = 1
                with arcpy.da.SearchCursor(thalweg_centroid, ['RiffleID', 'SHAPE@']) as cursor:
                    for row in cursor:
                        tmp_fn = 'in_memory/tmp_' + str(ct)
                        arcpy.SelectLayerByLocation_management(riff_lyr, 'INTERSECT', row[1], '', 'NEW_SELECTION')
                        arcpy.SelectLayerByAttribute_management(buffer_lyr, "NEW_SELECTION", "RiffleID = %s" % row[0])
                        arcpy.Clip_analysis(riff_lyr, buffer_lyr, tmp_fn)
                        shpList.append(tmp_fn)
                        ct += 1

                riff_contour_merge = arcpy.Merge_management(shpList, 'in_memory/riff_contour_merge')
                riff_contour_clip = arcpy.Dissolve_management(riff_contour_merge, 'in_memory/riff_contour_clip', ["RiffleID"], '', 'SINGLE_PART')

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

                #  j. remove saddles that are less than the saddle area threshold
                with arcpy.da.UpdateCursor(riff_poly, 'SHAPE@AREA') as cursor:
                    for row in cursor:
                        if row[0] < (myVars['saddleAreaThresh'] * bfw):
                            cursor.deleteRow()

                #  k. select features that contain the thalweg centroid
                arcpy.MakeFeatureLayer_management(riff_poly, 'riff_poly_lyr')
                arcpy.SelectLayerByLocation_management('riff_poly_lyr', 'INTERSECT', thalweg_centroid, '', 'NEW_SELECTION')
                if int(arcpy.GetCount_management('riff_poly_lyr').getOutput(0)) > 0:
                    saddle_raw = arcpy.PolygonToRaster_conversion('riff_poly_lyr', 'RiffleID', 'in_memory/saddles_raw', 'CELL_CENTER', '', desc.meanCellWidth)
                    saddle = Con(saddle_raw, 1, "VALUE" >= 0)
                else:
                    saddle = SetNull(mound, 1, '"VALUE" >= 0')
            else:
                saddle = SetNull(mound, 1, '"VALUE" >= 0')
        else:
            # oid_fieldname = arcpy.Describe(riff_contour_raw).OIDFieldName
            # saddle_raw = arcpy.PolygonToRaster_conversion(riff_contour_raw, oid_fieldname, 'in_memory/saddles_raw', 'CELL_CENTER', '', 0.1)
            # saddle = Con(saddle_raw, 1, "VALUE" >= 0)
            saddle = SetNull(mound, 1, '"VALUE" >= 0')
    else:
        saddle = SetNull(mound, 1, '"VALUE" >= 0')

    #  walls/banks
    #  a. calculate bank slope threshold
    if myVars['wallSlopeTh'] == '':
        slopeMeanResult = arcpy.GetRasterProperties_management(inChDEMSlope, 'MEAN')
        slopeMean = float(slopeMeanResult.getOutput(0))
        slopeSTDResult = arcpy.GetRasterProperties_management(inChDEMSlope, 'STD')
        slopeSTD = float(slopeSTDResult.getOutput(0))
        slopeTh = slopeMean + slopeSTD
        print '...wall slope threshold: ' + str(slopeTh) + ' degrees...'
    else:
        slopeTh = myVars['wallSlopeTh']

    #  b. segregate walls
    #cmSlope = cm *inChDEMSlope * SetNull(resTopo, 1, '"VALUE" < 0')  # isolate slope values for channel margin convexities
    cmSlope = cm * inChDEMSlope * mound_discrete  # isolate slope values for channel margin convexities
    wall = SetNull(cmSlope, 1, '"VALUE" <= ' + str(slopeTh))  # apply slope threshold
    #print '!! running non trans function !!' # todo: delete
    ras2poly_fn(mound_discrete, plane_discrete, bowl_discrete, trough_discrete, saddle, wall)
    #print '!! running trans function !!' # todo: delete
    ras2poly_fn(mound, plane, bowl, trough, saddle, wall, MoundPlane = moundtrans, TroughBowl = bowltrans)
    #print 'removing tier 2 temp files' # todo: delete
    # # ----------------------------------------------------------
    # # Remove temporary files
    #
    # print '...removing intermediary surfaces...'
    #
    # for root, dirs, files in os.walk(arcpy.env.workspace):
    #     for f in fnmatch.filter(files, 'tmp_*'):
    #         os.remove(os.path.join(root, f))
    #arcpy.Delete_management(os.path.join(evpath, 'tbl_Routes.dbf'))
    arcpy.Delete_management("in_memory")
    arcpy.Delete_management(tmp_dir)
    arcpy.Delete_management(os.path.join(evpath, 'tbl_Routes.dbf'))

    #  Save config file settings to output folder
    f = open("./config.py", "r")
    copy = open(os.path.join(outpath, "configSettings.txt"), "w")
    for line in f:
        copy.write(line)
    f.close()
    copy.write('\n' + 'Integrated bankfull width: ' + str(bfw) + ' m' + '\n')
    copy.write('Integrated wetted width: ' + str(ww) + ' m' + '\n')
    copy.write('Wall slope threshold: ' + str(slopeTh) + ' degrees' + '\n')
    copy.write('Reach sinuosity: ' + str(sinuosity) + '\n')
    copy.write('Reach gradient: ' + str(gradient) + ' percent' + '\n')
    copy.write('Thalweg ratio: ' + str(thalwegRatio) + '\n')
    copy.close()

    print '...done with Tier 2 classification.'

def tier3(**myVars):

    print 'Starting Tier 3 geomorphic unit classification...'

    #  create temporary workspace
    tmp_dir = tempfile.mkdtemp()

    #  environment settings
    arcpy.env.workspace = tmp_dir # set workspace to pf
    arcpy.env.overwriteOutput = True  # set to overwrite output

    #  set output paths
    evpath = os.path.join(myVars['workspace'], 'EvidenceLayers')
    if myVars['runFolderName'] != 'Default' and myVars['runFolderName'] != '':
        outpath = os.path.join(myVars['workspace'], 'Output', myVars['runFolderName'])
    else:
        runFolders = fnmatch.filter(next(os.walk(os.path.join(myVars['workspace'], 'Output')))[1], 'Run_*')
        runNum = int(max([i.split('_', 1)[1] for i in runFolders]))
        outpath = os.path.join(myVars['workspace'], 'Output', 'Run_%03d' % runNum)

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
    bf = Raster(os.path.join(myVars['workspace'], 'EvidenceLayers/bfCh.tif'))  # created in 'tier1' module
    dem = Raster(os.path.join(evpath, os.path.splitext(os.path.basename(os.path.join(myVars['workspace'], myVars['inDEM'])))[0] + '_mean.tif'))

    #  set raster environment settings
    desc = arcpy.Describe(dem)
    arcpy.env.extent = desc.Extent
    arcpy.env.outputCoordinateSystem = desc.SpatialReference
    arcpy.env.cellSize = desc.meanCellWidth


    #  ----------------------------------
    #    calculate reach-level metrics
    #  ----------------------------------

    #  --calculate integrated bankfull and wetted widths--
    bfw = intWidth_fn(os.path.join(myVars['workspace'], myVars['bfPolyShp']), os.path.join(myVars['workspace'], myVars['bfCL']))

    #  --calculate gradient, sinuosity, thalweg ratio--

    #  check thalweg to see if it contains 'Length' field if not add field
    tmp_thalweg = arcpy.CopyFeatures_management(os.path.join(myVars['workspace'], myVars['thalwegShp']), 'in_memory/tmp_thalweg')
    if not 'Length' in [f.name for f in arcpy.ListFields(tmp_thalweg)]:
        arcpy.AddField_management(tmp_thalweg, 'Length', 'DOUBLE')

    #  calculate/re-calculate length field
    with arcpy.da.UpdateCursor(tmp_thalweg, ['SHAPE@LENGTH', 'Length']) as cursor:
        for row in cursor:
            row[1] = round(row[0], 3)
            cursor.updateRow(row)

    #  create feature layer for 'Main' thalweg
    arcpy.MakeFeatureLayer_management(tmp_thalweg, 'thalweg_lyr', """ "ThalwegTyp" = 'Main' """)

    #  get 'Main' thalweg length
    maxLength = float([row[0] for row in arcpy.da.SearchCursor('thalweg_lyr', ("Length"))][0])

    #  convert thalweg ends to points
    thalweg_pts = arcpy.FeatureVerticesToPoints_management('thalweg_lyr', 'in_memory/thalweg_pts', "BOTH_ENDS")

    #  calculate straight line distance between thalweg end points
    arcpy.PointDistance_analysis(thalweg_pts, thalweg_pts, 'tbl_thalweg_dist.dbf')
    straightLength = round(arcpy.SearchCursor('tbl_thalweg_dist.dbf', "", "", "", 'DISTANCE' + " D").next().getValue('DISTANCE'), 3)

    #  extract demZ values for each thalweg end point
    ExtractMultiValuesToPoints(thalweg_pts, [[dem, 'demZ']])
    maxZ = round(arcpy.SearchCursor(thalweg_pts, "", "", "", 'demZ' + " D").next().getValue('demZ'), 3)
    minZ = round(arcpy.SearchCursor(thalweg_pts, "", "", "", 'demZ' + " A").next().getValue('demZ'), 3)

    #  sum lengths of all thalwegs in thalweg shp
    totalLength = sum((row[0] for row in arcpy.da.SearchCursor(tmp_thalweg, ['Length'])))

    #  calculate gradient,sinuosity, and thalweg ratio
    gradient = round(((maxZ - minZ) / maxLength) * 100, 3)
    sinuosity = round(maxLength / straightLength, 3)
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
        bfLine = arcpy.FeatureToLine_management(os.path.join(myVars['workspace'], myVars['bfPolyShp']), 'in_memory/tmp_bfLine')
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
        arcpy.SelectLayerByLocation_management('tmp_bfPtsZ_lyr', 'WITHIN_A_DISTANCE', os.path.join(myVars['workspace'], myVars['wPolyShp']), str(desc.meanCellWidth) + ' Meters')
        if int(arcpy.GetCount_management('tmp_bfPtsZ_lyr').getOutput(0)) > 0:
            arcpy.DeleteFeatures_management('tmp_bfPtsZ_lyr')

        #  d. create bankfull elevation raster
        bfe_tin = arcpy.CreateTin_3d('bfe_tin', desc.SpatialReference, [[bfPtsZ, 'demZ', 'masspoints'], [os.path.join(myVars['workspace'], myVars['bfPolyShp']), '<None>', 'hardclip']])
        tmp_bfe = arcpy.TinRaster_3d(bfe_tin, 'in_memory/bfe_ras', data_type = 'FLOAT', method = 'NATURAL_NEIGHBORS', sample_distance = "CELLSIZE 0.1")

        #  e. create bfe slope raster
        bfSlope = Slope(tmp_bfe, 'DEGREE')
        bfSlope.save(os.path.join(evpath, 'bfSlope.tif'))

        #  f. calculate mean bfe slope over bfw neighborhood
        neighborhood = NbrRectangle(bfw, bfw, 'MAP')
        slope_focal = FocalStatistics(bfSlope, neighborhood, 'MEAN')

        #  g. clip to bankfull polygon
        bfSlope_Smooth = ExtractByMask(slope_focal, os.path.join(myVars['workspace'], myVars['bfPolyShp']))

        #  h. save output
        bfSlope_Smooth.save(os.path.join(evpath, 'bfSlope_Smooth.tif'))

        #  i. delete intermediate fcs
        fcs = [bfPts, bfLine, bfPtsZ]
        for fc in fcs:
            arcpy.Delete_management(fc)
    else:
        bfSlope = Raster(os.path.join(evpath, 'bfSlope.tif'))
        bfSlope_Smooth = Raster(os.path.join(evpath, 'bfSlope_Smooth.tif'))

    #  --bf slope smoothed slope category thresholds--
    # Very Low < 0.6 deg
    # Low = 0.6-2.3 deg
    # Moderate = 2.3-4.3 deg
    # High = 4.3-11.3 deg
    # Very High > 11.3 deg

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
        bedSlopeSD_raw = FocalStatistics(Raster(os.path.join(evpath, 'slope_inCh_' + os.path.basename(os.path.join(myVars['workspace'], myVars['inDEM'])))), neighborhood, 'STD')
        bedSlopeSD = ExtractByMask(bedSlopeSD_raw, os.path.join(myVars['workspace'], myVars['bfPolyShp']))

        #  h. save output
        bedSlopeSD.save(os.path.join(evpath, 'bedSlopeSD.tif'))
        bedSlopeSD_Cat_ras = Con(bedSlopeSD < 5.5, 1, 2)
        bedSlopeSD_Cat = arcpy.RasterToPolygon_conversion(bedSlopeSD_Cat_ras, os.path.join(evpath, 'bedSlopeSD_Cat.shp'), 'NO_SIMPLIFY', 'VALUE')
        arcpy.MakeFeatureLayer_management(bedSlopeSD_Cat, 'bedSlope_lyr')
    else:
        arcpy.MakeFeatureLayer_management(os.path.join(evpath, 'bedSlopeSD_Cat.shp'), 'bedSlope_lyr')

    #  --channel edge polygon--

    if not os.path.exists(os.path.join(evpath, 'channelEdge.shp')):
        print '...channel edge...'

        # calculate distance from main centerline end points
        bfCL = arcpy.CopyFeatures_management(os.path.join(myVars['workspace'], myVars['bfCL']), 'in_memory/tmp_bfCL')
        bfCL_lyr = arcpy.MakeFeatureLayer_management(bfCL, 'bfCL_lyr', """ "Channel" = 'Main' """)
        bfCL_pts = arcpy.FeatureVerticesToPoints_management(bfCL_lyr, 'in_memory/bfCL_pts', "BOTH_ENDS")
        bfCLDist = EucDistance(bfCL_pts, '', desc.meanCellWidth)

        outCh = Con(bf < 1, 1)
        inCh_buffer = Con(EucDistance(Con(bf > 0, 1), 2 * float(desc.meanCellWidth), desc.meanCellWidth) > 0, 1)
        outChEdgeRas = Con(bfCLDist > (0.5 * bfw), Con(IsNull(outCh), inCh_buffer, outCh), outCh)

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

        arcpy.EliminatePolygonPart_management(os.path.join(myVars['workspace'], myVars['bfPolyShp']), 'in_memory/bfelim', 'AREA', 10*bfw, '', 'CONTAINED_ONLY')
        arcpy.Erase_analysis('in_memory/bfelim', os.path.join(myVars['workspace'], myVars['bfPolyShp']), 'in_memory/tmp_erase')

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
        arcpy.MakeFeatureLayer_management(os.path.join(outpath, 'Tier2_InChannel.shp'), 'forms_lyr')

        edge_forms = arcpy.SpatialJoin_analysis('outChEdge_lyr', 'forms_lyr', 'in_memory/tmp_edge_forms', 'JOIN_ONE_TO_MANY', '', '', 'INTERSECT')
        edge_forms_tbl = arcpy.Frequency_analysis(edge_forms, 'tbl_edge_forms.dbf', ['EdgeID'])
        arcpy.AddField_management(edge_forms_tbl, 'formCount', 'SHORT')
        arcpy.CalculateField_management(edge_forms_tbl, 'formCount', '!FREQUENCY!', 'PYTHON_9.3')
        arcpy.JoinField_management('outChEdge_lyr', 'EdgeID', edge_forms_tbl, 'EdgeID', ['formCount'])

        arcpy.SelectLayerByAttribute_management('forms_lyr', 'NEW_SELECTION', """ "UnitForm" = 'Mound' """)
        edge_mounds = arcpy.SpatialJoin_analysis('outChEdge_lyr', 'forms_lyr', 'in_memory/tmp_edge_mounds', 'JOIN_ONE_TO_MANY', '', '', 'INTERSECT')
        edge_mounds_tbl = arcpy.Frequency_analysis(edge_mounds, 'tbl_edge_mounds.dbf', ['EdgeID'])
        arcpy.AddField_management(edge_mounds_tbl, 'moundCount', 'SHORT')
        arcpy.CalculateField_management(edge_mounds_tbl, 'moundCount', '!FREQUENCY!', 'PYTHON_9.3')
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

        with arcpy.da.SearchCursor(os.path.join(myVars['workspace'], myVars['thalwegShp']), search_fields) as search:
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
        arcpy.CalculateField_management(thalPts, 'trResid', '!demZ! - !trendZ!', 'PYTHON_9.3')
        arr = arcpy.da.FeatureClassToNumPyArray(thalPts, ['trResid'])
        trResid_sd = arr['trResid'].std()
        arcpy.CalculateField_management(thalPts, 'trStResid', '!trResid! /' + str(trResid_sd), 'PYTHON_9.3')

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
        bfElim2 = arcpy.EliminatePolygonPart_management(os.path.join(myVars['workspace'], myVars['bfPolyShp']), 'in_memory/bfelim2', 'AREA', 10*bfw, '', 'ANY')
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
        bfCL = arcpy.CopyFeatures_management(os.path.join(myVars['workspace'], myVars['bfCL']), 'in_memory/tmp_bfCL')
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

    #  --channel nodes--

    if not os.path.exists(os.path.join(evpath, 'channelNodes.shp')):
        print '...channel nodes...'

        tmp_thalwegs = arcpy.CopyFeatures_management(os.path.join(myVars['workspace'], myVars['thalwegShp']), 'in_memory/thalwegs')

        arcpy.AddField_management(tmp_thalwegs, 'ThalwegID', 'SHORT')
        ct = 1
        with arcpy.da.UpdateCursor(tmp_thalwegs, ['ThalwegID']) as cursor:
            for row in cursor:
                row[0] = ct
                ct += 1
                cursor.updateRow(row)

        chNodes_mp = arcpy.Intersect_analysis(tmp_thalwegs, 'in_memory/tmp_chNodes_multiPart', 'NO_FID', '', 'POINT')

        if int(arcpy.GetCount_management(chNodes_mp).getOutput(0)) > 0:

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

            arcpy.LocateFeaturesAlongRoutes_lr(thalwegs_pts, mainCL_Route, 'ThalwegID', '', 'tbl_Routes.dbf', 'ThalwegID POINT MEAS', 'ALL')

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
        tmp_thalwegs = arcpy.CopyFeatures_management(os.path.join(myVars['workspace'], myVars['thalwegShp']), 'in_memory/thalwegs')

    #  ---------------------------------
    #  tier 3 classification
    #  ---------------------------------

    #  split units by slope categories

    #  create copy of tier 2 shapefile
    units_t2 = arcpy.CopyFeatures_management(os.path.join(outpath, 'Tier2_InChannel.shp'), 'in_memory/tmp_tier2_inChannel')
    arcpy.MakeFeatureLayer_management(units_t2, 'units_t2_lyr')
    arcpy.SelectLayerByAttribute_management('units_t2_lyr', "NEW_SELECTION", """ "UnitForm" = 'Bowl Transition' """)

    bowltrans = arcpy.CopyFeatures_management('units_t2_lyr', 'in_memory/bowl_trans')

    #  add attribute fields to tier 2 polygon shapefile
    nfields = [('GU', 'TEXT', '25'), ('GUKey', 'TEXT', '5')]

    for nfield in nfields:
        arcpy.AddField_management(bowltrans, nfield[0], nfield[1], '', '', nfield[2])

    guAttributes(bowltrans, bfw, dem, tmp_thalwegs, bfSlope, bfSlope_Smooth, evpath, **myVars)

    # ----------------------------------------------------------
    # Attribute tier 3 bowl transition features
    fields = ['UnitForm', 'bfSlopeSm', 'ThalwegTyp', 'Area', 'ElongRatio', 'SHAPE@', 'GU', 'GUKey']

    with arcpy.da.UpdateCursor(bowltrans, fields) as cursor:
        for row in cursor:
            if row[0] == 'Bowl Transition':
                    if row[2] == 'Cut-off' and row[3] > (myVars['chuteAreaThresh'] * bfw) and row[4] < 0.4:
                        row[6] = 'Chute'
                        row[7] = 'Ch'
            cursor.updateRow(row)

    with arcpy.da.UpdateCursor(bowltrans, fields) as cursor:
        for row in cursor:
            if row[6] != 'Chute':
                cursor.deleteRow()

    arcpy.SelectLayerByAttribute_management('units_t2_lyr', "NEW_SELECTION", """ "UnitForm" = 'Trough' OR "UnitForm" = 'Bowl Transition' """)
    #arcpy.CopyFeatures_management('units_t2_lyr', os.path.join(evpath, 'tmp_units_t2_lyr.shp')) # ToDo: delete after testing
    arcpy.SelectLayerByLocation_management('units_t2_lyr', 'ARE_IDENTICAL_TO', bowltrans, '','REMOVE_FROM_SELECTION')
    bowltras_trough_dissolve = arcpy.Dissolve_management('units_t2_lyr', 'in_memory/bowltras_trough_dissolve', ['ValleyUnit'], '', 'SINGLE_PART', 'UNSPLIT_LINES')
    #arcpy.CopyFeatures_management(bowltras_trough_dissolve, os.path.join(evpath, 'tmp_bowltras_trough_dissolve.shp')) # ToDo: delete after testing
    units_bowltrans_update = arcpy.Update_analysis(units_t2, bowltras_trough_dissolve, 'in_memory/units_bowltrans_update')
    with arcpy.da.UpdateCursor(units_bowltrans_update, ['SHAPE@Area', 'Area', 'UnitShape', 'UnitForm']) as cursor:
        for row in cursor:
            if row[3] == '':
                row[1] = row[0]
                row[2] = 'Planar'
                row[3] = 'Trough'
            cursor.updateRow(row)

    arcpy.MakeFeatureLayer_management(units_bowltrans_update, 'troughplane_lyr')
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

    #  find trough features < chute area threshold and merge with adjacent trough units
    units_troughplane_update = arcpy.Update_analysis(units_bowltrans_update, troughplane_slope_sp, 'in_memory/units_troughplane_update')

    #  if user doesn't want pocket pools, find bowl features < bowl area threshold and merge with adjacent unit (excluding walls)
    if myVars['createPocketPools'] != 'Yes':
        arcpy.MakeFeatureLayer_management(units_troughplane_update, 'units_troughplane_update_lyr')
        arcpy.SelectLayerByAttribute_management('units_troughplane_update_lyr', "NEW_SELECTION", """ "UnitForm" = 'Bowl' AND "Area" < %s """ % str(myVars['poolAreaThresh'] * bfw))
        #arcpy.CopyFeatures_management('units_troughplane_update_lyr', os.path.join(evpath, 'tmp_bowl_areaSelection.shp'))  # Todo: Delete after testing
        bowl_elim = arcpy.Eliminate_management('units_troughplane_update_lyr', 'in_memory/bowl_elim', 'AREA', """ "UnitForm" = 'Wall' """)
        #arcpy.CopyFeatures_management(bowl_elim, os.path.join(evpath, 'tmp_bowl_elim.shp')) # Todo: Delete after testing
        units_bowl_update = arcpy.Update_analysis(units_troughplane_update, bowl_elim, 'in_memory/units_bowl_update')
    else:
        units_bowl_update = units_troughplane_update

    arcpy.MakeFeatureLayer_management(units_bowl_update, 'units_bowl_update_lyr')

    #  add attribute fields to tier 2 polygon shapefile
    nfields = [('GU', 'TEXT', '25'), ('GUKey', 'TEXT', '5')]

    for nfield in nfields:
        arcpy.AddField_management(units_bowl_update, nfield[0], nfield[1], '', '', nfield[2])

    # ----------------------------------------------------------
    # Run tier 3 GU attributes function
    # ----------------------------------------------------------
    guAttributes(units_bowl_update, bfw, dem, tmp_thalwegs, bfSlope, bfSlope_Smooth, evpath, **myVars)

    # ----------------------------------------------------------
    # Classify Tier 3 GU
    # ----------------------------------------------------------
    # classify tier 3 wall features

    print '...classifying tier 3 wall features...'

    arcpy.MakeFeatureLayer_management(units_bowl_update, 'mound_ma_lyr', """ "UnitForm" = 'Mound' AND "Position" = 'Margin Attached' """)
    arcpy.MakeFeatureLayer_management(units_bowl_update, 'mound_mc_lyr', """ "UnitForm" = 'Mound' AND "Position" = 'Mid Channel' """)

    fields = ['UnitForm', 'Position', 'SHAPE@', 'Area','GU', 'GUKey']

    with arcpy.da.UpdateCursor(units_bowl_update, fields) as cursor:
        for row in cursor:
            if row[0] == 'Wall':
                if row[1] == 'Margin Attached':
                    row[4] = 'Bank'
                    row[5] = 'Bk'
                else:
                    if int(arcpy.GetCount_management(arcpy.SelectLayerByLocation_management('mound_ma_lyr', 'WITHIN_A_DISTANCE', row[2], 0.2 * bfw, "NEW_SELECTION")).getOutput(0)) > 0:
                        if row[3] >= (myVars['barAreaThresh'] * bfw):
                            row[4] = 'Margin Attached Bar'
                            row[5] = 'Br'
                        else:
                            row[4] = 'Barface'  # ToDo: Ask NK + JM about this classification
                            row[5] = 'Bf'
                    elif int(arcpy.GetCount_management(arcpy.SelectLayerByLocation_management('mound_mc_lyr', 'WITHIN_A_DISTANCE', row[2], 0.2 * bfw, "NEW_SELECTION")).getOutput(0)) > 0:
                        if row[3] >= (myVars['barAreaThresh'] * bfw):
                            row[4] = 'Mid Channel Bar'
                            row[5] = 'Br'
                        else:
                            row[4] = 'Barface'
                            row[5] = 'Bf'
                    else:
                        row[4] = 'NA'
                        row[5] = 'NA'
            cursor.updateRow(row)

    print '...classifying tier 3 concavities...'

    fields = ['UnitForm', 'Area', 'ThalwegCh', 'GU', 'GUKey']

    with arcpy.da.UpdateCursor(units_bowl_update, fields) as cursor:
        for row in cursor:
            if row[0] == 'Bowl':
                if row[1] >= (myVars['poolAreaThresh'] * bfw):
                    if row[2] == 'Backwater':
                        row[3] = 'Pond'
                        row[4] = 'Pd'
                    else:
                        row[3] = 'Pool'
                        row[4] = 'Po'
                else:
                    if myVars['createPocketPools'] == 'Yes':
                        row[3] = 'Pocket Pool'
                        row[4] = 'Pk'
            cursor.updateRow(row)

    # ----------------------------------------------------------
    # Attribute tier 3 planar features

    print '...classifying tier 3 planar features...'

    fields = ['UnitForm', 'OrientCat', 'ElongRatio', 'GU', 'GUKey']

    with arcpy.da.UpdateCursor(units_bowl_update, fields) as cursor:
        for row in cursor:
            if row[0] == 'Plane':
                if row[1] == 'Transverse' and row[2] < 0.6:
                    row[3] = 'Transition'
                    row[4] = 'Tr'
                    cursor.updateRow(row)

    arcpy.SelectLayerByAttribute_management('units_bowl_update_lyr', 'NEW_SELECTION', """ "GU" IS NULL AND "UnitForm" = 'Plane' """)
    plane_units = arcpy.CopyFeatures_management('units_bowl_update_lyr', 'in_memory/plane_units')
    planeflowtype = arcpy.Intersect_analysis([plane_units, os.path.join(outpath, 'Tier1.shp')], 'in_memory/planeflowtype')

    guAttributes(planeflowtype, bfw, dem, tmp_thalwegs, bfSlope, bfSlope_Smooth, evpath, **myVars)

    fields = ['UnitForm', 'Position', 'bfSlopeSm', 'bfwRatio', 'ElongRatio', 'FlowUnit', 'Area', 'ThalwegTyp', 'GU', 'GUKey']

    with arcpy.da.UpdateCursor(planeflowtype, fields) as cursor:
        for row in cursor:
            if row[0] == 'Plane':
                # if row[4] < 0.6 and row[3] < 0.17:  # ToDo: Ask NK why this criteria isn't the same as trough transition
                if row[4] < 0.4 and row[3] < 0.11:
                    row[8] = 'Transition'
                    row[9] = 'Tr'
                elif row[5] != 'Emergent' and row[7] == 'Cut-off' and row[6] >= (myVars['chuteAreaThresh'] * bfw) and row[4] < 0.4:
                    row[8] = 'Chute'
                    row[9] = 'Ch'
                elif row[6] >= (myVars['planebedAreaThresh'] * bfw):
                    if row[5] == 'Emergent':
                        if row[1] == 'Margin Attached':
                            row[8] = 'Margin Attached Bar'
                            row[9] = 'Br'
                        else:
                            row[8] = 'Mid Channel Bar'
                            row[9] = 'Bc'
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
                else:
                    row[8] = 'Transition'
                    row[9] = 'Tr'
            cursor.updateRow(row)

    #     ----------------------------------------------------------
        # Attribute tier 3 trough features
        arcpy.MakeFeatureLayer_management(units_bowl_update, 'pond_lyr',""" "UnitForm" = 'Bowl' AND "GU" = 'Pond' """)

        print '...classifying tier 3 trough features...'

        fields = ['UnitForm', 'bfSlopeSm', 'ThalwegTyp', 'Area', 'ElongRatio', 'SHAPE@', 'bfwRatio', 'GU', 'GUKey']

        with arcpy.da.UpdateCursor(units_bowl_update, fields) as cursor:
            for row in cursor:
                if row[0] == 'Trough':
                    if row[4] < 0.4 and row[6] < 0.11:
                    # if row[2] == 'None' and row[4] < 0.4: # ToDo: Ask NK why this sin't the same as plane transition criteria - Should we keep 'none'
                        row[7] = 'Transition'
                        row[8] = 'Tr'
                    elif row[2] == 'Cut-off' and row[3] > (myVars['chuteAreaThresh'] * bfw) and row[4] < 0.4:
                        row[7] = 'Chute'
                        row[8] = 'Ch'
                    elif row[3] >= (myVars['planebedAreaThresh'] * bfw):
                        if row[4] > 0.6 and int(arcpy.GetCount_management(arcpy.SelectLayerByLocation_management('pond_lyr', 'INTERSECT', row[5], '', "NEW_SELECTION")).getOutput(0)) > 0:
                            row[7] = 'Pond'
                            row[8] = 'Pd'
                        else:
                            if row[1] < 2.3:
                                row[7] = 'Glide-Run'
                                row[8] = 'GR'
                            elif row[1] < 4.3:
                                row[7] = 'Rapid'
                                row[8] = 'Ra'
                            else:
                                row[7] = 'Cascade'
                                row[8] = 'Ca'
                    else:
                        row[7] = 'Transition'
                        row[8] = 'Tr'
                cursor.updateRow(row)

        # ----------------------------------------------------------
        # Attribute tier 3 bowl transition features

        print '...classifying tier 3 bowl transition features...'

        fields = ['UnitForm', 'bfSlopeSm', 'ThalwegTyp', 'Area', 'ElongRatio', 'SHAPE@', 'GU', 'GUKey']

        with arcpy.da.UpdateCursor(units_bowl_update, fields) as cursor:
            for row in cursor:
                if row[0] == 'Bowl Transition':
                    if row[4] > 0.6 and int(arcpy.GetCount_management(arcpy.SelectLayerByLocation_management('pond_lyr', 'INTERSECT', row[5], '', "NEW_SELECTION")).getOutput(0)) > 0:
                        row[6] = 'Pond'
                        row[7] = 'Pd'
                    elif row[2] == 'None' and row[4] < 0.4:
                        row[6] = 'Transition'
                        row[7] = 'Tr'
                    else:
                        if row[2] == 'Cut-off' and row[3] > (myVars['chuteAreaThresh'] * bfw) and row[4] < 0.4:
                            row[6] = 'Chute'
                            row[7] = 'Ch'
                        elif row[2] == 'Braid' and row[3] > (myVars['chuteAreaThresh'] * bfw) and row[4] < 0.4:
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

        with arcpy.da.UpdateCursor(units_bowl_update, fields) as cursor:
            for row in cursor:
                if row[0] == 'Saddle':
                    row[1] = 'Riffle'
                    row[2] = 'Rf'
                cursor.updateRow(row)

    # ----------------------------------------------------------
    # Attribute tier 3 convexities

    print '...classifying Tier 3 mounds...'

    fields = ['UnitForm', 'Position', 'OrientCat', 'Morphology', 'Width', 'SHAPE@', 'Area','GU', 'GUKey']

    with arcpy.da.UpdateCursor(units_bowl_update, fields) as cursor:
        for row in cursor:
            if row[0] == 'Mound':
                if row[6] >= (myVars['barAreaThresh'] * bfw):
                    if row[1] != 'Margin Attached' and row[1] != 'Margin Detached':
                        row[7] = 'Mid Channel Bar'
                        row[8] = 'Bc'
                    else:
                        if row[3] == 'Elongated' and row[4] < (0.05 * bfw):
                            if row[4] == 'Transverse':
                                row[7] = 'Transition'
                                row[8] = 'Tr'
                            else:
                                row[7] = 'Bank'
                                row[8] = 'Bk'
                        else:
                            row[7] = 'Margin Attached Bar'
                            row[8] = 'Br'
                else:
                    row[7] = 'Transition'
                    row[8] = 'Tr'
            cursor.updateRow(row)

        with arcpy.da.UpdateCursor(units_bowl_update, fields) as cursor:
            for row in cursor:
                if row[0] == 'Mound Transition':
                    row[7] = 'Transition'
                    row[8] = 'Tr'
                cursor.updateRow(row)

    # ---------------------------------------------------------------------------------------------------
    # Dissolve planar units by UnitForm and GU if they share a border (cleans up slope breaks)
    # Re-run GU attributes
    units_planeflowtype_update = arcpy.Update_analysis(units_bowl_update, planeflowtype, 'in_memory/units_planeflowtype_update')
    t3_units = arcpy.Dissolve_management(units_planeflowtype_update, 'in_memory/t3_units', ['GU', 'GUKey'], '', 'SINGLE_PART', 'UNSPLIT_LINES')

    guAttributes(t3_units, bfw, dem, tmp_thalwegs, bfSlope, bfSlope_Smooth, evpath, **myVars)

    arcpy.CopyFeatures_management(t3_units, os.path.join(outpath, 'Tier3_InChannel_GU.shp'))
    arcpy.CopyFeatures_management(t3_units, os.path.join(outpath, 'Tier3_InChannel_GU_Raw.shp'))

    # ----------------------------------------------------------
    # Remove temporary files
    print '...removing intermediary surfaces...'

    for root, dirs, files in os.walk(myVars['workspace']):
        for f in fnmatch.filter(files, 'tbl_*'):
            os.remove(os.path.join(root, f))

    arcpy.Delete_management('in_memory')

    print '...done with Tier 3 GU classification.'


def tier3_subGU(**myVars):

    print 'Starting Tier 3 sub geomorphic unit classification...'

    #  create temporary workspace
    tmp_dir = tempfile.mkdtemp()

    #  environment settings
    arcpy.env.workspace = tmp_dir # set workspace to pf
    arcpy.env.overwriteOutput = True  # set to overwrite output

    #  set output paths
    evpath = os.path.join(myVars['workspace'], 'EvidenceLayers')
    if myVars['runFolderName'] != 'Default' and myVars['runFolderName'] != '':
        outpath = os.path.join(myVars['workspace'], 'Output', myVars['runFolderName'])
    else:
        runFolders = fnmatch.filter(next(os.walk(os.path.join(myVars['workspace'], 'Output')))[1], 'Run_*')
        runNum = int(max([i.split('_', 1)[1] for i in runFolders]))
        outpath = os.path.join(myVars['workspace'], 'Output', 'Run_%03d' % runNum)

    arcpy.Delete_management('in_memory')

    #  import required rasters
    dem = Raster(os.path.join(evpath, os.path.splitext(os.path.basename(os.path.join(myVars['workspace'], myVars['inDEM'])))[0] + '_mean.tif'))
    mIndex = Raster((os.path.join(evpath, 'mBendIndex.tif')))
    bfSlope = Raster(os.path.join(evpath, 'bfSlope.tif'))
    bfSlope_Smooth = Raster(os.path.join(evpath, 'bfSlope_Smooth.tif'))

    #  set raster environment settings
    desc = arcpy.Describe(dem)
    arcpy.env.extent = desc.Extent
    arcpy.env.outputCoordinateSystem = desc.SpatialReference
    arcpy.env.cellSize = desc.meanCellWidth

    #  import required shps
    arcpy.MakeFeatureLayer_management(os.path.join(evpath, 'channelEdge.shp'), 'edge_lyr')

    #  ----------------------------------
    #    calculate reach-level metrics
    #  ----------------------------------

    #  --calculate integrated bankfull and wetted widths--
    bfw = intWidth_fn(os.path.join(myVars['workspace'], myVars['bfPolyShp']), os.path.join(myVars['workspace'], myVars['bfCL']))

    #  --calculate gradient, sinuosity, thalweg ratio--

    #  check thalweg to see if it contains 'Length' field if not add field
    tmp_thalweg = arcpy.CopyFeatures_management(os.path.join(myVars['workspace'], myVars['thalwegShp']), 'in_memory/tmp_thalweg')
    if not 'Length' in [f.name for f in arcpy.ListFields(tmp_thalweg)]:
        arcpy.AddField_management(tmp_thalweg, 'Length', 'DOUBLE')

    #  calculate/re-calculate length field
    with arcpy.da.UpdateCursor(tmp_thalweg, ['SHAPE@LENGTH', 'Length']) as cursor:
        for row in cursor:
            row[1] = round(row[0], 3)
            cursor.updateRow(row)

    #  create feature layer for 'Main' thalweg
    arcpy.MakeFeatureLayer_management(tmp_thalweg, 'thalweg_lyr', """ "ThalwegTyp" = 'Main' """)

    #  get 'Main' thalweg length
    maxLength = float([row[0] for row in arcpy.da.SearchCursor('thalweg_lyr', ("Length"))][0])

    #  convert thalweg ends to points
    thalweg_pts = arcpy.FeatureVerticesToPoints_management('thalweg_lyr', 'in_memory/thalweg_pts', "BOTH_ENDS")

    #  calculate straight line distance between thalweg end points
    arcpy.PointDistance_analysis(thalweg_pts, thalweg_pts, 'tbl_thalweg_dist.dbf')
    straightLength = round(arcpy.SearchCursor('tbl_thalweg_dist.dbf', "", "", "", 'DISTANCE' + " D").next().getValue('DISTANCE'), 3)

    #  extract demZ values for each thalweg end point
    ExtractMultiValuesToPoints(thalweg_pts, [[dem, 'demZ']])
    maxZ = round(arcpy.SearchCursor(thalweg_pts, "", "", "", 'demZ' + " D").next().getValue('demZ'), 3)
    minZ = round(arcpy.SearchCursor(thalweg_pts, "", "", "", 'demZ' + " A").next().getValue('demZ'), 3)

    #  calculate gradient,sinuosity, and thalweg ratio
    gradient = round(((maxZ - minZ) / maxLength) * 100, 3)
    sinuosity = round(maxLength / straightLength, 3)

    #  ----------------------------------
    #    create tier 3 subGU polygons
    #  ----------------------------------
    t2_units = arcpy.CopyFeatures_management(os.path.join(outpath, 'Tier2_InChannel.shp'), 'in_memory/t2_units')
    t3_units = arcpy.CopyFeatures_management(os.path.join(outpath, 'Tier3_InChannel_GU.shp'), 'in_memory/t3_units')
    fields = arcpy.ListFields(t2_units)
    keep = ['ValleyUnit', 'UnitShape', 'UnitForm']
    drop = []
    for field in fields:
        if not field.required and field.name not in keep and field.type <> 'Geometry':
            drop.append(field.name)
    if len(drop) > 0:
        arcpy.DeleteField_management(t2_units, drop)

    t3_subunits = arcpy.Intersect_analysis([t3_units, t2_units], 'in_memory/t3_subunits')

    guAttributes(t3_subunits, bfw, dem, tmp_thalweg, bfSlope, bfSlope_Smooth, evpath, **myVars)

    # --tier 3 subGU functions --


    def subGUAttributes(units):

        print "Calculating tier 3 subGU attributes..."

        arcpy.MakeFeatureLayer_management(units, 'units_lyr')

        print "...unit roundness, convexity, compactness, relief, vertical compactness, platyness and sphericity..."

        #  calculate unit roundness and convexity using convex hull polygon
        #  calculate compactness, relief, vertical compactness, platyness, and sphericity

        unit_convexhull = arcpy.MinimumBoundingGeometry_management(units, 'in_memory/units_convexhull', 'CONVEX_HULL', '', '', 'MBG_FIELDS')
        arcpy.AddField_management(unit_convexhull, 'chPerim', 'DOUBLE')
        with arcpy.da.UpdateCursor(unit_convexhull, ['SHAPE@Length', 'chPerim']) as cursor:
            for row in cursor:
                row[1] = row[0]
                cursor.updateRow(row)
        arcpy.JoinField_management(units, 'UnitID', unit_convexhull, 'UnitID', ['chPerim'])

        tbl_unit_elevRange = ZonalStatisticsAsTable(units, 'UnitID', dem, 'tbl_unit_elevRange.dbf', 'DATA', 'RANGE')
        arcpy.JoinField_management(units, 'UnitID', tbl_unit_elevRange, 'UnitID', ['RANGE'])

        nfields = [('RiffCrest', 'TEXT', '5'), ('Roundness', 'DOUBLE', ''), ('Convexity', 'DOUBLE', ''), ('Compactness', 'DOUBLE', ''),
                   ('Relief', 'DOUBLE', ''), ('VCompact', 'DOUBLE', ''), ('Platyness', 'DOUBLE', ''), ('Sphericity', 'DOUBLE', '')]

        for nfield in nfields:
            arcpy.AddField_management(units, nfield[0], nfield[1], '', '', nfield[2])

        fields = ['Area', 'Perimeter', 'Width', 'Length', 'RANGE', 'chPerim', 'Roundness', 'Convexity', 'Compactness', 'Relief', 'VCompact', 'Platyness', 'Sphericity']
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

        #  --calculate channel node intersection--

        print '...channel confluence/diffluence...'

        if os.path.exists(os.path.join(evpath, 'channelNodes.shp')):
            arcpy.MakeFeatureLayer_management(os.path.join(evpath, 'channelNodes.shp'), 'confluence_lyr', """ "ChNodeType" = 'Confluence' """)
            arcpy.MakeFeatureLayer_management(os.path.join(evpath, 'channelNodes.shp'), 'diffluence_lyr', """ "ChNodeType" = 'Diffluence' """)

            with arcpy.da.UpdateCursor(units, ['ForceHyd']) as cursor:
                for row in cursor:
                    row[0] = 'NA'
                    cursor.updateRow(row)

            #  identify units that are in close proximity to channel confluence [assigning Y/N]
            arcpy.SelectLayerByLocation_management('units_lyr', 'INTERSECT', 'confluence_lyr', '', 'NEW_SELECTION')

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

            arcpy.SelectLayerByAttribute_management('units_lyr', "CLEAR_SELECTION")
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

        arcpy.SelectLayerByAttribute_management('units_lyr', "CLEAR_SELECTION")

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

        return(units)

    # ----------------------------------------------------------
    # Run tier 3 subGU attributes function
    # ----------------------------------------------------------
    subGUAttributes(t3_subunits)

    # add attribute fields to tier units shapefile
    nfields = [('SubGU', 'TEXT', '35'), ('SubGUKey', 'TEXT', '10'), ('SubUnitID', 'SHORT', '')]
    for nfield in nfields:
        arcpy.AddField_management(t3_subunits, nfield[0], nfield[1], '', '', nfield[2])

    # --tier 3 pool sub geomorphic unit logic--
    print '...classifying tier 3 pool sub geomorphic units...'

    fields = ['GU', 'SubGU', 'SubGUKey', 'ForceElem', 'ForceHyd', 'ThalwegTyp', 'mBendCat']

    with arcpy.da.UpdateCursor(t3_subunits, fields) as cursor:
        for row in cursor:
            if row[0] == 'Pool':
                if row[3] != 'NA':
                    row[1] = 'Forced Pool'
                    row[2] = 'Po-Fc'
                elif row[3] == 'Plunge':
                    row[1] = 'Plunge Pool'
                    row[2] = 'Po-Pg'
                elif row[3] == 'Grade Control':
                    row[1] = 'Dammed Pool'
                    row[2] = 'Po-Dm'
                elif row[3] == 'Confluence' and row[4] != 'Split':
                    row[1] = 'Confluence Pool'
                    row[2] = 'Po-Cf'
                elif row[5] == 'Outside':
                    row[1] = 'Meander Pool'
                    row[2] = 'Po-Md'
                else:
                    row[1] = 'Pool'
                    row[2] = 'Po'
            cursor.updateRow(row)

    # --tier 3 chute sub geomorphic unit logic--
    print '...classifying tier 3 chute sub geomorphic units...'

    fields = ['GU', 'SubGU', 'SubGUKey', 'ForceElem', 'ThalwegTyp', 'mBendCat']
    #  ToDo: need to add logic for case where main and cut-off are present (see NK keys)
    with arcpy.da.UpdateCursor(t3_subunits, fields) as cursor:
        for row in cursor:
            if row[0] == 'Chute':
                if row[3] != 'NA':
                    row[1] = 'Forced Chute'
                    row[2] = 'Ch-Fc'
                elif row[4] != 'None' and row[5] == 'Outside':
                    row[1] = 'Shallow Thalweg'
                    row[2] = 'Ch-Th'
                elif row[4] == 'Cut-off':
                    row[1] = 'Cut-off Chute'
                    row[2] = 'Ch-Cu'
                else:
                    row[1] = 'Chute'
                    row[2] = 'Ch'
            cursor.updateRow(row)

    # --tier 3 step sub geomorphic unit logic--
    print '...classifying tier 3 step sub geomorphic units...'

    fields = ['GU', 'SubGU', 'SubGUKey', 'ForceElem', 'Relief']
    with arcpy.da.UpdateCursor(t3_subunits, fields) as cursor:
        for row in cursor:
            if row[0] == 'Step':
                if row[3] == 'Anthropogenic':
                    row[1] = 'Engineered Structure'
                    row[2] = 'St-En'
                elif row[4] > myVars['waterfallReliefThreshold']:
                    row[1] = 'Waterfall'
                    row[2] = 'St-Wa'
                elif row[3] != 'NA':
                    row[1] = 'Forced Step'
                    row[2] = 'St-Fc'
                else:
                    row[1] = 'Step'
                    row[2] = 'St'
            cursor.updateRow(row)

    # --tier 3 riffle sub geomorphic unit logic--
    print '...classifying tier 3 riffle sub geomorphic units...'

    fields = ['GU', 'SubGU', 'SubGUKey', 'ForceElem']
    with arcpy.da.UpdateCursor(t3_subunits, fields) as cursor:
        for row in cursor:
            if row[0] == 'Riffle':
                if row[3] != 'NA':
                    row[1] = 'Forced Riffle'
                    row[2] = 'Rf-Fc'
                else:
                    row[1] = 'Riffle'
                    row[2] = 'Rf'
            cursor.updateRow(row)

    # --tier 3 bank sub geomorphic unit logic--
    print '...classifying tier 3 bank sub geomorphic units...'

    fields = ['GU', 'SubGU', 'SubGUKey', 'mBendCat']
    with arcpy.da.UpdateCursor(t3_subunits, fields) as cursor:
        for row in cursor:
            if row[0] == 'Bank':
                row[1] = 'Bank'
                row[2] = 'Bk'
            cursor.updateRow(row)

    # --tier 3 glide-run sub geomorphic unit logic--
    print '...classifying tier 3 glide-run sub geomorphic units...'
    #  ToDo: need to create roughness field and include logic (see NK keys)
    fields = ['GU', 'SubGU', 'SubGUKey', 'UnitForm']
    with arcpy.da.UpdateCursor(t3_subunits, fields) as cursor:
        for row in cursor:
            if row[0] == 'Glide-Run':
                if row[3] == 'Bowl Transition':
                    row[1] = 'Glide'
                    row[2] = 'GR-Gl'
                elif row[3] == 'Trough':
                    row[1] = 'Glide'
                    row[2] = 'GR-Gl'
                else:
                    row[1] = 'Run'
                    row[2] = 'GR-Ru'
            cursor.updateRow(row)

    # --tier 3 mid channel bar sub geomorphic unit logic--
    print '...classifying tier 3 mid channel bar sub geomorphic units...'
    #  ToDo: Add logic for bank attached islands
    fields = ['GU', 'SubGU', 'SubGUKey', 'OrientCat', 'ForceHyd', 'Morphology', 'ThalwegCt']
    with arcpy.da.UpdateCursor(t3_subunits, fields) as cursor:
        for row in cursor:
            if row[0] == 'Mid Channel Bar':
                if row[4] == 'Expansion' and row[3] != 'Longitudinal':
                    row[1] = 'Expansion Bar'
                    row[2] = 'Bc-Ex'
                elif row[4] == 'Eddy' and row[3] != 'Longitudinal':
                    row[1] = 'Eddy Bar'
                    row[2] = 'Bc-Ed'
                elif row[5] == 'Lobate' and row[3] != 'Transverse':
                    row[1] = 'Lobate Bar'
                    row[2] = 'Bc-Lb'
                elif row[6] > 1:
                    row[1] = 'Compound Bar'
                    row[2] = 'Bc-Cp'
                elif row[3] == 'Transverse':
                    row[1] = 'Transverse Bar'
                    row[2] = 'Bc-Tr'
                elif row[3] == 'Longitudinal':
                    row[1] = 'Longitudinal Bar'
                    row[2] = 'Bc-Lo'
                elif row[3] == 'Diagonal':
                    row[1] = 'Diagonal Bar'
                    row[2] = 'Bc-Dg'
                else:
                    row[1] = 'Mid Channel Bar'
                    row[2] = 'Bc'
            cursor.updateRow(row)

    # --tier 3 margin attached bar sub geomorphic unit logic--
    print '...classifying tier 3 margin attached bar sub geomorphic units...'
    #  ToDo: Need to check with NK if Diagnoal and Transverse bar logic is in correct sequence
    fields = ['GU', 'SubGU', 'SubGUKey', 'Position', 'OrientCat', 'ForceHyd', 'bedSlope', 'UnitForm', 'mBendCat', 'ElongRatio']
    with arcpy.da.UpdateCursor(t3_subunits, fields) as cursor:
        for row in cursor:
            if row[0] == 'Margin Attached Bar':
                if row[5] == 'Confluence' and row[3] != 'Channel Spanning':
                    row[1] = 'Confluence Bar'
                    row[2] = 'Br-Cf'
                elif row[5] == 'Eddy' and row[4] != 'Longitudinal':
                    row[1] = 'Eddy Bar'
                    row[2] = 'Br-Ed'
                elif row[5] == 'Expansion' and row[4] != 'Longitudinal':
                    row[1] = 'Expansion Bar'
                    row[2] = 'Br-Ex'
                elif row[6] < 0.6 or row[7] == 'Planar':
                    row[1] = 'Bench'
                    row[2] = 'Br-Be'
                elif gradient < 4.0: #
                    if sinuosity > 1.3:
                        if row[8] == 'Inside':
                            row[1] = 'Point Bar'
                            row[2] = 'Br-Pt'
                        elif row[8] == 'Outside':
                            row[1] = 'Counterpoint Bar'
                            row[2] = 'Br-Ct'
                        elif row[4] == 'Diagonal':
                            row[1] = 'Diagonal Bar'
                            row[2] = 'Br-Dg'
                        elif row[4] == 'Transverse':
                            row[1] = 'Transverse Bar'
                            row[1] = 'Br-Tr'
                        else:
                            row[1] = 'Lateral Bar'
                            row[2] = 'Br-La'
                    else:
                        row[1] = 'Lateral Bar'
                        row[2] = 'Br-La'
                elif gradient > 4.0:
                    if row[4] != 'Longitudinal':
                        row[1] = 'Transverse Rib'
                        row[2] = 'Br-Tb'
                    elif row[9] < 0.4:
                        row[1] = 'Ridge'
                        row[2] = 'Br-Ri'
                    else:
                        row[1] = 'Lateral Bar'
                        row[2] = 'Br-La'
                else:
                    row[1] = 'Margin Attached Bar'
                    row[2] = 'Br'
            cursor.updateRow(row)

    fields = ['OID@', 'SubUnitID']
    with arcpy.da.UpdateCursor(t3_subunits, fields) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    arcpy.CopyFeatures_management(t3_subunits, os.path.join(outpath, 'Tier3_InChannel_subGU.shp'))
    arcpy.CopyFeatures_management(t3_subunits, os.path.join(outpath, 'Tier3_InChannel_subGU_Raw.shp'))

    # ----------------------------------------------------------
    # Remove temporary files
    print '...removing intermediary surfaces...'

    for root, dirs, files in os.walk(myVars['workspace']):
        for f in fnmatch.filter(files, 'tbl_*'):
            os.remove(os.path.join(root, f))

    arcpy.Delete_management('in_memory')

    print '...done with Tier 3 sub GU classification.'