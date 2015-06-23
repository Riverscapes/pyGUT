# Geomorphic Unit Functions

# Last updated: 5/28/2015
# Created by: Sara Bangen (sara.bangen@gmail.com)

# Changes:
#       v23:
#       - Uses version 21 of inverse fill but with only a single fill
#       - Uses unsmooted DEM and detDEM as inputs
#       - Removed routine for isolating riffles in guMerge function since only using single fill
#       v22:
#       - Went back to previous method of calculting inverse fill
#       v21:
#       - Changed order of shrink and expand to directly follow ea other
#       - Removed mean slope (now using smoothed raster)
#       - Mean bankfull slope for planar features rather than mean slope
#       - Normalized inverse fill calculation:
#               - 2 'fills' instead of using buffer and single fill
#               - outputs inverse fill with values [1, 2] where 1 are from first fill, 2 are from second fill
#		v20:
#       - Convexity inverse fill threshold from > 0.05 to > 0.0
#		- Inverse membership calculation so that area threshold + shrink/expand is used
#       - Changed rapid-cascade euclidean distance:
#               - distance from non-qualifying and qualifying pools (not just nq)
#               - changed distance from [0.5, 0.55] to [0.5, 0.75]
#       v18:
#       - Cleaned up code
#       - Added config.py file
#       v17:
#       - Added tranform functions back in (per JM)
#       v16:
#       - Re-vamp of out of channel units
#           - Got rid of 'relief'
#           - Now simply using slope and normalized height above detrended bankfull
#		v 15:
#	   - added cascade/rapid planar unit function
#		v 14:
#	   - changed guThresh fn so area calculations are now done on raster (previsously
#		 converted raster to polygon, then calculated area, and then converted back to raster)
#       v13:
#	   - Increased planar normBFDepth upper threshold back up to 0.6
#	   - Decreased conexity normBFDepth upper threshold to 0.4
#      - Increased area threshold for concavities to 0.5 * intBFW (previously 0.25)
#       v12:
#	   - Increased area threshold for convexities and planar features to 0.5 * intBFW (previously 0.25)
#	   - Decreased planar normBFDepth upper threshold to 0.5
#	   - Increased convexity normBFDepth upper threshold to 0.5
#       v11:
#	   - Total re-vamp based on fuzzy cluster analysis
#      - Got rid of transform functions; now simply using binary [0,1] functions
#       Previous versions:
#      - Edited inverse fill evidence raster function so that the bankfull polygon
#        'holes' aren't filled
#      - Added bankfull distance evidence raster
#      - Added cutbanks to Tier 2 out of channel units
#      - Added fans to out of channel units (crude, needs development)
#      - Turned off long curvature
#      - Normalized convexity thresholds [(0.05, 0.01), (0.1, 0.99)]
#      - Changed inverse fill buffers from (-0.2, 0.2) to (-0.3, 0.1)

import arcpy, numpy, os, config
from arcpy import env
from arcpy.sa import *

# -----------------------------------------------------------------------
#  In Channel Evidence Rasters
#
#
# Input parameters
# dem:               DEM name, including suffix
# det:                 Detrended DEM name, including suffix
# bfPoints:       Bankfull points shapefile name, including suffix
# bfPolyShp:    Bankfull polygon shapfiled name, including suffix
# wePolyShp:  Height above bankfull raster name, including suffix
# intWW:          Integrated wetted width (m; floating point)
# hadBF:           Height above detrended bankfull elevation raster name, including suffix
# fwSlope:        Focal window (i.e., neighborhood) for mean slope calculation
# -----------------------------------------------------------------------


def bfPoly(det, bfPolyShp):
    tmp_bfPoly = 'tmp_bfPoly.img'
    arcpy.PolygonToRaster_conversion(bfPolyShp, 'ID', tmp_bfPoly,
                                     'CELL_CENTER')
    outCon = Con(IsNull(tmp_bfPoly), 0, 1)
    outRas = ExtractByMask(outCon, det)
    outRas.save('bfPoly.img')
    arcpy.Delete_management('tmp_bfPoly.img')


def normMeanSlope(det, fwSlope):
    # Calculate detrended slope raster
    detSlope = Slope(det, 'DEGREE')

    # Calculate mean slope over 1x1 m window
    neighborhood = NbrRectangle(fwSlope, fwSlope, 'MAP')
    meanSlope = FocalStatistics(detSlope, neighborhood, 'MEAN', 'DATA')
    outMeanSlope = ExtractByMask(meanSlope, det)
    outMeanSlope.save('meanSlope.img')

    # Normalize by 90 (i.e., max possible degree slope)
    normMeanSlope = outMeanSlope / 90.0
    normMeanSlope.save('normMeanSlope.img')


def normConcavity(dem, bfPolyShp):
    rFill = Fill(dem)
    rRas = (rFill - dem)
    rCon = Con(IsNull(rRas), 0, rRas)
    outConcavity = ExtractByMask(rCon, bfPolyShp)
    outConcavity.save("Concavity.img")
    outConcavityMaxResult = arcpy.GetRasterProperties_management(outConcavity, "MAXIMUM")
    outConcavityMax = float(outConcavityMaxResult.getOutput(0))
    normConcavity = (outConcavity / float(outConcavityMax))
    normConcavity.save('normConcavity.img')


def normBFDepth(hadBF):
    bfD = Abs(SetNull(hadBF, hadBF, '"VALUE" > 0'))
    bfDMaxResult = arcpy.GetRasterProperties_management(bfD, "MAXIMUM")
    bfDMax = float(bfDMaxResult.getOutput(0))
    normBFD = (bfD / float(bfDMax))
    bfD.save('bfDepth.img')
    normBFD.save('normBFDepth.img')


def normInverseFill(det, bfPoly):
    # Reclassify bfPoly raster
    rBF = Reclassify(bfPoly, 'VALUE', RemapValue([[1, -1], [0, 1]]))

    # Fill routine 1:
    # Get inverse det DEM for in-channel cells
    invDet = rBF * det

    # Fill and get difference
    rFill = Fill(invDet)
    rDiff = rFill - invDet

    # Save the inverse fill raster
    rDiff.save('invFill.img')

    # Get Raster Properties
    inverseFillResult = arcpy.GetRasterProperties_management(rDiff, "MAXIMUM")
    inverseFillMax = float(inverseFillResult.getOutput(0))

    normInvFill = rDiff / inverseFillMax
    normInvFill.save('normInvFill.img')

def chMargin(bfPolyShp, wePolyShp, intWW):
    # Remove any wePoly parts < 5% of total area
    wePolyElim = 'wePolyElim.shp'
    arcpy.EliminatePolygonPart_management(wePolyShp, wePolyElim,
                                          'PERCENT', '', 5, 'ANY')                                                                                                                         
    # Erase polyElim
    polyErase = 'polyErase.shp'
    arcpy.Erase_analysis(bfPolyShp, wePolyElim, polyErase, "")
    # Buffer
    polyBuffer = 'polyBuffer.shp'
    bufferDist = 0.1 * intWW
    arcpy.Buffer_analysis(polyErase, polyBuffer, bufferDist, 'FULL')
    # Clip
    polyClip = 'polyClip.shp'
    arcpy.Clip_analysis(polyBuffer, bfPolyShp, polyClip)
    # Process: Polygon to Raster
    arcpy.PolygonToRaster_conversion(polyClip, 'FID', 'outRas.img',
                                     'CELL_CENTER', 'NONE', '0.1')
    # Process: Raster Calculator
    chMargin = Con(IsNull('outRas.img'), 0, 1)
    # Save the inverse fill raster
    chMargin.save('chMargin.img')

    # Delete intermediate shapefiles and rasters
    arcpy.Delete_management('wePolyElim.shp')
    arcpy.Delete_management('polyErase.shp')
    arcpy.Delete_management('polyBuffer.shp')
    arcpy.Delete_management('polyClip.shp')
    arcpy.Delete_management('outRas.img')


def bfSlope(cm, meanSlope, bfPoly):
    # Essentially mean slope within bankfull channel with banks 
    # removed (to reduce bank edge effects)
    # Subset slope raster
    # Set high sloping areas with channel margin to null
    # otherwise will bias focal window calc
    slope_th01 = SetNull((meanSlope * cm), 1, '"VALUE" >= 25')
    # Subset  slope raster:
    # Get slope within bf channel and slope_th01
    slope_th02 = slope_th01 * meanSlope * bfPoly
    slope_th03 = SetNull(slope_th01, slope_th02, '"VALUE" = 0')
    rclass_sl = Con(slope_th03 > 0, 1)
    # Get largest contingent area
    # Ensures won't include smaller channel margin cells in focal calc
    reGroup01 = RegionGroup(rclass_sl, "FOUR", "WITHIN")
    zonalGeom01 = ZonalGeometry(reGroup01, "Value", "Area", "0.1")
    maxResult01 = arcpy.GetRasterProperties_management(zonalGeom01, "MAXIMUM")
    whereClause = "Value < " + str(float(maxResult01.getOutput(0)))
    zonal_th = SetNull(zonalGeom01, slope_th03, whereClause)
    #  Calculate mean slope over bfw neighborhood
    neighborhood = NbrRectangle(config.intBFW, config.intBFW, "MAP")
    slope_focal = FocalStatistics(zonal_th, neighborhood, "MEAN")
    meanBFSlope = ExtractByMask(slope_focal, zonal_th)
    meanBFSlope.save("detSlopeMean_BFW.img")


def detSD(det, meanBFSlope):
    # Essentially detrended DEM SD within bankfull channel with banks removed 
    # (to reduce bank edge effects)
    # Clip down detrededed DEM
    # Ensures won't include high sloping channel margsin cells in focal calc
    det_extract01 = ExtractByMask(det, meanBFSlope)
    # Calculate detrended DEM sd over bfw neighborhood
    neighborhood = NbrRectangle(config.intBFW, config.intBFW, "MAP")
    det_focal = FocalStatistics(det_extract01, neighborhood, "STD")
    det_extract02 = ExtractByMask(det_focal, det_extract01)
    maxResult02 = arcpy.GetRasterProperties_management(det_extract02, "MAXIMUM")
    max02 = float(maxResult02.getOutput(0))
    normDetSD = det_extract02 / max02
    normDetSD.save("detSD_BFW_norm.img")

# -----------------------------------------------------------------------
# Out of Channel Evidence Rasters
#
# Input parameters
#
# workspace:   workingfolder
# det:         Detrended DEM name, including suffix.
# bfPoints:    Bankfull point shapefile name, including suffix
# bfPolyShape: Bankfull polygon shapefile name, including suffix
# bfDepth:     bfDepth raster
# bfPoly:      bfPolygon raster
# fwRelief:  Focal window (in meters) for detDEM relief calculation.
#	         Note: MUST be odd number (e.g. 3.1)
# -----------------------------------------------------------------------


def HADBF(det, bfPoints):
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
    hadBF = det - zMean
    hadBF.save('HADBF.img')

    arcpy.Delete_management('tmp_bfPoints.shp')


def normHADBF(HADBF, bfDepth):

    # Get mean bfDepth value
    maxResult = arcpy.GetRasterProperties_management(bfDepth, "MAXIMUM")
    max = float(maxResult.getOutput(0))

    # Calculate normalized hadBF raster
    HADBF_norm = HADBF / max
    HADBF_norm.save('normHADBF.img')


def detSlope(det):

#   Calculate detrended slope raster
    detSlope = Slope(det, 'DEGREE')
    detSlope.save('detSlope.img')


def bfDist(bfPolyShp, det):

    # Calculate bankfull distance
    rawDist = EucDistance(bfPolyShp)
    outDist = ExtractByMask(rawDist, det)
    outDist.save('bfDist.img')


def detRelief(det, bfPoly, fwRelief):

    # Calculate detrended relief raster
    neighborhood = NbrRectangle(fwRelief, fwRelief, 'MAP')
    # Clip to just area outside bankfull
    tmp_det = SetNull(bfPoly, det, '"VALUE" = 1')
    Relief = FocalStatistics(tmp_det, neighborhood, 'RANGE', 'DATA')
    outRelief = ExtractByMask(Relief, tmp_det)
    outRelief.save('detRelief.img')

# -----------------------------------------------------------------------
# Out of Channel Transform Functions
#
# Input parameters
#
# bfPoly:     	 Bankfull polygon raster name, including suffix
# normHADBF: 	 Height above bankfull raster name, including suffix
# meanSlope:     Mean detrended slope raster name, including suffix
# Relief:        Detrended relief raster name, including suffix
# lowHADBF: 	 Lower normalized HADBF threshold
# upHADBF:  	 Upper normalized HADBF threshold
# lowSlope:  	 Lower slope threshold
# upSlope:   	 Upper slope threshold
# lowBFDist:     Lower bankfull distance threshold
# upBFDist: 	 Upper bankfull distance threshold
# lowRelief:     Lower relief threshold
# upRelief: 	 Upper relief threshold
# -----------------------------------------------------------------------


def afpTFs(bfPoly, meanSlope, normHADBF, Relief):

    # Calculate transform function line slope + intercept
    sl_le = lineEq(0.99, 0.01, config.lowSlope, config.upSlope)
    hadbf_le = lineEq(0.99, 0.01, config.lowHADBF, config.upHADBF)
    r_le = lineEq(0.99, 0.01, config.lowRelief, config.upRelief)

    # Execute Conditional Statements
    bf_fn = Con(bfPoly == 0, 0.99, 0.01)
    sl_fn = Con(meanSlope <= config.lowSlope, 0.99, Con(meanSlope >= config.upSlope, 0.01, meanSlope * sl_le[0] + sl_le[1]))
    hadbf_fn = Con(normHADBF <= config.lowHADBF, 0.99, Con(normHADBF >= config.upHADBF, 0.01, normHADBF * hadbf_le[0] + hadbf_le[1]))
    r_fn = Con(Relief <= config.lowRelief, 0.99, Con(Relief >= config.upRelief, 0.01, Relief * r_le[0] + r_le[1]))

    # Calculate floodplain output
    outAFP = (bf_fn * sl_fn * hadbf_fn * r_fn)
    outAFP.save('t2AFloodplain_Mem.img')

    guThreshAttr(outAFP, 't2Floodplain', 1.0, 'Out of Channel', 'Active Floodplain', 7, 'FALSE')


def cbTFs(bfPoly, meanSlope, bfDist):

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

    guThreshAttr(outCB, 't2Cutbank', 0.1, 'Out of Channel', 'Cutbank', 6, 'FALSE')


def hsTFs(bfPoly, meanSlope, bfDist, Relief):

    # Calculate transform function line slope + intercept
    sl_le = lineEq(0.01, 0.99, config.lowSlope, config.upSlope)
    dist_le = lineEq(0.01, 0.99, config.lowBFDist, config.upBFDist)
    r_le = lineEq(0.01, 0.99, config.lowRelief, config.upRelief)

    # Execute Conditional Statements
    bf_fn = Con(bfPoly == 0, 0.99, 0.01)
    slope_fn = Con(meanSlope >= config.upSlope, 0.99, Con(meanSlope <= config.lowSlope, 0.01, meanSlope * sl_le[0] + sl_le[1]))
    dist_fn = Con(bfDist >= config.upBFDist, 0.99, Con(bfDist <= config.lowBFDist, 0.01, bfDist * dist_le[0] + dist_le[1]))
    r_fn = Con(Relief >= config.upRelief, 0.99, Con(Relief <= config.lowRelief, 0.01, Relief * r_le[0] + r_le[1]))

    # Calculate hillslope output
    outHS = (bf_fn * slope_fn * dist_fn * r_fn)
    outHS.save('t2HillslopeFan_Mem.img')

    guThreshAttr(outHS, 't2HillslopeFan', 1.0, 'Out of Channel', 'Hillslope/Fan', 8, 'FALSE')


def ifpTFs(bfPoly, meanSlope, normHADBF, Relief):

    # Calculate transform function line slope + intercept
    sl_le = lineEq(0.99, 0.01, config.lowSlope, config.upSlope)
    hadbf_le = lineEq(0.01, 0.99, config.lowHADBF, config.upHADBF)
    r_le = lineEq(0.99, 0.01, config.lowRelief, config.upRelief)

    # Execute Conditional Statements
    bf_fn = Con(bfPoly == 0, 0.99, 0.01)
    sl_fn = Con(meanSlope <= config.lowSlope, 0.99, Con(meanSlope >= config.upSlope, 0.01, meanSlope * sl_le[0] + sl_le[1]))
    hadbf_fn = Con(normHADBF <= config.lowHADBF, 0.01, Con(normHADBF >= config.upHADBF, 0.99, normHADBF * hadbf_le[0] + hadbf_le[1]))
    r_fn = Con(Relief <= config.lowRelief, 0.99, Con(Relief >= config.upRelief, 0.01, Relief * r_le[0] + r_le[1]))

    # Calculate terrace output
    outIFP = (bf_fn * sl_fn * hadbf_fn * r_fn)
    outIFP.save('t2Terrace_Mem.img')

    guThreshAttr(outIFP, 't2Terrace', 1.0, 'Out of Channel', 'Terrace', 9, 'FALSE')

# -----------------------------------------------------------------------
# In Channel Transform Functions
#
# Input parameters
#
# workspace:  workingfolder
# bfPoly:   Bankfull polygon raster name, including suffix
# normBFDepth: Normalized bankfull depth raster
# hadBF:    Height above bankfull raster name, including suffix
# relief:   Detrended relief raster name, including suffix
# slope:    Detrended slope raster name, including suffix
# lowBFSlope: Mean detrended bankfull slope - lower threshold
# upBFSlope: Mean detrended bankfull slope - upper threshold
# low.hadBF:  Height above bankfull raster - lower threshold
# up.hadBF:   Height above bankfull raster - upper threshold
# low.relief: Detrended relief raster - lower threshold
# up.relief:  Detrended relief raster - upper threshold
# low.slope:  Detrended slope raster - lower threshold
# up.slope:   Detrended slope raster - upper threshold
# -----------------------------------------------------------------------


def concavityTFs(normBFD, bfPoly, nc):

    # Get summary stats for use in transform functions
    sdResult = arcpy.GetRasterProperties_management(normBFD, "STD")
    sd = float(sdResult.getOutput(0))
    meanResult = arcpy.GetRasterProperties_management(normBFD, "MEAN")
    mean = float(meanResult.getOutput(0))

    # Calculate transform function line slope + intercept
    bfD_le = lineEq(0.01, 0.99, mean, (mean + sd))

    # Execute Conditional Statements
    bf_fn = Con(bfPoly == 0, 0.01, 0.99)
    nc_fn = Con(nc > 0, 0.99, 0.01)
    bfD_fn = Con(normBFD <= mean, 0.01, Con(normBFD >= (mean + sd), 0.99, normBFD * bfD_le[0] + bfD_le[1]))

    # Calculate concavity output
    rawCV = (bfD_fn * nc_fn * bf_fn)
    rCV = Con(IsNull(rawCV), 0.01, rawCV)
    outCV = ExtractByMask(rCV, bfPoly)
    outCV.save('t2Concavity_Mem.img')

    guThreshAttr(outCV, 't2Concavity', 0.25, 'In Channel', 'Concavity', 1, 'TRUE')


def chMarginTFs(cm, meanSlope, bfPoly, t2cv):

    # Calculate transform function line slope + intercept
    sl_le = lineEq(0.01, 0.99, config.lowCMSlope, config.upCMSlope)

    # Execute Conditional Statements
    cm_fn = Con(cm == 0, 0.01, 0.99)
    slope_fn = Con(meanSlope <= config.lowCMSlope, 0.01, Con(meanSlope >=  config.upCMSlope, 0.99, meanSlope * sl_le[0] + sl_le[1]))

    inv_cv = Con(IsNull(t2cv), 0.01, t2cv)
    inv_cv2 = 1.0 - inv_cv

    # Calculate channel margin output
    rawCM = (cm_fn * slope_fn * inv_cv2)
    rcCM = Con(IsNull(rawCM), 0.01, rawCM)
    outCM = ExtractByMask(rcCM, bfPoly)
    outCM.save('t2ChMargin_Mem.img')

    guThreshAttr(outCM, 't2ChMargin', 0.05, 'Channel Interface', 'Bank', 5, 'FALSE')


def convexityTFs(bfPoly, nc, normInvF, normBFD, t2cv, t2cm):

    # Calculate transform function line slope + intercept
    normBFD_le = lineEq(0.99, 0.01, 0.4, 0.6)
    nc_le = lineEq(0.99, 0.01, 0, 0.1)

    # Execute Conditional Statements
    bf_fn = Con(bfPoly == 0, 0.01, 0.99)
    nc_fn = Con(nc > 0.1, 0.01, Con(nc <= 0.0, 0.99, nc * nc_le[0] + nc_le[1]))
    invF_fn = Con(normInvF > 0.0, 0.99, 0.01)
    normBFD_fn = Con(normBFD <= 0.4, 0.99, Con(normBFD >= 0.6, 0.01, normBFD * normBFD_le[0] + normBFD_le[1]))

    inv_cv = Con(IsNull(t2cv), 0.01, t2cv)
    inv_cv2 = 1.0 - inv_cv
    inv_cm = Con(IsNull(t2cm), 0.01, t2cm)
    inv_cm2 = 1.0 - inv_cm
    inv_t2 = inv_cv2 * inv_cm2

    # Calculate convexity output
    rawCX = (bf_fn * invF_fn * normBFD_fn * nc_fn * inv_t2)
    outCX = ExtractByMask(rawCX, bfPoly)
    outCX.save('t2Convexity_Mem.img')

    guThreshAttr(outCX, 't2Convexity', 0.5, 'In Channel', 'Convexity', 2, 'FALSE')


def planarTFs(bfPoly, normBFD, meanSlope, normInvF, nc, meanBFSlope, normDetSD, t2cv,  t2cm, t2cx, det, t2cvNQ, t2cvQ):

    bf_fn = Con(bfPoly == 0, 0.01, 0.99)

    # Runs and Glides
    # Calculate transform function line slope + intercept
    normBFD_le = lineEq(0.99, 0.01, 0.6, 0.8)
    sl_le = lineEq(0.99, 0.01, config.lowBFSlope, config.upBFSlope)
    invF_le = lineEq(0.99, 0.01, 0.0, 0.1)
    nc_le = lineEq(0.99, 0.01, 0.0, 0.1)

    # Execute Conditional Statements
    normBFD_fn = Con(normBFD <= 0.6, 0.99, Con(normBFD >= 0.8, 0.01, normBFD * normBFD_le[0] + normBFD_le[1]))
    #meanSlope_fn = Con(meanSlope <= 8.0, 0.99, Con(meanSlope >= 11.0, 0.01, meanSlope * sl_le[0] + sl_le[1]))
    meanSlope_fn = Con(meanBFSlope <= config.lowBFSlope, 0.99, Con(meanBFSlope >= config.upBFSlope, 0.01, meanBFSlope * sl_le[0] + sl_le[1]))
    invF_fn = Con(normInvF > 0.1, 0.01, Con(normInvF <= 0.0, 0.99, normInvF * invF_le[0] + invF_le[1]))
    nc_fn = Con(nc > 0.1, 0.01, Con(nc <= 0.0, 0.99, nc * nc_le[0] + nc_le[1]))

    inv_cv = Con(IsNull(t2cv), 0.01, t2cv)
    inv_cv2 = 1.0 - inv_cv
    inv_cm = Con(IsNull(t2cm), 0.01, t2cm)
    inv_cm2 = 1.0 - inv_cm
    inv_cx = Con(IsNull(t2cx), 0.01, t2cx)
    inv_cx2 = 1.0 - inv_cx
    inv_t2_01 = inv_cv2 * inv_cm2 * inv_cx2

    rawPF_01 = (bf_fn * normBFD_fn * meanSlope_fn * invF_fn * nc_fn * inv_t2_01)
    rcPF_01 = Con(IsNull(rawPF_01), 0.01, rawPF_01)
    outPF_01 = ExtractByMask(rcPF_01, bfPoly)
    outPF_01.save('t2Planar_runglide_Mem.img')

    guThreshAttr(outPF_01, 't2Planar_runglide', 0.5, 'In Channel', 'Planar-RunGlide', 3, 'FALSE')

    # Rapids and cascades

    # Calculate additional evidence raster:
    # euclidean distance from non-qualifying + qualifing pools
    reGroup02 = RegionGroup(t2cvNQ, "FOUR", "WITHIN")
    zonalGeom02 = ZonalGeometry(reGroup02, "Value", "Area", "0.1")
    area_th = Con(zonalGeom02 > 0.1, 1)
    mosaicRas = arcpy.MosaicToNewRaster_management(input_rasters = [area_th, t2cvQ],
                                                   output_location = config.workspace,
                                                   raster_dataset_name_with_extension = 'tmp_mosaicRas.img',
                                                   number_of_bands = 1)
    eucDist = EucDistance(mosaicRas, "", "0.1")
    eucDist_extract = ExtractByMask(eucDist, normBFD)
    eucDist_norm = eucDist_extract / config.intBFW
    eucDist_norm.save("eucDist_nqCV_norm.img")
    arcpy.Delete_management('tmp_mosaicRas.img')

    # Calculate transform function line slope + intercept
    bfsl_le = lineEq(0.01, 0.99, config.lowBFSlope, config.upBFSlope)
    sd_le = lineEq(0.01, 0.99, 0.25, 0.3)
    dist_le = lineEq(0.99, 0.01, 0.5, 0.75)

    # Execute Conditional Statements
    bfSlope_fn = Con(meanBFSlope >= config.upBFSlope, 0.99, Con(meanBFSlope <= config.lowBFSlope, 0.01, meanBFSlope * bfsl_le[0] + bfsl_le[1]))
    #meanSlope_fn2 = Con(meanSlope >= 7.0, 0.99, Con(meanSlope <= 5.0, 0.01, meanSlope * bfsl_le[0] + bfsl_le[1]))
    detSD_fn = Con(normDetSD >= 0.30, 0.99, Con(normDetSD <= 0.25, 0.01, normDetSD * sd_le[0] + sd_le[1]))
    eucDist_fn = Con(eucDist_norm <= 0.5, 0.99, Con(eucDist_norm >= 0.75, 0.01, eucDist_norm * dist_le[0] + dist_le[1]))

    pf_mem = Raster('t2Planar_runglide_Mem2.img')
    inv_pf = 1.0 - pf_mem
    inv_t2_02 = inv_pf * inv_t2_01

    #rawPF_02 = (bf_fn * bfSlope_fn * detSD_fn * eucDist_fn * inv_t2_02)
    rawPF_02 = ((bf_fn) * (bfSlope_fn) * (eucDist_fn) * (inv_t2_02))
    rcPF_02 = Con(IsNull(rawPF_02), 0.01, rawPF_02)
    outPF_02 = ExtractByMask(rcPF_02, bfPoly)
    outPF_02.save('t2Planar_rapcasc_Mem.img')


    guThreshAttr(outPF_02, 't2Planar_rapcasc', 0.5, 'In Channel', 'Planar-RapidCascade', 4, 'FALSE')

# ------------------------------------------------------------------------------
# Geomorphic Unit Area Threshold & Attributes Function
# --------------------------------------------------------------------------------


def guThreshAttr(ras, outName, thresh, t1Name, t2Name, rasVal, saveNQ):

    # Check that maximum probability ras value is > than probability threshold
    maxResult01 = arcpy.GetRasterProperties_management(ras, "MAXIMUM")
    max01 = float(maxResult01.getOutput(0))

    # If it is:
    if max01 > config.memTh:

    # Compute area Threshold
        areaTh = float(thresh * config.intBFW)

    # Create threshold where clause
        whereClause = '"VALUE" <= ' + str(config.memTh)

        rThresh = SetNull(ras, 1, whereClause)

        rArea = ZonalGeometry(rThresh, 'VALUE', 'AREA', cell_size = 0.1)
        maxArea = float(arcpy.GetRasterProperties_management(rArea, "MAXIMUM").getOutput(0))

        if maxArea > areaTh:

            if t2Name == 'Bank':
                # Group raster by region
                rRegionGrp = RegionGroup(rThresh, 'FOUR')
            else:
                rShrink = Shrink(rThresh, 1, [1, 2])
                rExpand = Expand(rShrink, 1, [1, 2])
                # Group raster by region
                rRegionGrp = RegionGroup(rExpand, 'FOUR')

            # Calculate area of each region
            rZonalGeometry = ZonalGeometry(rRegionGrp, "Value", "AREA", "0.1")

            # Remove regions that are less than the threshold area value
            maxResult02 = arcpy.GetRasterProperties_management(rZonalGeometry, "MAXIMUM")
            max02 = float(maxResult02.getOutput(0))

            if max02 > areaTh:

                rThresh2 = SetNull(rZonalGeometry, rRegionGrp, '"VALUE" < ' + str(areaTh))
                maxResult03 = arcpy.GetRasterProperties_management(rThresh2, "MAXIMUM")
                max03 = float(maxResult03.getOutput(0))
                minResult01 = arcpy.GetRasterProperties_management(rThresh2, "MINIMUM")
                min01 = float(minResult01.getOutput(0))
                valList = list(range(int(min01), int(max03) + 1))

                if t2Name == 'Bank':
                    outRas = Con(rThresh2 > 0, 1)
                    outRas.save('{}.img'.format(outName))

                    # Raster to Polygon
                    tmpPoly = 'tmpPoly.shp'
                    arcpy.RasterToPolygon_conversion(rThresh2, tmpPoly, 'NO_SIMPLIFY', 'VALUE')

                else:
                    # Save output raster
                    outRas = Con(rThresh2 > 0, 1)
                    outRas.save('{}.img'.format(outName))

                    # Raster to Polygon
                    tmpPoly = 'tmpPoly.shp'
                    arcpy.RasterToPolygon_conversion(rThresh2, tmpPoly, 'NO_SIMPLIFY', 'VALUE')

                # Add Tier 1 and Tier 2 Names to attribute table
                arcpy.AddField_management(tmpPoly, "Tier1", "TEXT", 20)
                arcpy.AddField_management(tmpPoly, "Tier2", "TEXT", 25)
                arcpy.AddField_management(tmpPoly, "rasCode", "SHORT", 2)

                fields = ["Tier1", "Tier2", "rasCode"]

                with arcpy.da.UpdateCursor(tmpPoly, fields) as cursor:
                    for row in cursor:
                        row[0] = t1Name
                        row[1] = t2Name
                        row[2] = rasVal
                        cursor.updateRow(row)

                # Add shape orientation and position related field to the attribute table
                arcpy.AddField_management(tmpPoly, "guPosition", "TEXT", 25)
                arcpy.AddField_management(tmpPoly, "guArea", "FLOAT", "9", "3")
                arcpy.AddField_management(tmpPoly, "guWidth", "FLOAT", "7", "3")
                arcpy.AddField_management(tmpPoly, "guLength", "FLOAT", "7", "3")
                arcpy.AddField_management(tmpPoly, "guOrient", "TEXT", "15")

                # Calculate area field
                fields = ["SHAPE@Area", "guArea"]
                with arcpy.da.UpdateCursor(tmpPoly, fields) as cursor:
                    for row in cursor:
                        row[1] = row[0]
                        cursor.updateRow(row)

                # Calculate orientation and position for all in channel units
                if t1Name == 'In Channel':
                    unitPosition(config.bfPolyShp, config.wePolyShp, tmpPoly, config.intWW)
                    unitOrientation(tmpPoly, config.bfXS)

           #      # If planar run/glide unit is wider than long, delete it
           #      # note, it will get classified as a transition in guMerge function

           #      if t2Name == 'Planar-RunGlide':
           #          fields = ["guPosition", "guOrient"]
           #          with arcpy.da.UpdateCursor(tmpPoly, fields) as cursor:
           #              for row in cursor:
           #                  if row[1] == 'Transverse':
    							# cursor.deleteRow()

           #      # If planar rapid/cascade unit is wider than long, delete it
           #      # note, it will get classified as a transition in guMerge function

           #      if t2Name == 'Planar-RapidCascade':
           #          fields = ["guPosition", "guOrient"]
           #          with arcpy.da.UpdateCursor(tmpPoly, fields) as cursor:
           #              for row in cursor:
           #                  if row[1] == 'Transverse':
    							# cursor.deleteRow()

                outShp = '{}.shp'.format(outName)
                arcpy.EliminatePolygonPart_management(tmpPoly, outShp, 'Area', areaTh, '', 'CONTAINED_ONLY')
                arcpy.Delete_management('tmpPoly.shp')

            if saveNQ == 'TRUE':

                outShpNQ = '{}_NonQ.shp'.format(outName)

                # Remove regions that are less than the threshold area value
                outRasNQ = SetNull(rZonalGeometry, 1, '"VALUE" > ' + str(areaTh))
                outRasNQ.save('{}_NonQ.img'.format(outName))

                # Raster to Polygon
                tmpPolyNQ = 'tmpPolyNQ.shp'
                arcpy.RasterToPolygon_conversion(outRasNQ, tmpPolyNQ, 'NO_SIMPLIFY', 'VALUE')


                # Add Tier 1 and Tier 2 Names to attribute table
                arcpy.AddField_management(tmpPolyNQ, "Tier1", "TEXT", 20)
                arcpy.AddField_management(tmpPolyNQ, "Tier2", "TEXT", 25)
                arcpy.AddField_management(tmpPolyNQ, "rasCode", "SHORT", 2)

                fields = ["Tier1", "Tier2", "rasCode"]

                with arcpy.da.UpdateCursor(tmpPolyNQ, fields) as cursor:
                    for row in cursor:
                        row[0] = t1Name
                        row[1] = t2Name
                        row[2] = rasVal
                        cursor.updateRow(row)

                arcpy.EliminatePolygonPart_management(tmpPolyNQ, outShpNQ, 'Area', areaTh, '', 'CONTAINED_ONLY')

                arcpy.Delete_management('tmpPolyNQ.shp')

            # Output new probability raster, where non-qualifying areas are assigned value of 0.01
            rThresh2 = SetNull(ras, 1, '"VALUE" <=  0.01')

            if t2Name == 'Bank':
                rRegionGrp2 = RegionGroup(rThresh2, 'FOUR')
                rZonalGeometry2 = ZonalGeometry(rRegionGrp2, "Value", "AREA", "0.1")
                rThresh3 = SetNull(rZonalGeometry2, 1, '"VALUE" < ' + str(areaTh))
                pRas = Con(IsNull(rThresh3), 0.01, ras)
            else:
                rShrink2 = Shrink(rThresh2, 1, 1)
                rExpand2 = Expand(rShrink2, 1, 1)
                rRegionGrp2 = RegionGroup(rExpand2, 'FOUR')
                rZonalGeometry2 = ZonalGeometry(rRegionGrp2, "Value", "AREA", "0.1")
                rThresh3 = SetNull(rZonalGeometry2, 1, '"VALUE" < ' + str(areaTh))
                pRas = Con(IsNull(rThresh3), 0.01, ras)

            pRasOut = ExtractByMask(pRas, ras)
            pRasOut.save('{}2.img'.format(os.path.splitext(ras.name)[0]))

    print('Finished delineating: ' + t2Name)

# ------------------------------------------------------------------------------
# Tier 2 Attributes Functions
# --------------------------------------------------------------------------------


def unitPosition(bfPolyShp, wePolyShp, units, intWW):

    print('Computing unit position....')

    #-----------------------------------------------------------
    # Create channel edge polygon
    #----------------------------------------------------------

    # Create copy of bfPoly and wPoly
    bfPoly = 'tmpPoly_bf1.shp'
    wPoly = 'tmpPoly_w1.shp'
    arcpy.CopyFeatures_management(bfPolyShp, bfPoly)
    arcpy.CopyFeatures_management(wePolyShp, wPoly)

    # Remove small polygon parts from bfPoly and wPoly
    # threshold: < 5% of total area
    bfPolyElim = 'tmpPoly_bf2.shp'
    wPolyElim = 'tmpPoly_w2.shp'
    arcpy.EliminatePolygonPart_management (wPoly, wPolyElim, 'PERCENT', '', 5, 'ANY')
    arcpy.EliminatePolygonPart_management (bfPoly, bfPolyElim, 'PERCENT', '', 5, 'ANY')

    # Erase wPoly from bfPoly
    erasePoly = 'tmpPoly_erase.shp'
    arcpy.Erase_analysis(bfPolyElim, wPolyElim, erasePoly, "")

    # Buffer output by one cell
    # ensures there are no 'breaks' along the banks due to areas
    # where bankfull and wetted extent were the same
    polyBuffer = 'tmpPoly_buffer.shp'
    arcpy.Buffer_analysis(erasePoly, polyBuffer, 0.1, 'FULL')

    edgePoly = 'tmpPoly_edge.shp'
    arcpy.Clip_analysis(polyBuffer, bfPolyElim, edgePoly)

    #------------------------------------------------------------------------------
    # Split multipart edge polgyons into single part polygons
    #------------------------------------------------------------------------------
    edgePolySplit = 'tmpPoly_edge2.shp'
    arcpy.MultipartToSinglepart_management(edgePoly, edgePolySplit)

    #------------------------------------------------------------------------------
    # Assign position to each poly in the units polygon
    #------------------------------------------------------------------------------
    # Create a copy of the unitsPath poly
    tmp_units = 'tmpPoly_units1.shp'
    arcpy.CopyFeatures_management(units, tmp_units)

    # Calculate distance threshold
    dTh = 0.1 * intWW

    #  Loop through units
    edge_lyr = 'edge_lyr'
    arcpy.MakeFeatureLayer_management(edgePolySplit, edge_lyr)

    ## old cursors
    cursor = arcpy.UpdateCursor(tmp_units, fields = 'guPosition')
    for unit in cursor:
        poly = unit.Shape
        arcpy.SelectLayerByLocation_management(edge_lyr, "WITHIN_A_DISTANCE", poly, dTh, "NEW_SELECTION")
        edgeCount = int(arcpy.GetCount_management(edge_lyr).getOutput(0))
        if edgeCount < 1:
            unit.guPosition = 'Mid Channel'
        elif edgeCount >= 2:
            unit.guPosition = 'Channel Spanning'
        else:
            unit.guPosition = 'Edge Attached'
        cursor.updateRow(unit)
    del cursor

    # Write output to input unitsPath shapefile
    arcpy.CopyFeatures_management(tmp_units, units)

    arcpy.Delete_management('tmpPoly_bf1.shp')
    arcpy.Delete_management('tmpPoly_w1.shp')
    arcpy.Delete_management('tmpPoly_bf2.shp')
    arcpy.Delete_management('tmpPoly_w2.shp')
    arcpy.Delete_management('tmpPoly_erase.shp')
    arcpy.Delete_management('tmpPoly_buffer.shp')
    arcpy.Delete_management('tmpPoly_edge.shp')
    arcpy.Delete_management('tmpPoly_edge2.shp')
    arcpy.Delete_management('tmpPoly_units1.shp')


def unitOrientation(units, bfXS):

    print ('Computing unit orientation....')

    #-----------------------------------------------------------
    # Delete unnecessary fields from xsecs
    #----------------------------------------------------------

    # Create copy of xsecs
    xsec = 'tmpPoly_xsec1.shp'
    arcpy.CopyFeatures_management(bfXS, xsec)

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
    #  the case, retain an extra field (the first one in the original list)
    desc = arcpy.Describe(xsec)
    if desc.dataType in ["ShapeFile", "DbaseTable"]:
        fieldNameList = fieldNameList[1:]

    # Execute DeleteField to delete all fields in the field list.
    xsec2 = arcpy.DeleteField_management(xsec, fieldNameList)

    #-----------------------------------------------------------
    # Clip xsec to unit poly
    #----------------------------------------------------------

    # Create tmp poly - a copy of the unitsPath poly
    tmp_units = 'tmpPoly_units1.shp'
    arcpy.CopyFeatures_management(units, tmp_units)

    # Clip xsec to unit polys
    xsec_clip = 'tmpPoly_xsec2.shp'
    arcpy.Clip_analysis(xsec2, tmp_units, xsec_clip)

    # Split multipart xsecs into single part xsecs
    xsec_split = 'tmpPoly_xsec3.shp'
    arcpy.MultipartToSinglepart_management(xsec_clip, xsec_split)

    # Add length field to attribute table
    arcpy.AddField_management(xsec_split, "guWidth", "FLOAT", "7", "3")

    # Calculate xsec length
    fields = ["SHAPE@LENGTH", "guWidth"]

    with arcpy.da.UpdateCursor(xsec_split, fields) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)

    # Delete 'tiny' segments
    # ....if end up using mean xsec length in unit length cal,
    # these small segments won't skew the results.
    with arcpy.da.UpdateCursor(xsec_split, "guWidth") as cursor:
        for row in cursor:
            if row[0] < 0.1:
                cursor.deleteRow()

    #-----------------------------------------------------------
    # Attribute max xsec length to ea poly
    #----------------------------------------------------------

    # Spatial join

    # Create a new fieldmappings and add the input feature classes
    fieldmappings = arcpy.FieldMappings()
    fieldmappings.addTable(xsec_split)
    fieldmappings.addTable(units)

    # Get the guWidth fieldmap.
    guWidthFieldIndex = fieldmappings.findFieldMapIndex("guWidth")
    fieldmap = fieldmappings.getFieldMap(guWidthFieldIndex)

    # Set the merge rule to mean and then replace the old fieldmap in the mappings object
    # with the updated one
    fieldmap.mergeRule = "maximum"
    fieldmappings.replaceFieldMap(guWidthFieldIndex, fieldmap)

    #Run the Spatial Join tool, using the defaults for the join operation and join type
    units_join = 'tmpPoly_units2.shp'
    arcpy.SpatialJoin_analysis(tmp_units, xsec_split, units_join, "#", "#", fieldmappings)

    #-----------------------------------------------------------
    # Add fields to unit polys
    #----------------------------------------------------------

    # Calculate  guLength, gu Width
    fields = ["guWidth", "guArea", "guLength"]

    with arcpy.da.UpdateCursor(units_join, fields) as cursor:
        for row in cursor:
            if row[0] > 0.0:
                row[2] = row[1]/row[0]
            cursor.updateRow(row)

    # Determine orientation
    fields = ["guWidth", "guLength", "guOrient"]

    with arcpy.da.UpdateCursor(units_join, fields) as cursor:
        for row in cursor:
            if row[0] > 0.0:
                if row[0]/row[1] > 1.0:
                    row[2] = "Transverse"
                else:
                    row[2] = "Streamwise"
            else:
                row[2] = 'NA'
            cursor.updateRow(row)

    # Write output to input unitsPath shapefile
    arcpy.CopyFeatures_management(units_join, units)

    arcpy.Delete_management('tmpPoly_xsec1.shp')
    arcpy.Delete_management('tmpPoly_xsec2.shp')
    arcpy.Delete_management('tmpPoly_xsec3.shp')
    arcpy.Delete_management('tmpPoly_units1.shp')
    arcpy.Delete_management('tmpPoly_units2.shp')

# -----------------------------------
# GU Merge Function
# -----------------------------------


def guMerge(det):

    print('Merging units....')

    # Create output raster/shapefile names
    outshp = '{}_Tier2.shp'.format(config.siteName)
    outRas = '{}_Tier2.img'.format(config.siteName)
    outshpSmooth = '{}_Tier2_Smoothed.shp'.format(config.siteName)

    # Create empty list
    shpList = []

    # Search workspace folder for all polygon shapefiles that match searchName
    # Add to list
    for root, dir, files in os.walk(arcpy.env.workspace):

        for f in files:
            shpList = arcpy.ListFeatureClasses('t2*', 'Polygon')

    for shp in shpList:
        if "NonQ.shp" in shp:
            shpList.remove(shp)
        if "check" in shp:
            shpList.remove(shp)
        if "Mem" in shp:
            shpList.remove(shp)

    # Merge all shapefiles in list
    tmpPoly = 'tmpPoly.shp'
    arcpy.Merge_management(shpList, tmpPoly)

    tmpPolySmooth = 'tmpPolySmooth.shp'
    arcpy.SmoothPolygon_cartography(tmpPoly, tmpPolySmooth, 'PAEK', 2)

    def merge(poly, polySmooth, smooth):
        # Delineate transition zones
        # Create/calculate attribute fields
        # Merge with existing polygon shapefile
        rasDomain = 'rasDomain.shp'
        tranShp = 'tranShp.shp'
        tranShpIn = 'tranShpIn.shp'
        tranShpOut = 'tranShpOut.shp'

        arcpy.RasterDomain_3d(det, rasDomain, 'POLYGON')
        arcpy.Erase_analysis(rasDomain, poly, tranShp)

        arcpy.Erase_analysis(tranShp, config.bfPolyShp, tranShpOut)
        arcpy.Clip_analysis(tranShp, config.bfPolyShp, tranShpIn)

        arcpy.AddField_management(tranShpIn, "Tier1", "TEXT", 20)
        arcpy.AddField_management(tranShpIn, "Tier2", "TEXT", 25)
        arcpy.AddField_management(tranShpIn, "rasCode", "SHORT", 2)

        fields = ["Tier1", "Tier2", "rasCode"]

        with arcpy.da.UpdateCursor(tranShpIn, fields) as cursor:
            for row in cursor:
                row[0] = 'In Channel'
                row[1] = 'Transition'
                row[2] = 11
                cursor.updateRow(row)

        arcpy.AddField_management(tranShpOut, "Tier1", "TEXT", 20)
        arcpy.AddField_management(tranShpOut, "Tier2", "TEXT", 25)
        arcpy.AddField_management(tranShpOut, "rasCode", "SHORT", 2)

        fields = ["Tier1", "Tier2", "rasCode"]

        with arcpy.da.UpdateCursor(tranShpOut, fields) as cursor:
            for row in cursor:
                row[0] = 'Out of Channel'
                row[1] = 'Transition'
                row[2] = 12
                cursor.updateRow(row)

        if smooth == 'FALSE':
            poly2 = outshp
            arcpy.Merge_management([poly, tranShpIn, tranShpOut], poly2)
            arcpy.PolygonToRaster_conversion(poly2, 'rasCode', outRas, 'MAXIMUM_AREA', '', 0.1)

        if smooth =='TRUE':
            poly2 = outshp
            arcpy.Merge_management([poly, tranShpIn, tranShpOut], poly2)
            arcpy.PolygonToRaster_conversion(poly2, 'rasCode', outRas, 'MAXIMUM_AREA', '', 0.1)

            poly3 = outshpSmooth
            arcpy.Merge_management([polySmooth, tranShpIn, tranShpOut], poly3)

        arcpy.Delete_management(tranShp)
        arcpy.Delete_management(tranShpIn)
        arcpy.Delete_management(tranShpOut)
        arcpy.Delete_management(rasDomain)

    merge(tmpPoly, tmpPolySmooth, smooth = 'TRUE')

    # Delete temporary files
    arcpy.Delete_management(tmpPoly)
    arcpy.Delete_management(tmpPolySmooth)


def adjPolyCount(units, dTh):

    print('Calculting number of adjacent units....')
    #------------------------------------------------------------------------------
    # Create copies of the unitsPath poly
    #------------------------------------------------------------------------------
    # Create a copy of the unitsPath poly
    tmp_units = 'tmpPoly_units1.shp'
    arcpy.CopyFeatures_management(units, tmp_units)

    units_adj = 'tmpPoly_units2.shp'
    arcpy.CopyFeatures_management(units, units_adj)

    #------------------------------------------------------------------------------
    # Assign position to each poly in the units polygon
    #------------------------------------------------------------------------------

    # Add shape position field
    arcpy.AddField_management(units, "nAdjUnits", "SHORT", "4")

    #  Create layer for selection
    units_adj_lyr = 'units_adj_lyr'
    arcpy.MakeFeatureLayer_management(units_adj, units_adj_lyr)

    # Loop through units
    # using old cursors
    # use an update cursor to edit the 'nAdjUnits' field in the units polygon
    cursor = arcpy.UpdateCursor(units, fields = 'nAdjUnits')
    # for each polygon in the units polygon
    for unit in cursor:
        # xxxx
        poly = unit.Shape
        # select polygons from the units layer that are within the distance threshold from each units polygon
        arcpy.SelectLayerByLocation_management(units_adj_lyr, "WITHIN_A_DISTANCE", poly, dTh, "NEW_SELECTION")
        # get the count of selected polygons
        # as is, the polygon i is also selected.  subtract 1 from count to just get number of adjacent polygons.
        adjCount = int(arcpy.GetCount_management(units_adj_lyr).getOutput(0)) - 1
        # assign the count of selected polygons to the 'nAdjUnits' field
        unit.nAdjUnits = adjCount
        # update the row in the attribute table
        cursor.updateRow(unit)
    # delete the cursor (required when using old cursors)
    del cursor

    # Write output to input unitsPath shapefile
    arcpy.CopyFeatures_management(units, unitsPath)

    # Delete temporary files
    arcpy.Delete_management('tmpPoly_units1.shp')
    arcpy.Delete_management('tmpPoly_units2.shp')


def lineEq(y1, y2, x1, x2):

    m = (y1 - y2) / (x1 - x2)
    b = (y1) - (m * x1)

    return m, b
