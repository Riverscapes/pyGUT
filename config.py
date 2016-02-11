# Geomorphic Unit Tool Configuration File

# Last updated: 10/14/2015
# Created by: Sara Bangen (sara.bangen@gmail.com)

# ---------------------------------------------------------------------
# User-defined input parameters that must be set before each model run

# workspace: 	    Path to where the inputs are stored.  This is same path where output will be written.
# Site name:		Site name.  Used to name final output.
# intBFW:           Site integrated bankfull width (m).
# intWW:			Site integrated wetted width (m).
# memTh:			Membership threshold for crisp output.
# bfPoints:		    Bankfull points shapefile name (include file extension; e.g. 'bfPoints.shp')
# bfPolyShp:	    Bankfull polygon shapefile name (include file extension)
# bfXS:			    Bankfull cross sections shapefile name (include file extension)
# wePolyShp:	    Wetted polygon shapefile name (include file extension)
# champUnits:       Champ channel units shapefile
# inDet: 		    Detrended DEM fiSUBSTRATECOVER_2013_CBW05583-026031_1646le name (include file extension)
# inDEM:            DEM file name (include file extension)
# inWaterD:		    Water depth raster file name (include file extension)
# champGrainSize:   Champ grain size *.csv.  Must have columns: 'ChannelUnitID', 'ChannelUnitNumber', 'D84'.  Filename must end with '*GrainSizeDistributionResults.csv'. 
# champSubstrate:	Champ channel unit substrate *.csv.
# champLW:			Champ channel unit large wood *.csv.
# ---------------------------------------------------------------------

workspace    = r'C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\TopographicGUs\wrk_Data\00_Watershed\TestData_ForPB\validationData\Oct2015\Wenatchee\Output'
siteName     = 'LowWen'
intBFW       = 38.8
intWW   	 = 32.2
memTh        = 0.68
bfPoints     = 'bfPoints.shp'
bfPolyShp    = 'bfPolygon.shp'
bfXS         = 'bfXS.shp'
wePolyShp    = 'wePoly.shp'
inDet        = 'detDEM.tif'
inDEM        = 'dem.tif'
# Tier 3 (optional):
champUnits   = 'channelUnitsClip.shp'
inWaterD	 = 'waterDepth.tif'
champGrainSize = 'GrainSizeDistributionResults.csv'
champSubstrate = 'champSubstrate.csv'
champLW	    = 'champLW.csv'


# ---------------------------------------------------------------------
# Optional input parameters that can be set before a model run.

# lowSlope:  	 Lower slope (in degress) threshold; used in flooplain, terrace, hillslope
# upSlope:   	 Upper slope (in degress) threshold; used in flooplain, terrace, hillslope
# lowDMSlope:  	 Lower channel margin slope (in degress) threshold; used in bank + cutbank
# upCMSlope:   	 Upper channel margin slope (in degress) threshold; used in bank + cutbank
# lowHADBF:      Lower normalized height above detrended bankfull threshold; used in floodplain + terrace
# upHADBF:       Upper normalized height above detrended bankfull threshold; used in floodplain + terrace
# lowRelief:     Lower DEM relief (m) threshold; used in floodplaink, terrace + hillslope
# upRelief: 	 Upper DEM relief (m) threshold; used in floodplaink, terrace + hillslope
# lowBFDist:     Lower bankfull distance threshold; used in cutbank + hillslope
# upBFDist: 	 Upper bankfull distance threshold; used in cutbank + hillslope
# fwRelief:      Focal window size for dem relief call
# ---------------------------------------------------------------------

lowSlope     = 10
upSlope      = 15
lowCMSlope   = 15
upCMSlope    = 25
lowHADBF     = 1.0
upHADBF      = 1.2
lowRelief    = 0.8
upRelief     = 1.0
lowBFDist    = 0.1*intBFW
upBFDist     = 0.2*intBFW
fwRelief     = 0.5*intBFW 