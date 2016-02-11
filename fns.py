# Geomorphic Unit Tool Functions

# Last updated: 10/14/2015
# Created by: Sara Bangen (sara.bangen@gmail.com)

import arcpy, numpy, os
from arcpy import env
from arcpy.sa import *

config = {}


def setConfig(newconf):
    global config
    config = newconf

# -----------------------------------------------------------------------
#  Evidence Raster Function
#
# Input parameters
# dem:          DEM name, including suffix
# det:          Detrended DEM name, including suffix
# bfPoints:     Bankfull points shapefile name, including suffix
# bfPolyShp:    Bankfull polygon shapfiled name, including suffix
# wePolyShp:    Height above bankfull raster name, including suffix
# intBFW:       Integrated bankfull width (m; floating point)
# intWW:        Integrated wetted width (m; floating point)
# fwRelief:     Focal window (in meters) for detDEM relief calculation.
# -----------------------------------------------------------------------

def EvidenceRasters(dem, det, bfPoints, bfPolyShp, wePolyShp, intBFW, intWW, fwRelief):

    # GENERAL EVIDENCE RASTERS

    #----------------------------------------
    # Bankfull raster

    tmp_bfPoly = 'tmp_bfPoly.img'
    # Convert bankfulll polygon to raster
    arcpy.PolygonToRaster_conversion(bfPolyShp, 'FID', tmp_bfPoly, 'CELL_CENTER')
    # Set cells inside/outside bankfull polygon to 1/0
    outCon = Con(IsNull(tmp_bfPoly), 0, 1)
    # Clip to detrended DEM
    bfPoly = ExtractByMask(outCon, det)
    # Save output
    bfPoly.save('bfPoly.img')
    arcpy.Delete_management('tmp_bfPoly.img')

    #----------------------------------------
    # Mean slope raster

    # Calculate detrended slope raster
    detSlope = Slope(det, 'DEGREE')
    # Calculate mean slope over neighborhood window
    fwSlope = round(intBFW * 0.1, 1)
    neighborhood = NbrRectangle(fwSlope, fwSlope, 'MAP')
    meanSlope = FocalStatistics(detSlope, neighborhood, 'MEAN', 'DATA')
    outMeanSlope = ExtractByMask(meanSlope, det)
    # Save output
    detSlope.save('detSlope.img')
    outMeanSlope.save('meanSlope.img')

    # IN CHANNEL SPECFIC EVIDENCE RASTERS

    #----------------------------------------
    # Normalized fill raster

    # Fill dem and get difference
    rFill = Fill(dem)
    rDiff = (rFill - dem)
    # Clip to bankfull
    rClip = ExtractByMask(rDiff, bfPolyShp)
    # Normalize values
    fMinResult = arcpy.GetRasterProperties_management(rClip, 'MINIMUM')
    fMin = float(fMinResult.getOutput(0))
    fMaxResult = arcpy.GetRasterProperties_management(rClip, 'MAXIMUM')
    fMax = float(fMaxResult.getOutput(0))
    normFill = (rClip - fMin) / (fMax - fMin)
    # Save output
    normFill.save('normFill.img')

    #----------------------------------------
    # Normalized inverse fill raster

    # Fill detrended DEM and get difference
    rFill = Fill(det)
    rDiff = rFill - det
    # Clip to bankfull
    rClip = ExtractByMask(rDiff, bfPolyShp)
    # Set cells that were filled to NA and cell that weren't to 1
    # Multiply by detrended DEM to get Z values ('convexity height')
    rNull = SetNull(rClip, 1, '"VALUE" > 0') * det
    # Normalize Z values
    zMinResult = arcpy.GetRasterProperties_management(rNull, 'MINIMUM')
    zMin = float(zMinResult.getOutput(0))   
    zMaxResult = arcpy.GetRasterProperties_management(rNull, 'MAXIMUM')
    zMax = float(zMaxResult.getOutput(0))    
    rNorm = (rNull - zMin) / (zMax - zMin)
    # Set all other values to 0 and clip to bf
    rCon = Con(IsNull(rNorm), 0, rNorm)
    invFill = ExtractByMask(rCon, bfPolyShp)
    # Save output
    invFill.save('normInvFill.img')

    #----------------------------------------
    # Channel margin raster

    # Remove any wePoly parts < 5% of total area
    wePolyElim = 'wePolyElim.shp'
    arcpy.EliminatePolygonPart_management(wePolyShp, wePolyElim, 'PERCENT', '', 5, 'ANY')                     
    # Erase wePolyelim from bankfull polygon
    polyErase = 'polyErase.shp'
    arcpy.Erase_analysis(bfPolyShp, wePolyElim, polyErase, '')
    # Buffer the output by 10% of the integrated wetted width
    polyBuffer = 'polyBuffer.shp'
    bufferDist = 0.1 * intWW
    arcpy.Buffer_analysis(polyErase, polyBuffer, bufferDist, 'FULL')
    # Clip the output to the bankull polygon
    polyClip = 'polyClip.shp'
    arcpy.Clip_analysis(polyBuffer, bfPolyShp, polyClip)
    # Convert the output to a raster
    arcpy.PolygonToRaster_conversion(polyClip, 'FID', 'outRas.img', 'CELL_CENTER', 'NONE', '0.1')                                
    # Set all cells inside/outside the bankfull ratser to 1/0 
    chMargin = Con(IsNull('outRas.img'), 0, 1)
    # Save the ouput
    chMargin.save('chMargin.img')
    # Delete intermediate shapefiles and rasters
    arcpy.Delete_management('wePolyElim.shp')
    arcpy.Delete_management('polyErase.shp')
    arcpy.Delete_management('polyBuffer.shp')
    arcpy.Delete_management('polyClip.shp')
    arcpy.Delete_management('outRas.img')

    #----------------------------------------
    # Bankfull surface slope raster

    # Convert bankfull polygon to points
    bfLine = 'tmp_bfLine.shp'
    bfPts = 'tmp_bfPts.shp'
    arcpy.FeatureToLine_management(bfPolyShp, bfLine)
    arcpy.FeatureVerticesToPoints_management(bfLine, bfPts, 'ALL')
    # Extract dem Z value to bankfull polygon points
    arcpy.CopyFeatures_management(bfPts, 'tmp_bfPtsZ.shp')
    bfPtsZ = 'tmp_bfPtsZ.shp'
    ExtractMultiValuesToPoints(bfPtsZ, [[dem, 'demZ']], 'NONE')
    # Remove points where demZ = -9999 (so, < 0) and where points
    # intersect wePoly (this is to remove points at DS and US extent of reach)
    with arcpy.da.UpdateCursor(bfPtsZ, 'demZ') as cursor:
        for row in cursor:
            if row[0] <= 0.0:
                cursor.deleteRow()
    arcpy.MakeFeatureLayer_management(bfPtsZ, 'tmp_bfPtsZ_lyr')
    arcpy.SelectLayerByLocation_management('tmp_bfPtsZ_lyr', 'WITHIN_A_DISTANCE', wePolyShp, '0.02 Meters')
    if int(arcpy.GetCount_management('tmp_bfPtsZ_lyr').getOutput(0)) > 0:
        arcpy.DeleteFeatures_management('tmp_bfPtsZ_lyr')
    # Create bankfull elevation tin and raster
    bfetin = 'tmp_bfetin'
    bfe = 'bfe.img'
    desc = arcpy.Describe(dem)
    sr = desc.spatialReference
    arcpy.CreateTin_3d(bfetin, sr, [[bfPtsZ, 'demZ', 'masspoints'], [bfPolyShp, '<None>', 'softclip']])
    arcpy.TinRaster_3d(bfetin, bfe, 'FLOAT', 'NATURAL_NEIGHBORS', 'CELLSIZE 0.1')
    # Create bfe slope raster
    bfSlope = Slope(bfe, 'DEGREE')
    # Calculate mean bfe slope over bfw neighborhood
    neighborhood = NbrRectangle(config.intBFW, config.intBFW, 'MAP')
    slope_focal = FocalStatistics(bfSlope, neighborhood, 'MEAN')
    # Clip to bankfull polygon
    meanBFSlope = ExtractByMask(slope_focal, bfPolyShp)
    # Save output
    meanBFSlope.save('bfeSlope_meanBFW.img')
    # Delete intermediate shapefiles and rasters
    arcpy.Delete_management('tmp_bfLine.shp')
    arcpy.Delete_management('tmp_bfPts.shp')
    arcpy.Delete_management('tmp_bfPtsZ.shp')
    arcpy.Delete_management('tmp_bfPtsZ_lyr')
    arcpy.Delete_management('tmp_bfetin')

    #----------------------------------------
    # Normalized bankfull depth raster

    # Subtract dem from bankfull surface dem
    rawBFD = 'tmp_rawBFD.img'
    rawBFD = Minus(bfe, dem)
    BFD = SetNull(rawBFD, rawBFD, '"VALUE" < 0')
    # Normalize values
    bMinResult = arcpy.GetRasterProperties_management(BFD, 'MINIMUM')
    bMin = float(bMinResult.getOutput(0))
    bMaxResult = arcpy.GetRasterProperties_management(BFD, 'MAXIMUM')
    bMax = float(bMaxResult.getOutput(0))
    normBFD = (BFD - bMin) / (bMax - bMin)
    # Save output
    BFD.save('bfDepth.img')
    normBFD.save('normBFDepth.img')
    # Delete intermediate shapefiles and rasters
    # arcpy.Delete_management('tmp_rawBFD.shp')

    # OUT OF CHANNEL SPECIFIC EVIDENCE RASTERS

    #----------------------------------------
    # Normalized height above detrended bankfull Z raster

    # Extract detDEM z values to bfPoints
    arcpy.CopyFeatures_management(bfPoints, 'tmp_bfPoints.shp')
    tmpPts = 'tmp_bfPoints.shp'
    ExtractMultiValuesToPoints(tmpPts, [[det, 'detZ']], 'NONE')
    # Delete any points where 'detZ' values is NoData
    # Note: in shapefile NoData is -9999, but for some
    # reason when imported here, it is changed to '0.0'
    with arcpy.da.UpdateCursor(tmpPts, 'detZ') as cursor:
        for row in cursor:
            if row[0] == 0.0:
                cursor.deleteRow()
    # Get mean detZ value
    zList = []
    with arcpy.da.SearchCursor(tmpPts, 'detZ') as rows:
        for row in rows:
            zList.append(row)
    zMean = numpy.mean(zList)
    # Calculate height above detrended DEM (hadBF) raster
    # as det Z - mean Z
    HADBF = Minus(det, zMean)
    # Normalize hadBF by maximum bankfull depth
    maxResult = arcpy.GetRasterProperties_management(BFD, 'MAXIMUM')
    max = float(maxResult.getOutput(0))
    HADBF_norm = HADBF / max   
    # Save output
    HADBF.save('HADBF.img')
    HADBF_norm.save('normHADBF.img')
    # Delete temporary files
    arcpy.Delete_management('tmp_bfPoints.shp')

    #----------------------------------------
    # Distance from bankfull raster

    # Calculate euclidean distance from bankfull polygon
    rawDist = EucDistance(bfPolyShp)
    # Clip to detrended DEM
    outDist = ExtractByMask(rawDist, det)
    # Save output
    outDist.save('bfDist.img')

    #----------------------------------------
    # Detrended DEM relief raster

    # Set neighborhood window
    neighborhood = NbrRectangle(fwRelief, fwRelief, 'MAP')
    # Clip detrended DEM area outside bankfull
    tmp_det = SetNull(bfPoly, det, '"VALUE" = 1')
    # Calculate relief as Z range in neighborhood
    Relief = FocalStatistics(tmp_det, neighborhood, 'RANGE', 'DATA')
    # Clip to area outside bankfull 
    outRelief = ExtractByMask(Relief, tmp_det)
    # Save output
    outRelief.save('detRelief.img')

# -----------------------------------------------------------------------
# Tier 2 Function
#
# -----------------------------------------------------------------------

def Tier2():

    # Assign input evidence rasters
    bfPoly = Raster('bfPoly.img')
    meanSlope = Raster('meanSlope.img')
    normHADBF = Raster('normHADBF.img')
    Relief = Raster('detRelief.img')
    bfDist = Raster('bfDist.img')
    normBFD = Raster('normBFDepth.img')
    normF = Raster('normFill.img')
    cm = Raster('chMargin.img')
    normInvF = Raster('normInvFill.img')
    bfeSlope = Raster('bfeSlope_meanBFW.img')

    # OUT OF CHANNEL UNITS

    #----------------------------------------
    # Active Floodplain Units

    # Calculate transform function line slope + intercept
    sl_le = lineEq(0.99, 0.01, config.lowSlope, config.upSlope)
    hadbf_le = lineEq(0.99, 0.01, config.lowHADBF, config.upHADBF)
    r_le = lineEq(0.99, 0.01, config.lowRelief, config.upRelief)
    # Execute Conditional Statements
    bf_fn = Con(bfPoly == 0, 0.99, 0.01)
    sl_fn = Con(meanSlope <= config.lowSlope, 0.99, Con(meanSlope >= config.upSlope, 0.01, meanSlope * sl_le[0] + sl_le[1]))
    hadbf_fn = Con(normHADBF <= config.lowHADBF, 0.99, Con(normHADBF >= config.upHADBF, 0.01, normHADBF * hadbf_le[0] + hadbf_le[1]))
    r_fn = Con(Relief <= config.lowRelief, 0.99, Con(Relief >= config.upRelief, 0.01, Relief * r_le[0] + r_le[1]))
    # Calculate and save floodplain output
    outAFP = (bf_fn * sl_fn * hadbf_fn * r_fn)
    outAFP.save('t2AFloodplain_Mem.img')
    # Run output through guThresh function
    guThresh(outAFP, 't2Floodplain', 1.0, 'Out of Channel', 'Active Floodplain', 7, 'FALSE')

    #----------------------------------------
    # Cutbank Units

    # Calculate transform function line slope + intercept
    sl_le = lineEq(0.01, 0.99, config.lowCMSlope, config.upCMSlope)
    dist_le = lineEq(0.99, 0.01, config.lowBFDist, config.upBFDist)
    # Execute Conditional Statements
    bf_fn = Con(bfPoly == 0, 0.99, 0.01)
    slope_fn = Con(meanSlope <= config.lowCMSlope, 0.01, Con(meanSlope >= config.upCMSlope, 0.99, meanSlope * sl_le[0] + sl_le[1]))
    dist_fn = Con(bfDist <= config.lowBFDist, 0.99, Con(bfDist >= config.upBFDist, 0.01, bfDist * dist_le[0] + dist_le[1]))
    # Calculate cutbank output
    outCB = (bf_fn * slope_fn * dist_fn)
    outCB.save('t2Cutbank_Mem.img')
    # Run and save output through guThresh function
    guThresh(outCB, 't2Cutbank', 0.1, 'Out of Channel', 'Cutbank', 6, 'FALSE')

    #----------------------------------------
    # Hillslope/Fan Units

    # Calculate transform function line slope + intercept
    sl_le = lineEq(0.01, 0.99, config.lowSlope, config.upSlope)
    dist_le = lineEq(0.01, 0.99, config.lowBFDist, config.upBFDist)
    r_le = lineEq(0.01, 0.99, config.lowRelief, config.upRelief)
    # Execute Conditional Statements
    bf_fn = Con(bfPoly == 0, 0.99, 0.01)
    slope_fn = Con(meanSlope >= config.upSlope, 0.99, Con(meanSlope <= config.lowSlope, 0.01, meanSlope * sl_le[0] + sl_le[1]))
    dist_fn = Con(bfDist >= config.upBFDist, 0.99, Con(bfDist <= config.lowBFDist, 0.01, bfDist * dist_le[0] + dist_le[1]))
    r_fn = Con(Relief >= config.upRelief, 0.99, Con(Relief <= config.lowRelief, 0.01, Relief * r_le[0] + r_le[1]))
    # Calculate and save hillslope output
    outHS = (bf_fn * slope_fn * dist_fn * r_fn)
    outHS.save('t2HillslopeFan_Mem.img')
    # Run output through guThresh function
    guThresh(outHS, 't2HillslopeFan', 1.0, 'Out of Channel', 'Hillslope/Fan', 8, 'FALSE')

    #----------------------------------------
    # Inactive Floodplain (i.e., terraces) Units

    # Calculate transform function line slope + intercept
    sl_le = lineEq(0.99, 0.01, config.lowSlope, config.upSlope)
    hadbf_le = lineEq(0.01, 0.99, config.lowHADBF, config.upHADBF)
    r_le = lineEq(0.99, 0.01, config.lowRelief, config.upRelief)
    # Execute Conditional Statements
    bf_fn = Con(bfPoly == 0, 0.99, 0.01)
    sl_fn = Con(meanSlope <= config.lowSlope, 0.99, Con(meanSlope >= config.upSlope, 0.01, meanSlope * sl_le[0] + sl_le[1]))
    hadbf_fn = Con(normHADBF <= config.lowHADBF, 0.01, Con(normHADBF >= config.upHADBF, 0.99, normHADBF * hadbf_le[0] + hadbf_le[1]))
    r_fn = Con(Relief <= config.lowRelief, 0.99, Con(Relief >= config.upRelief, 0.01, Relief * r_le[0] + r_le[1]))
    # Calculate and save terrace output
    outIFP = (bf_fn * sl_fn * hadbf_fn * r_fn)
    outIFP.save('t2Terrace_Mem.img')
    # Run output through guThresh function
    guThresh(outIFP, 't2Terrace', 1.0, 'Out of Channel', 'Terrace', 9, 'FALSE')

    # IN CHANNEL UNITS

    #----------------------------------------
    # Concavity Units

    # Get summary stats for use in transform functions
    sdResult = arcpy.GetRasterProperties_management(normBFD, 'STD')
    sd = float(sdResult.getOutput(0))
    meanResult = arcpy.GetRasterProperties_management(normBFD, 'MEAN')
    mean = float(meanResult.getOutput(0))
    # Calculate transform function line slope + intercept
    bfD_le = lineEq(0.01, 0.99, mean, (mean + (1 * sd)))
    # Execute Conditional Statements
    bf_fn = Con(bfPoly == 0, 0.01, 0.99)
    normF_fn = Con(normF > 0, 0.99, 0.01)
    normBFD_fn = Con(normBFD <= mean, 0.01, Con(normBFD >= (mean + (1 * sd)), 0.99, normBFD * bfD_le[0] + bfD_le[1]))
    # Calculate and save concavity output
    rawCV = (normBFD_fn * normF_fn * bf_fn)
    rCV = Con(IsNull(rawCV), 0.01, rawCV)
    outCV = ExtractByMask(rCV, bfPoly)
    outCV.save('t2Concavity_Mem.img')
    # Run output through guThresh function
    guThresh(outCV, 't2Concavity', 0.25, 'In Channel', 'Concavity', 1, 'TRUE')

    #----------------------------------------
    # Bank Units

    # Read in and assign tier 2 concavity membership
    t2cv = Raster('t2Concavity_Mem2.img')
    # Calculate transform function line slope + intercept
    sl_le = lineEq(0.01, 0.99, config.lowCMSlope, config.upCMSlope)
    # Execute Conditional Statements
    cm_fn = Con(cm == 0, 0.01, 0.99)
    slope_fn = Con(meanSlope <= config.lowCMSlope, 0.01, Con(meanSlope >=  config.upCMSlope, 0.99, meanSlope * sl_le[0] + sl_le[1]))
    inv_cv = Con(IsNull(t2cv), 0.01, t2cv)
    inv_cv2 = 1.0 - inv_cv
    # Calculate and save channel margin output
    rawCM = (cm_fn * slope_fn * inv_cv2)
    rcCM = Con(IsNull(rawCM), 0.01, rawCM)
    outCM = ExtractByMask(rcCM, bfPoly)
    outCM.save('t2ChMargin_Mem.img')
    # Run output through guThresh function
    guThresh(outCM, 't2ChMargin', 0.05, 'Channel Interface', 'Bank', 5, 'FALSE')

    #----------------------------------------
    # Convexity Units

    # Read in and assign tier 2 channel margin membership
    t2cm = Raster('t2ChMargin_Mem2.img')
    # Get summary stats for use in transform functions
    sdResult = arcpy.GetRasterProperties_management(normBFD, 'STD')
    sd = float(sdResult.getOutput(0))
    meanResult = arcpy.GetRasterProperties_management(normBFD, 'MEAN')
    mean = float(meanResult.getOutput(0))
    # Calculate transform function line slope + intercept
    normBFD_le = lineEq(0.99, 0.01, mean, mean + (1 * sd))
    #normF_le = lineEq(0.99, 0.01, 0, 0.05)
    invF_le = lineEq(0.01, 0.99, 0.0, 0.1)
    # Execute Conditional Statements
    bf_fn = Con(bfPoly == 0, 0.01, 0.99)
    normF_fn = Con(normF == 0, 0.99, 0.01)
    invF_fn = Con(normInvF > 0.1, 0.99, Con(normInvF <= 0.0, 0.01, normInvF * invF_le[0] + invF_le[1]))
    normBFD_fn = Con(normBFD <= mean, 0.99, Con(normBFD >= mean + (1 * sd), 0.01, normBFD * normBFD_le[0] + normBFD_le[1]))
    # Calculate inverse tier 2 unit
    inv_cm = Con(IsNull(t2cm), 0.01, t2cm)
    inv_cm2 = 1.0 - inv_cm
    inv_t2 = inv_cv2 * inv_cm2
    # Calculate and save convexity output
    rawCX = (bf_fn * invF_fn * normBFD_fn * inv_t2)
    outCX = ExtractByMask(rawCX, bfPoly)
    outCX.save('t2Convexity_Mem.img')
    # Run output through guThresh function
    guThresh(outCX, 't2Convexity', 0.5, 'In Channel', 'Convexity', 2, 'FALSE')

    #----------------------------------------
    # Run/Glide Units

    # Read in and assign tier 2 convexity membership
    t2cx = Raster('t2Convexity_Mem2.img')
    # Calculate transform function line slope + intercept
    bfeSl_le = lineEq(0.99, 0.01, 1.5, 3.0)
    normF_le = lineEq(0.99, 0.01, 0.0, 0.1)
    invF_le = lineEq(0.99, 0.01, 0.0, 0.1)
    # Execute Conditional Statements
    bf_fn = Con(bfPoly == 0, 0.01, 0.99)
    bfeSl_fn = Con(bfeSlope > 3.0, 0.01, Con(bfeSlope < 1.5, 0.99, bfeSlope * bfeSl_le[0] + bfeSl_le[1]))
    normF_fn = Con(normF > 0.1, 0.01, Con(normF <= 0.0, 0.99, normF * normF_le[0] + normF_le[1]))
    invF_fn = Con(normInvF > 0.1, 0.01, Con(normInvF <= 0.0, 0.99, normInvF * invF_le[0] + invF_le[1]))
    # Calculate inverse tier 2 unit
    inv_cx = Con(IsNull(t2cx), 0.01, t2cx)
    inv_cx2 = 1.0 - inv_cx
    inv_t2 = inv_cv2 * inv_cm2 * inv_cx2
    # Calculate and save run/glide output
    rawPF_01 = (bf_fn * bfeSl_fn * invF_fn * normF_fn * inv_t2)
    rcPF_01 = Con(IsNull(rawPF_01), 0.01, rawPF_01)
    outPF_01 = ExtractByMask(rcPF_01, bfPoly)
    outPF_01.save('t2Planar_runglide_Mem.img')
    # Run output through guThresh function
    guThresh(outPF_01, 't2Planar_runglide', 0.5, 'In Channel', 'Planar-RunGlide', 3, 'FALSE')

    #----------------------------------------
    # Rapid/Cascade Units

    # Calculate transform function line slope + intercept
    bfeSl_le_02 = lineEq(0.01, 0.99, 1.5, 3.0)
    nc_le_02 = lineEq(0.99, 0.01, 0.0, 0.2)
    invF_le_02 = lineEq(0.99, 0.01, 0.0, 0.2)
    # Execute Conditional Statements
    bfeSl_fn_02 = Con(bfeSlope > 3.0, 0.99, Con(bfeSlope < 1.5, 0.01, bfeSlope * bfeSl_le_02[0] + bfeSl_le_02[1]))
    nc_fn_02 = Con(normF > 0.2, 0.01, Con(normF <= 0.0, 0.99, normF * nc_le_02[0] + nc_le_02[1]))
    invF_fn_02 = Con(normInvF > 0.2, 0.01, Con(normInvF <= 0.0, 0.99, normInvF * invF_le_02[0] + invF_le_02[1]))
    # Calculate rapid/cascade output
    rawPF_02 = (bf_fn * bfeSl_fn_02 * inv_t2)
    rcPF_02 = Con(IsNull(rawPF_02), 0.01, rawPF_02)
    outPF_02 = ExtractByMask(rcPF_02, bfPoly)
    outPF_02.save('t2Planar_rapcasc_Mem.img')
    # Run output through guThresh function
    guThresh(outPF_02, 't2Planar_rapcasc', 0.5, 'In Channel', 'Planar-RapidCascade', 4, 'FALSE')

# -----------------------------------------------------------------------
# Geomorphic Unit Threshold Function
#
# Input parameters
#
# ras:           Input raster name
# outName:       Output raster name, not including suffix
# areaThFactor:  Factor value used for area threshold (e.g., 0.5; area thresh will be 0.5 * bankfull width)
# t1Name:        Tier 1 name
# t2Name:        Tier 2 name
# rasVal:        Unique raster value
# saveNQ:        TRUE/FALSE - Should non qualifying (by area) units be saved?
# -----------------------------------------------------------------------

def guThresh(ras, outName, areaThFactor, t1Name, t2Name, rasVal, saveNQ):

    # Check that maximum ras membership value is > than user defined membership threshold
    # Get the max value
    maxResult01 = arcpy.GetRasterProperties_management(ras, 'MAXIMUM')
    max01 = float(maxResult01.getOutput(0))
    # If max is greater:
    if max01 > config.memTh:

        # Calculate area threshold
        # as area threshold factor * intergrated bankfull width
        areaTh = float(areaThFactor * config.intBFW)
        # Set all cells above/below membership threshold to 1/null
        whereClause = '"VALUE" <= ' + str(config.memTh)
        rThresh = SetNull(ras, 1, whereClause)
        # Calculate area of cells with value of 1
        rArea = ZonalGeometry(rThresh, 'VALUE', 'AREA', cell_size = 0.1)
        maxArea = float(arcpy.GetRasterProperties_management(rArea, 'MAXIMUM').getOutput(0))
        # If area is greater than the area threshold:
        if maxArea > areaTh:
            # Run separate routine for banks
            # Tend to be elongated features, so don't want to apply same 
            # shrink/expand routine
            if t2Name == 'Bank':
                # Group raster by region
                rRegionGrp = RegionGroup(rThresh, 'FOUR')
            else:
                # Shrink and then expand by 1 cell to remove elongate 'pig tail' features
                rShrink = Shrink(rThresh, 1, 1)
                rExpand = Expand(rShrink, 1, 1)
                # Group raster by region
                rRegionGrp = RegionGroup(rExpand, 'FOUR')

            # Calculate area of each region
            rZonalGeometry = ZonalGeometry(rRegionGrp, 'Value', 'AREA', '0.1')
            # Get maximum area value
            maxResult02 = arcpy.GetRasterProperties_management(rZonalGeometry, 'MAXIMUM')
            max02 = float(maxResult02.getOutput(0))
            # Check that maximum area for any region is greater than the area threshold
            # since this could have changed after running shrink/expand routine
            if max02 > areaTh:
                # Remove regions that are less than the threshold area value
                rThresh2 = SetNull(rZonalGeometry, rRegionGrp, '"VALUE" < ' + str(areaTh))
                # Convert to polygon
                tmpPoly = 'tmpPoly.shp'
                arcpy.RasterToPolygon_conversion(rThresh2, tmpPoly, 'NO_SIMPLIFY', 'VALUE')
                # Add Tier 1 and Tier 2 Names to attribute table
                arcpy.AddField_management(tmpPoly, 'Tier1', 'TEXT', 20)
                arcpy.AddField_management(tmpPoly, 'Tier2', 'TEXT', 25)
                arcpy.AddField_management(tmpPoly, 'rasCode', 'SHORT', 2)
                # Populate fields
                fields = ['Tier1', 'Tier2', 'rasCode']
                with arcpy.da.UpdateCursor(tmpPoly, fields) as cursor:
                    for row in cursor:
                        row[0] = t1Name
                        row[1] = t2Name
                        row[2] = rasVal
                        cursor.updateRow(row)
                # Remove any 'holes' less than the area threshold and save output
                outShp = '{}.shp'.format(outName)
                arcpy.EliminatePolygonPart_management(tmpPoly, outShp, 'Area', areaTh, '', 'CONTAINED_ONLY')
                arcpy.Delete_management('tmpPoly.shp')
            # Save non-qualifying units if argument is set to 'TRUE'
            if saveNQ == 'TRUE':
                outShpNQ = '{}_NonQ.shp'.format(outName)
                # Remove regions that are greater than the threshold area value
                outRasNQ = SetNull(rZonalGeometry, 1, '"VALUE" > ' + str(areaTh))
                # Raster to Polygon
                tmpPolyNQ = 'tmpPolyNQ.shp'
                arcpy.RasterToPolygon_conversion(outRasNQ, tmpPolyNQ, 'NO_SIMPLIFY', 'VALUE')
                # Add Tier 1 and Tier 2 Names to attribute table
                arcpy.AddField_management(tmpPolyNQ, 'Tier1', 'TEXT', 20)
                arcpy.AddField_management(tmpPolyNQ, 'Tier2', 'TEXT', 25)
                arcpy.AddField_management(tmpPolyNQ, 'rasCode', 'SHORT', 2)
                # Populate fields
                fields = ['Tier1', 'Tier2', 'rasCode']
                with arcpy.da.UpdateCursor(tmpPolyNQ, fields) as cursor:
                    for row in cursor:
                        row[0] = t1Name
                        row[1] = t2Name
                        row[2] = rasVal
                        cursor.updateRow(row)
                # Remove any 'holes' less than the area threshold and save output
                arcpy.EliminatePolygonPart_management(tmpPolyNQ, outShpNQ, 'Area', areaTh, '', 'CONTAINED_ONLY')
                arcpy.Delete_management('tmpPolyNQ.shp')

            # Output new probability raster, where non-qualifying areas are assigned value of 0.01
            rThresh2 = SetNull(ras, 1, '"VALUE" <=  0.01')

            if t2Name == 'Bank':
                rRegionGrp2 = RegionGroup(rThresh2, 'FOUR')
                rZonalGeometry2 = ZonalGeometry(rRegionGrp2, 'Value', 'AREA', '0.1')
                rThresh3 = SetNull(rZonalGeometry2, 1, '"VALUE" < ' + str(areaTh))
                pRas = Con(IsNull(rThresh3), 0.01, ras)
            else:
                rShrink2 = Shrink(rThresh2, 1, 1)
                rExpand2 = Expand(rShrink2, 1, 1)
                rRegionGrp2 = RegionGroup(rExpand2, 'FOUR')
                rZonalGeometry2 = ZonalGeometry(rRegionGrp2, 'Value', 'AREA', '0.1')
                rThresh3 = SetNull(rZonalGeometry2, 1, '"VALUE" < ' + str(areaTh))
                pRas = Con(IsNull(rThresh3), 0.01, ras)

            pRasOut = ExtractByMask(pRas, ras)
            pRasOut.save('{}2.img'.format(os.path.splitext(ras.name)[0]))

    print('Finished delineating: ' + t2Name)

# -----------------------------------------------------------------------
# Tier 3 Function
#
# -----------------------------------------------------------------------

def Tier3():

    # Create copy
    t2PolyShp = arcpy.ListFiles('*Tier2.shp')[0]
    arcpy.CopyFeatures_management(t2PolyShp, 'tmp_units.shp')
    units = 'tmp_units.shp'

    # Add attribute fields to tier 2 polygon shapefile
    arcpy.AddField_management(units, 'guArea', 'FLOAT')
    arcpy.AddField_management(units, 'guWidth', 'FLOAT')
    arcpy.AddField_management(units, 'guLength', 'FLOAT')
    arcpy.AddField_management(units, 'guPosition', 'TEXT')
    arcpy.AddField_management(units, 'guOrient', 'TEXT')

    print('Computing tier 3 attributes....')

    # Populate area attribute field
    fields = ['SHAPE@Area', 'guArea']
    with arcpy.da.UpdateCursor(units, fields) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    #----------------------------------------------------------
    # Calculate unit position

    print ('...unit position...')

    # Step1: Create channel edge polygon
    # Create copy of bfPoly and wPoly
    bfPoly = 'tmpPoly_bf1.shp'
    wPoly = 'tmpPoly_w1.shp'
    arcpy.CopyFeatures_management(config.bfPolyShp, bfPoly)
    arcpy.CopyFeatures_management(config.wePolyShp, wPoly)
    # Remove small polygon parts from bfPoly and wPoly
    # threshold: < 5% of total area
    bfPolyElim = 'tmpPoly_bf2.shp'
    wPolyElim = 'tmpPoly_w2.shp'
    arcpy.EliminatePolygonPart_management (wPoly, wPolyElim, 'PERCENT', '', 5, 'ANY')
    arcpy.EliminatePolygonPart_management (bfPoly, bfPolyElim, 'PERCENT', '', 5, 'ANY')
    # Erase wPoly from bfPoly
    erasePoly = 'tmpPoly_erase.shp'
    arcpy.Erase_analysis(bfPolyElim, wPolyElim, erasePoly, '')
    # Buffer output by one cell
    # ensures there are no 'breaks' along the banks due to areas
    # where bankfull and wetted extent were the same
    polyBuffer = 'tmpPoly_buffer.shp'
    arcpy.Buffer_analysis(erasePoly, polyBuffer, 0.1, 'FULL')
    edgePoly = 'tmpPoly_edge.shp'
    arcpy.Clip_analysis(polyBuffer, bfPolyElim, edgePoly)
    # Split multipart edge polgyons into single part polygons
    edgePolySplit = 'tmpPoly_edge2.shp'
    arcpy.MultipartToSinglepart_management(edgePoly, edgePolySplit)

    # Step2: Assign position to each poly in the units polygon
    # Calculate distance threshold
    dTh = 0.1 * config.intWW
    #  Loop through units
    edge_lyr = 'edge_lyr'
    arcpy.MakeFeatureLayer_management(edgePolySplit, edge_lyr)

    cursor = arcpy.UpdateCursor(units)
    for row in cursor:
        if row.Tier1 == 'In Channel':
            poly = row.Shape
            arcpy.SelectLayerByLocation_management(edge_lyr, 'WITHIN_A_DISTANCE', poly, dTh, 'NEW_SELECTION')
            edgeCount = int(arcpy.GetCount_management(edge_lyr).getOutput(0))
            if edgeCount < 1:
                row.guPosition = 'Mid Channel'
            elif edgeCount >= 2:
                row.guPosition = 'Channel Spanning'
            else:
                row.guPosition = 'Edge Attached'
        else:
            row.guPosition = 'NA'
        cursor.updateRow(row)
    del cursor

    # Delete temporary files
    arcpy.Delete_management(bfPoly)
    arcpy.Delete_management(wPoly)
    arcpy.Delete_management(bfPolyElim)
    arcpy.Delete_management(wPolyElim)
    arcpy.Delete_management(erasePoly)
    arcpy.Delete_management(polyBuffer)
    arcpy.Delete_management(edgePoly)
    arcpy.Delete_management(edgePolySplit)

    #----------------------------------------------------------
    # Calculate unit orientation

    print ('...unit orientation...')

    # Step1: Delete unnecessary fields from xsecs
    # Create copy of xsecs
    xsec = 'tmpPoly_xsec1.shp'
    arcpy.CopyFeatures_management(config.bfXS, xsec)
    # Use ListFields to get a list of field objects
    fieldObjList = arcpy.ListFields(xsec)
    # Create an empty list that will be populated with field names
    fieldNameList = []
    # For each field in the object list, add the field name to the
    #  name list.  If the field is required, exclude it, to prevent errors
    for field in fieldObjList:
        if not field.required:
            fieldNameList.append(field.name)
    # dBASE tables require a field other than an OID and Shape.  If this is
    # the case, retain an extra field (the first one in the original list)
    desc = arcpy.Describe(xsec)
    if desc.dataType in ['ShapeFile', 'DbaseTable']:
        fieldNameList = fieldNameList[1:]
    # Execute DeleteField to delete all fields in the field list.
    xsec2 = arcpy.DeleteField_management(xsec, fieldNameList)

    # Step2: Clip xsec to unit poly
    # Clip xsec to unit polys
    xsec_clip = 'tmpPoly_xsec_clip.shp'
    arcpy.Intersect_analysis([xsec2, units], xsec_clip, 'ONLY_FID')
    # Split multipart xsecs into single part xsecs
    xsec_split = 'tmpPoly_xsec_split.shp'
    arcpy.MultipartToSinglepart_management(xsec_clip, xsec_split)

    # Step3: Calculate unit length, width
    # Add length field to attribute table
    arcpy.AddField_management(xsec_split, 'guWidth', 'FLOAT', '7', '3')
    # Calculate xsec length
    fields = ['SHAPE@LENGTH', 'guWidth']
    with arcpy.da.UpdateCursor(xsec_split, fields) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)
    # Delete 'tiny' segments
    # ....if end up using mean xsec length in unit length cal,
    # these small segments won't skew the results.
    with arcpy.da.UpdateCursor(xsec_split, 'guWidth') as cursor:
        for row in cursor:
            if row[0] < 0.1:
                cursor.deleteRow()
    # Attribute max xsec length to each polygon
    # Spatial join
    # Create a new fieldmappings and add the input feature classes
    fieldmappings = arcpy.FieldMappings()
    fieldmappings.addTable(xsec_split)
    fieldmappings.addTable(units)
    # Get the guWidth fieldmap
    guWidthFieldIndex = fieldmappings.findFieldMapIndex('guWidth')
    fieldmap = fieldmappings.getFieldMap(guWidthFieldIndex)
    # Set the merge rule to mean and then replace the old fieldmap in the mappings object
    # with the updated one
    fieldmap.mergeRule = 'maximum'
    fieldmappings.replaceFieldMap(guWidthFieldIndex, fieldmap)
    #Run the Spatial Join tool, using the defaults for the join operation and join type
    units_join = 'tmp_units_join.shp'
    arcpy.SpatialJoin_analysis(units, xsec_split, units_join, '#', '#', fieldmappings, 'CONTAINS')
    # Calculate  guLength, gu Width
    fields = ['Tier1', 'guWidth', 'guArea', 'guLength']
    with arcpy.da.UpdateCursor(units_join, fields) as cursor:
        for row in cursor:
            if row[0] == 'In Channel':
                if row[1] > 0.0:
                    row[3] = row[2]/row[1]
            else:
                row[3] = -9999
            cursor.updateRow(row)

    # Step4: Assign orientation
    fields = ['Tier1', 'guWidth', 'guLength', 'guOrient']
    with arcpy.da.UpdateCursor(units_join, fields) as cursor:
        for row in cursor:
            if row[0] == 'In Channel':
                if row[1] > 0.0:
                    if row[1]/row[2] > 1.0:
                        row[3] = 'Transverse'
                    else:
                        row[3] = 'Streamwise'
                else:
                    row[3] = 'NA'
            else:
                row[3] = 'NA'
            cursor.updateRow(row)

    # Delete temporary files
    arcpy.Delete_management(xsec)
    arcpy.Delete_management(xsec_clip)
    arcpy.Delete_management(xsec_split)
    arcpy.Delete_management(units)

    #----------------------------------------------------------
    # Attribute forcing

    print ('...forcing elements...')

    # Step1: Attribute forcing elements to CHaMP channel unit polygons
    # Convert cover csvs to dbfs
    arcpy.TableToTable_conversion(config.champLW, env.workspace, 'tbl_lwd.dbf')
    arcpy.TableToTable_conversion(config.champSubstrate, env.workspace, 'tbl_cover.dbf')
    # Summarise wood data (i.e., sum dry and wet wood)
    if 'DEBRIS' in str(config.champLW):
        arcpy.Statistics_analysis('tbl_lwd.dbf', 'tbl_lwd_sum.dbf', [['SumLWDCoun', 'SUM']], 'ChannelU_1')
        arcpy.AddField_management('tbl_lwd_sum.dbf', 'lwdCount', 'SHORT')
        arcpy.CalculateField_management('tbl_lwd_sum.dbf', 'lwdCount', '[SUM_SumLWD]')
    if 'PIECE' in str(config.champLW):
        arcpy.Frequency_analysis('tbl_lwd.dbf', 'tbl_lwd_sum.dbf', 'ChannelU_1')
        arcpy.AddField_management('tbl_lwd_sum.dbf', 'lwdCount', 'SHORT')
        arcpy.CalculateField_management('tbl_lwd_sum.dbf', 'lwdCount', '[FREQUENCY]')
    # Join aux csv data to CHaMP channel unit shapefile
    arcpy.CopyFeatures_management(config.champUnits, 'tmp_champUnits.shp')
    tmp_cus = 'tmp_champUnits.shp'
    arcpy.JoinField_management(tmp_cus, 'Unit_Numbe', 'tbl_cover.dbf', 'ChannelU_1', 'BouldersGT')
    arcpy.JoinField_management(tmp_cus, 'Unit_Numbe', 'tbl_lwd_sum.dbf', 'ChannelU_1', 'lwdCount')
 
    # Step2: Spatial join with GUT tier 3 unit shapefile 
    # Create a new fieldmappings and add the input feature classes
    fieldmappings = arcpy.FieldMappings()
    fieldmappings.addTable(units_join)
    fieldmappings.addTable(tmp_cus)
    # Get the fieldmap for BouldersGT and lwdCount fields
    bldFieldIndex = fieldmappings.findFieldMapIndex('BouldersGT')
    fieldmap1 = fieldmappings.getFieldMap(bldFieldIndex)
    lwdFieldIndex = fieldmappings.findFieldMapIndex('lwdCount')
    fieldmap2 = fieldmappings.getFieldMap(lwdFieldIndex)
    # Set the merge rule to sum and then replace the old fieldmap in the mappings object
    # with the updated ones
    fieldmap1.mergeRule = 'sum'
    fieldmappings.replaceFieldMap(bldFieldIndex, fieldmap1)
    fieldmap2.mergeRule = 'sum'
    fieldmappings.replaceFieldMap(lwdFieldIndex, fieldmap2)
    # Run the Spatial Join tool, using the defaults for the join operation and join type
    units_join2 = 'tmp_units_join2.shp'
    arcpy.SpatialJoin_analysis(units_join, tmp_cus, units_join2, '#', '#', fieldmappings, 'INTERSECT')
    # Change field name from 'BouldersGT' to 'pBLD'
    # Add new field
    arcpy.AddField_management(units_join2, 'pBoulder', 'SHORT')
    # Calculate field
    arcpy.CalculateField_management(units_join2, 'pBoulder', '[BouldersGT]')

    # Delete temporary files
    arcpy.Delete_management('tmp_units_join.shp')
    arcpy.Delete_management('tbl_cover.dbf')
    arcpy.Delete_management('tbl_lwd.dbf')
    arcpy.Delete_management('tbl_lwd_sum.dbf')

    #----------------------------------------------------------
    # Attribute low flow roughness

    print ('...low flow relative roughness...')

    # Step1: Attribute D84 to CHaMP channel unit polygons
    # Convert grain size csv to dbf table
    arcpy.TableToTable_conversion(config.champGrainSize, env.workspace, 'tbl_d84.dbf')
    # Join aux D84 value to CHaMP channel unit shapefile
    arcpy.JoinField_management(tmp_cus, 'Unit_Numbe', 'tbl_d84.dbf', 'ChannelU_1', 'D84')
    # Make sure D84 field is float
    # (Arc Issue that converts field to type integer if first element is integer)
    arcpy.AddField_management(tmp_cus, 'D84_float', 'FLOAT')
    fields = ['D84', 'D84_float']
    with arcpy.da.UpdateCursor(tmp_cus, fields) as cursor:
        for row in cursor:
            row[1] = float(row[0])
            cursor.updateRow(row)   
    # Convert to D84 raster
    arcpy.FeatureToRaster_conversion(tmp_cus, 'D84_float', 'd84.img', 0.1)
    # Step2: Calculate low flow relative roughness raster
    # Read in water depth raster
    wd = Raster(config.inWaterD)
    # In low flow relative roughness calculation, convert d84 (in mm) to m
    lfr = (Raster('d84.img')/1000)/wd
    # Save the output
    lfr.save('lowFlowRoughess.img')
    # Step3: Assign mean low flow relative roughness value to GUT tier 3 unit shapefiles
    # Get mean value for each tier 3 polygon
    ZonalStatisticsAsTable(units_join2, 'FID', lfr, 'tbl_lfr', 'DATA', 'MEAN')
    # Join mean value table to unit shapefile
    arcpy.JoinField_management(units_join2, 'FID', 'tbl_lfr.dbf', 'FID', 'MEAN')
    # Change field name from 'MEAN' to 'LFRR'
    # Add new field
    arcpy.AddField_management(units_join2, 'LFRR', 'FLOAT')
    # Calculate field
    arcpy.CalculateField_management(units_join2, 'LFRR', '[MEAN]')
    # Delete unnecessary files
    arcpy.Delete_management(tmp_cus)
    arcpy.Delete_management('tbl_d84.dbf')

    #----------------------------------------------------------
    # Attribute bankfull surface slope

    print ('...surface slope.')

    # Step1: Calculate low flow relative roughness raster
    # Read in mean bankfull surface slope raster
    bfeSlope = Raster('bfeSlope_meanBFW.img')
    # Step2: Assign mean bankfull surface slope raster to GUT tier 3 unit shapefiles
    # Get mean value for each tier 3 polygon
    ZonalStatisticsAsTable(units_join2, 'FID', bfeSlope, 'tbl_bfeSlope', 'DATA', 'MEAN')
    # Join mean value table to unit shapefile
    arcpy.JoinField_management(units_join2, 'FID', 'tbl_bfeSlope.dbf', 'FID', 'MEAN')
    # Change field name from 'MEAN' to 'bfeSlope'
    # Add new field
    arcpy.AddField_management(units_join2, 'bfeSlope', 'FLOAT')
    # Calculate field
    arcpy.CalculateField_management(units_join2, 'bfeSlope', '[MEAN]')

    #----------------------------------------------------------  
    # Clean up shapefile 

    print 'Cleaning up attribute table and creating transition zones...'

    # Step1: Keep only required or necessary fields
    # Create list of current fields
    fieldList = arcpy.ListFields(units_join2)
    # Create an empty list that will be populated with field names to delete
    dropList = []
    # Create list of field names to keep
    keepList = ['GRIDCODE', 'Tier1', 'Tier2', 'rasCode', 'guArea', 'guLength',
    'guWidth', 'guPosition', 'guOrient', 'pBoulder', 'lwdCount', 'LFRR', 'bfeSlope']
    # For each field in the object list, add the field name to the
    #  drop list, if it is not in the keep list
    for field in fieldList:
        if not field.required and field.name not in keepList:
            dropList.append(field.name)
    # Execute DeleteField to delete all fields in the field list.
    arcpy.DeleteField_management(units_join2, dropList)  

    # Step2: Add transition zones
    rasDomain = 'rasDomain.shp'
    tranShp = 'tranShp.shp'
    tranShpIn = 'tranShpIn.shp'
    tranShpOut = 'tranShpOut.shp'
    # Create single polygon from detrended DEM
    arcpy.RasterDomain_3d(Raster(config.inDet), rasDomain, 'POLYGON')
    # Create transition zone shp by clipping out classified polygons
    arcpy.Erase_analysis(rasDomain, units_join2, tranShp)
    # Get list of attribute fields from tier 3 units shp and add to transition shp
    fieldList = arcpy.ListFields(units_join2)
    for field in fieldList:
        if field.name != 'FID' and field.name != 'Shape':
            arcpy.AddField_management(tranShp, field.name, field.type)
    # Set attribute field values
    fields = ['Tier2', 'guWidth', 'guLength', 'guPosition', 'guOrient', 'lwdCount', 'pBoulder', 'LFRR', 'bfeSlope']
    with arcpy.da.UpdateCursor(tranShp, fields) as cursor:
        for row in cursor:
            row[0] = 'Transition'
            row[1] = -9999
            row[2] = -9999
            row[3] = 'NA'
            row[4] = 'NA'  
            row[5] = -9999
            row[6] = -9999
            row[7] = -9999
            row[8] = -9999
            cursor.updateRow(row)   
    # Differentiate in-channel transitions from out-of-channel transitions
    arcpy.Erase_analysis(tranShp, config.bfPolyShp, tranShpOut)
    arcpy.Clip_analysis(tranShp, config.bfPolyShp, tranShpIn)
    # Assign Tier 1 and rasCode to in-channel and out-of-channel transitions
    fields = ['Tier1','rasCode', 'SHAPE@Area', 'guArea']
    with arcpy.da.UpdateCursor(tranShpIn, fields) as cursor:
        for row in cursor:
            row[0] = 'In Channel'
            row[1] = 10
            row[3] = row[2]
            cursor.updateRow(row)
    with arcpy.da.UpdateCursor(tranShpOut, fields) as cursor:
        for row in cursor:
            row[0] = 'Out of Channel'
            row[1] = 11
            row[3] = row[2]
            cursor.updateRow(row)
    units_merge = 'tmp_units_merge.shp'
    arcpy.Merge_management([units_join2, tranShpIn, tranShpOut], units_merge)
    # Delete unnecessary files
    arcpy.Delete_management(units_join2)
    arcpy.Delete_management(tranShp)
    arcpy.Delete_management(tranShpIn)
    arcpy.Delete_management(tranShpOut)
    arcpy.Delete_management(rasDomain)

    # Step3: Update attribute fields so non in-channel units have NULL boulders, lwd, lfr values
    fields = ['Tier1', 'pBoulder', 'lwdCount', 'LFRR', 'guWidth', 'bfeSlope']
    with arcpy.da.UpdateCursor(units_merge, fields) as cursor:
        for row in cursor:
            if row[0] != 'In Channel':
                row[1] = -9999
                row[2] = -9999
                row[3] = -9999
                row[4] = -9999
                row[5] = -9999               
            cursor.updateRow(row)   

    #----------------------------------------------------------  
    # Apply tier 3 logic 

    print 'Applying tier 3 logic to in-channel units...'

    # Add tier 3 attribute field
    arcpy.AddField_management(units_merge, 'Tier3', 'TEXT', 150)
    # Apply tier 3 logic based on attribute fields
    fields = ['Tier1', 'Tier2', 'Tier3', 'LFRR', 'bfeSlope', 'guOrient', 'lwdCount', 'pBoulder', 'guPosition']
    with arcpy.da.UpdateCursor(units_merge, fields) as cursor:
        for row in cursor:
            if row[0] != 'In Channel':
                row[2] = 'NA'
            if row[1] == 'Planar-RunGlide':
                if row[3] < 0.5:
                    row[2] = 'Glide'
                else:
                    row[2] = 'Run'
            if row[1] == 'Planar-RapidCascade':
                if row[4] < 4.0:
                    row[2] = 'Rapid'
                else:
                    row[2] = 'Cascade'                
            if row[1] == 'Concavity':
                if row[5] == 'Transverse':
                    row[2] = 'Plunge pool'
                else:
                    if row[6] > 0 or row[7] > 0:
                        row[2] = 'Structurally forced pool'
                    else:
                        if row[8] == 'Channel Spanning':
                            row[2] = 'Beaver Pond; Confluence Pool; Dammed Pool'
                        elif row[8] == 'Edge Attached':
                            row[2] = 'Bar-forced Pool; Chute; Confluence Pool; Return Channel; Shallow Thalweg'
                        else:
                            row[2] = 'Chute; Confluence Pool; Secondary Channel'
            if row[1] == 'Convexity':
                if row[8] == 'Channel Spanning':
                    row[2] = 'Backwater bar; Compound bar; Forced riffle; Riffle; Unit bar'
                else:
                    if row[5] == 'Streamwise':
                        if row[8] == 'Mid Channel':
                            row[2] = 'Backwater bar; Boulder bar; Compound bar; Diagonal bar; Eddy bar; Expansion bar; Forced bar; Lobate bar; Longitudinal bar; Unit bar'
                        else:
                            row[2] = 'Backwater bar; Boulder bar; Compound bar; Confluence bar; Eddy bar; Forced bar; Lateral bar; Point bar; Reattachment bar; Ridge; Scroll bar; Unit bar'
                    else:
                        if row[8] == 'Mid Channel':
                            row[2] = 'Backwater bar; Compound bar; Expansion bar; Unit bar'
                        else:
                            row[2] = 'Backwater bar; Compound bar; Unit bar'    
    
            cursor.updateRow(row)
    # Save output
    arcpy.CopyFeatures_management(units_merge, '{}_Tier3.shp'.format(config.siteName))
    # Delete unnecessary files
    arcpy.Delete_management(units_merge)
    
# -----------------------------------------------------------------------
# Geomorphic Unit Merge Function
# -----------------------------------------------------------------------

def guMerge():

    print('Merging units....')

    # Create output raster/shapefile names
    outshp = '{}_Tier2.shp'.format(config.siteName)
    # Create empty list
    shpList = []
    # Search workspace folder for all polygon shapefiles that match searchName
    # Add to list
    for root, dir, files in os.walk(arcpy.env.workspace):
        for f in files:
            shpList = arcpy.ListFeatureClasses('t2*', 'Polygon')
    # Remove any shapefiles that have 'NonQ', 'check', or 'Mem'
    for shp in shpList:
        if 'NonQ.shp' in shp:
            shpList.remove(shp)
        if 'check' in shp:
            shpList.remove(shp)
        if 'Mem' in shp:
            shpList.remove(shp)

    # Merge all shapefiles in list
    arcpy.Merge_management(shpList, outshp)

# -----------------------------------------------------------------------
# Slope Line Equation Function
# -----------------------------------------------------------------------

def lineEq(y1, y2, x1, x2):

    m = (y1 - y2) / (x1 - x2)
    b = (y1) - (m * x1)

    return m, b
