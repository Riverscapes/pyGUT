#  user defined arguments
guPolyShp     = r'C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\TopographicGUs\wrk_Data\01_TestSites\Lemhi\CBW05583-028079\2012\VISIT_1029\metricTest\Tier2_InChannel.shp'
bfPolyShp     = r'C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\TopographicGUs\wrk_Data\01_TestSites\Lemhi\CBW05583-028079\2012\VISIT_1029\metricTest\Bankfull.shp'
wePolyShp     = r'C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\TopographicGUs\wrk_Data\01_TestSites\Lemhi\CBW05583-028079\2012\VISIT_1029\metricTest\WaterExtent.shp'
inDEM         = r'C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\TopographicGUs\wrk_Data\01_TestSites\Lemhi\CBW05583-028079\2012\VISIT_1029\metricTest\DEM_mean.tif'
inWSEDEM      = r'C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\TopographicGUs\wrk_Data\01_TestSites\Lemhi\CBW05583-028079\2012\VISIT_1029\metricTest\WSEDEM.tif'
outFolder     = r'C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\TopographicGUs\wrk_Data\01_TestSites\Lemhi\CBW05583-028079\2012\VISIT_1029\metricTest'

# start of script

#  import required modules and extensions
import os
import numpy
import arcpy
from arcpy.sa import *
arcpy.CheckOutExtension('Spatial')

def main():

    #  set environment settings
    arcpy.env.workspace = outFolder
    arcpy.env.overwriteOutput = True

    #  import required rasters
    dem = Raster(inDEM)
    wsedem = Raster(inWSEDEM)

    #  set raster environment settings
    desc = arcpy.Describe(dem)
    arcpy.env.extent = desc.Extent
    arcpy.env.outputCoordinateSystem = desc.SpatialReference
    arcpy.env.cellSize = desc.meanCellWidth

    #  create temp copy of input units shp
    unit_poly = arcpy.CopyFeatures_management(guPolyShp, 'in_memory/unit_poly')
    unit_lyr = arcpy.MakeFeatureLayer_management(unit_poly, 'units_lyr')

    #  calculate unit area and perimeter
    arcpy.AddField_management(unit_poly, 'UnitID', 'SHORT')
    arcpy.AddField_management(unit_poly, 'Area', 'DOUBLE')
    arcpy.AddField_management(unit_poly, 'Perimeter', 'DOUBLE')
    arcpy.AddField_management(unit_poly, 'Compact', 'DOUBLE')

    fields = ['OID@', 'UnitID', 'SHAPE@AREA', 'SHAPE@LENGTH', 'Area', 'Perimeter', 'Compact']
    with arcpy.da.UpdateCursor(unit_poly, fields) as cursor:
        for row in cursor:
            row[1] = row[0]
            row[4] = row[2]
            row[5] = row[3]
            row[6] = row[4] / (row[5]**2)
            cursor.updateRow(row)

    #  calculate unit length and width using minimum bounding polygon
    unit_minbound = arcpy.MinimumBoundingGeometry_management(unit_poly, 'in_memory/units_minbound', 'RECTANGLE_BY_WIDTH', '', '', 'MBG_FIELDS')
    arcpy.AddField_management(unit_minbound, 'Width', 'DOUBLE')
    arcpy.AddField_management(unit_minbound, 'Length', 'DOUBLE')
    fields = ['MBG_Width', 'MBG_Length', 'Width', 'Length']
    with arcpy.da.UpdateCursor(unit_minbound, fields) as cursor:
        for row in cursor:
            row[2] = row[0]
            row[3] = row[1]
            cursor.updateRow(row)
    arcpy.JoinField_management(unit_poly, 'UnitID', unit_minbound, 'UnitID', ['Width', 'Length'])

    #  unit bed slope raster mean and sd
    bed_slope = Slope(dem, 'DEGREE')
    bed_slope.save('in_memory/BedSl')

    #  unit curvature raster mean and sd
    Curvature(dem, '', 'in_memory/PrCrv', 'in_memory/PlCrv')

    #  unit water surface slope raster mean and sd
    ws_slope = Slope(wsedem, 'DEGREE')
    ws_slope.save('in_memory/WSSl')

    #  create bankfull surface slope raster
    #  a. convert bankfull polygon to points
    bf_pts = arcpy.FeatureVerticesToPoints_management(bfPolyShp, 'in_memory/bf_pts', 'ALL')
    #  b. extract dem Z value to bankfull polygon points
    ExtractMultiValuesToPoints(bf_pts, [[dem, 'demZ']], 'NONE')
    #  c. remove points where demZ = -9999 (so, < 0) and where points
    #  intersect wePoly (this is to remove points at DS and US extent of reach)
    with arcpy.da.UpdateCursor(bf_pts, 'demZ') as cursor:
        for row in cursor:
            if row[0] <= 0.0:
                cursor.deleteRow()
    arcpy.MakeFeatureLayer_management(bf_pts, 'bf_pts_lyr')
    arcpy.SelectLayerByLocation_management('bf_pts_lyr', 'WITHIN_A_DISTANCE', wePolyShp, str(desc.meanCellWidth) + ' Meters')
    if int(arcpy.GetCount_management('bf_pts_lyr').getOutput(0)) > 0:
        arcpy.DeleteFeatures_management('bf_pts_lyr')
    #  d. create bankfull elevation raster and clip to bankfull
    raw_bfe = NaturalNeighbor(bf_pts, 'demZ', 0.1)
    bfe = ExtractByMask(raw_bfe, bfPolyShp)
    #  e. calculate bfe slope
    bfe_slope = Slope(bfe, 'DEGREE')
    bfe_slope.save('in_memory/BFSl')

    #  raster stats to units
    rasters = ['in_memory/BedSl', 'in_memory/WSSl', 'in_memory/BFSl', 'in_memory/PrCrv', 'in_memory/PlCrv']
    for raster in rasters:
        raster_name = raster.split('/')[1]
        tbl_name = 'tbl_' + raster_name + '.dbf'
        mean_fname = raster_name + '_Mean'
        sd_fname = raster_name + '_SD'
        ZonalStatisticsAsTable(unit_lyr, 'UnitID', raster, tbl_name, 'DATA', 'MEAN_STD')
        arcpy.AddField_management(tbl_name, mean_fname, 'DOUBLE')
        arcpy.AddField_management(tbl_name, sd_fname, 'DOUBLE')
        with arcpy.da.UpdateCursor(tbl_name, ['MEAN', 'STD', mean_fname, sd_fname]) as cursor:
            for row in cursor:
                row[2] = row[0]
                row[3] = row[1]
                cursor.updateRow(row)
        arcpy.JoinField_management(unit_poly, 'UnitID', tbl_name, 'UnitID', [mean_fname, sd_fname])
        arcpy.Delete_management(tbl_name)

    #  save unit poly shp with metrics to new shp
    out_fname = os.path.splitext(os.path.basename(guPolyShp))[0]
    arcpy.CopyFeatures_management(unit_poly, out_fname + '_metrics.shp')

    #  output attribute table to a *csv
    nparr = arcpy.da.FeatureClassToNumPyArray(unit_poly, ['*'])
    field_names = [f.name for f in arcpy.ListFields(unit_poly)]
    fields_str = ','.join(str(i) for i in field_names)
    numpy.savetxt(outFolder + '/' + out_fname + '_metrics.csv', nparr, fmt="%s", delimiter=",", header=str(fields_str), comments='')

if __name__ == '__main__':
    main()