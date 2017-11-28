# Geomorphic Unit Tool Configuration File

# Created by: Sara Bangen (sara.bangen@gmail.com)

# ---------------------------------------------------------------------
# User-defined input parameters that must be set before each model run.  Include file extension in all filenames.

# Project Level Parameters:
    # workspace: 	    Path to where the inputs are stored.  This is same path where output will be written.
    # runFolderName:    GUT run output folder name.  If set to 'Default' sequential folder name will be used (e.g., Run_001).

# Tier 1 Parameters:
    # bfPolyShp:	    Bankfull polygon shapefile.
    # bfCL:			    Bankfull centerline shapefile [Required fields: 'Channel', 'CLID']
    # wPolyShp:	        Wetted polygon shapefile
    # inDEM:            DEM raster

# Tier 2 Additional Parameters
    # createSaddles:    Argument indicating if saddles should be created/classified
    # bowlPercentile:   Residual topography percentile above which a cell will be classfied as a bowl
    # planePercentile:  Residual topography percentile below which a cell will be classified as a plane
    # wallSlopeTh:      Slope theshold above which a cell will be classified as a wall (barring other criteria).  If value is left blank slope mean + sd will be calculated and used as threshold
    # thalwegShp:       Thalweg polyline shapefile
    # wCL               Wetted centerline shapefile

# Tier 3 Additional Parameters
    # areaThresh:       Area threshold (as ratio fo bfw) for cascades, rapids, transitions, glide-runs.
# ---------------------------------------------------------------------
#  Project Level Parameters
workspace      = r'C:/et_al/Shared/Projects/USA/CHaMP/ResearchProjects/GUT/wrk_Data/Lemhi/CBW05583-170447/2012/VISIT_920\ModelRuns'
runFolderName  = 'GUT_2.1\Run_01'

#  Tier 1 Parameters
#  -----------------------------
#  Input Shapefiles and Rasters:
bfPolyShp      = 'Inputs/Bankfull.shp'
bfCL           = 'Inputs/BankfullCL.shp'
wPolyShp       = 'Inputs/WaterExtent.shp'
inDEM          = 'Inputs/DEM.tif'

#  Tier 2 Additional Parameters
#  -----------------------------
#  Input Shapefiles:
thalwegShp     = 'Inputs/Thalwegs.shp'
wCL            = 'Inputs/CenterLine.shp'
#  Unit Form Arguments:
createSaddles = 'True' # Default: 'True'
wallSlopeTh    = '' # Default: '' [if left blank slope distribution [mean + sd] is used to set threshold]
#  - Percentiles for Discrete Forms -
bowlPercentile = (65, )  # Default: (50, )
troughPercentile = (25, ) # Default: (25, )
planePercentile = (25, 25) # Default: (25, 25)
moundPercentile = (25, ) # Default: (25, )
#  - Percentiles for Forms with Transitions -
bowlPercentile2 = (65, )  # Default: (50, )
troughPercentile2 = (25, 65) # Default: (25, 50)
planePercentile2 = (25, 15) # Default: (25, 15)
moundTransitionPercentile = (15, 35)  # Default: (15, 35)
moundPercentile2 = (35, ) # Default: (35, )

#  Tier 3 Additional Parameters
#  -----------------------------
#  Input Shapefiles and Rasters:
areaThresh = 0.75  # Default: 0.75

import tierFunctions
myVars = globals()

tierFunctions.tier1(**myVars)
tierFunctions.tier2(**myVars)
tierFunctions.tier3(**myVars)
tierFunctions.tier3_subGU(**myVars)