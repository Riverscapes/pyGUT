# Updated: 5/28/2015

# Changes:
#	   - Linked to Functions_v11 - v15
#	   		- uses fuzzy cluster results
#			- based on [0 1]; removed transform functions/probabilities
#	   - Suppressed R functions calls (longitudinal curvature, channel unit distance)
#      - Added bankfull distance evidence raster
#      - Added cutbanks to Tier 2 out of channel units
#      - Added alluvial fans
#
# -----------------------------------
# Start of script

print 'Model is busy running.....'

# Import required modules
# Check out the ArcGIS Spatial Analyst extension license
import arcpy, time, fns, config
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension('Spatial')
arcpy.CheckOutExtension("3D")

start = time.time()

# Set workspace
# Set environment settings to overwrite output
arcpy.env.workspace = config.workspace
arcpy.env.overwriteOutput = True

# Set raster and environment parameters
det = Raster(config.inDet)
desc = arcpy.Describe(det)
arcpy.env.extent = desc.Extent
arcpy.env.outputCoordinateSystem = desc.SpatialReference
arcpy.env.cellSize = desc.meanCellWidth


def EvidenceRasters():

    dem = Raster(config.inDEM)
    fns.bfPoly(det, config.bfPolyShp)
    bfPoly = Raster('bfPoly.img')
    fns.HADBF(det, config.bfPoints)
    HADBF = Raster('HADBF.img')
    fns.normBFDepth(HADBF)
    bfDepth = Raster('bfDepth.img')
    fns.normHADBF(HADBF, bfDepth)
    fns.detSlope(det)
    detSlope = Raster('detSlope.img')
    fns.bfDist(config.bfPolyShp, det)
    fns.detRelief(det, bfPoly, config.fwRelief)
    fns.normMeanSlope(det, config.fwSlope)
    fns.normConcavity(dem, config.bfPolyShp)
    fns.normInverseFill(det, bfPoly)
    fns.chMargin(config.bfPolyShp, config.wePolyShp, config.intWW)
    cm = Raster('chMargin.img')
    meanSlope = Raster('meanSlope.img')
    fns.bfSlope(cm, meanSlope, bfPoly)
    #fns.bfSlope(cm, detSlope, bfPoly)
    meanBFSlope = Raster("detSlopeMean_BFW.img")
    fns.detSD(det, meanBFSlope)

EvidenceRasters()


def InChTransform():

    # Input rasters
    cm = Raster('chMargin.img')
    normInvF = Raster('normInvFill.img')
    normBFD = Raster('normBFDepth.img')
    nc = Raster('normConcavity.img')
    meanSlope = Raster('meanSlope.img')
    meanBFSlope = Raster('detSlopeMean_BFW.img')
    normDetSD = Raster('detSD_BFW_norm.img')
    bfPoly = Raster('bfPoly.img')

    fns.concavityTFs(normBFD, bfPoly, nc)
    t2cv = Raster('t2Concavity_Mem2.img')
    t2cvQ = Raster('t2Concavity.img')
    t2cvNQ = Raster('t2Concavity_NonQ.img')
    fns.chMarginTFs(cm, meanSlope, bfPoly, t2cv)
    t2cm = Raster('t2ChMargin_Mem2.img')
    fns.convexityTFs(bfPoly, nc, normInvF, normBFD, t2cv, t2cm)
    t2cx = Raster('t2Convexity_Mem2.img')
    fns.planarTFs(bfPoly, normBFD, meanSlope, normInvF, nc, meanBFSlope, normDetSD, t2cv, t2cm, t2cx, det, t2cvNQ, t2cvQ)

InChTransform()


def OutChTransform(*args):

    # Input rasters
    bfDist = Raster('bfDist.img')
    bfPoly = Raster('bfPoly.img')
    normHADBF = Raster('normHADBF.img')
    meanSlope = Raster('meanSlope.img')
    Relief = Raster('detRelief.img')

    fns.afpTFs(bfPoly, meanSlope, normHADBF, Relief)
    fns.cbTFs(bfPoly, meanSlope, bfDist)
    fns.hsTFs(bfPoly, meanSlope, bfDist, Relief)
    fns.ifpTFs(bfPoly, meanSlope, normHADBF, Relief)

OutChTransform()


def Merge():

    fns.guMerge(det)

Merge()

print 'Model run completed.'
print 'It took', time.time()-start, 'seconds.'
