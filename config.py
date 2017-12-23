# Geomorphic Unit Tool Configuration File

# Created by: Sara Bangen (sara.bangen@gmail.com)

# ---------------------------------------------------------------------
# User-defined input parameters that must be set before each model run.  Include file extension in all filenames.

# Project Level Parameters:
    # workspace: 	    Path to where the inputs are stored.  This is same path where output will be written.
    # runFolderName:    GUT run output folder name.  If set to 'Default' sequential folder name will be used (e.g., Run_001).

# Tier 1 Parameters:
    # bfPolyShp:	    Bankfull polygon shapefile.
    # bfCL:			    Bankfull centerline shapefile
    # wPolyShp:	        Wetted polygon shapefile
    # inDEM:            DEM raster

# Tier 2 Additional Parameters
    # thalwegShp:       Thalweg polyline shapefile
    # wCL               Wetted centerline shapefile
    # createSaddles:    Argument indicating if saddles should be created/classified
    # saddleAreaThresh: Area threshold (as ratio fo bfw) for saddles
    # wallSlopeTh:      Slope theshold above which a cell will be classified as a wall (barring other criteria).  If value is left blank slope mean + sd will be calculated and used as threshold
    # Residual Topography Percentile Thresholds:
    #   - Statistical breaks in residual topography evidence raster used to classify Tier 2 shapes and forms
    #   - Percentile thresholds are defined be tuple in the order of (min, max)
    #   - Examples:
    #       bowlPercentile = (-65, ): Negative residual topography values ranging from the 65th percentile to max will be classified as bowl (barring other criteria)
    #       moundTransitionPercentile = (15, 35): Positive residual topography values ranging from the 15th to 35th percentile will be classified as mound transition(barring other criteria)

# Tier 3 GU Additional Parameters
    # createPocketPools:    Argument indicating if pocket pools (i.e., pools with area < pool area threshold) should be created/classified
    # poolAreaThresh:       Area threshold (as ratio fo bfw) for pool features.  Applies to pools, ponds
    # planebedAreaThresh:   Area threshold (as ratio fo bfw) for planebed features.  Applies to: run-glides, rapids, cascades
    # barAreaThresh:        Area threshold (as ratio fo bfw) for bar features.  Applies to: margin-attached bars, mid-channel bars.
    # chuteAreaThresh:      Area threshold (as ratio fo bfw) for chute features.  Applies to: chutes, shallow thalwegs

# Tier 3 SubGU Additional Parameters
    # waterfallReliefThreshold: Relief value above which a step feature will be classified as a waterfall

# ---------------------------------------------------------------------
#  Project Level Parameters
workspace      = r'C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\GUT\wrk_Data\Lemhi\CBW05583-028079\2012\VISIT_1029\ModelRuns'
runFolderName  = 'GUT_2.1\Run_Test04'

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
createSaddles = 'Yes' # Default: 'Yes'
saddleAreaThresh = 0.25 # Default: 0.25
wallSlopeTh    = '' # Default: '' [if left blank slope distribution [mean + sd] is used to set threshold]

#  - Residual Topography Percentile Thresholds -
bowlPercentile = (-65, )  # Default: (-65, )
troughPercentile = (-25, -65) # Default: (-25, -65)
planePercentile = (-25, 15) # Default: (-25, 15)
moundTransitionPercentile = (15, 35) # Default: (15, 35)
moundPercentile = (35, ) # Default: (35, )

#  Tier 3 Additional Parameters
#  -----------------------------
createPocketPools = 'Yes' # Default: 'Yes'
#  - Area Thresholds -
poolAreaThresh = 0.5  # Default: 0.5; Applies to: pools, ponds
planebedAreaThresh = 0.75  # Default: 0.75; Applies to: run-glides, rapids, cascades
barAreaThresh = 0.25  # Default: 0.5; Applies to: margin-attached bars, mid-channel bars
chuteAreaThresh = 0.25  # Default: 0.25; Applies to: chutes, shallow thalwegs

#  Tier 3 SubGU Additional Parameters
#  -----------------------------
waterfallReliefThreshold = 3.0 # Default: 3.0

import tierFunctions
myVars = globals()

#tierFunctions.tier1(**myVars)
#tierFunctions.tier2(**myVars)
tierFunctions.tier3(**myVars)
#tierFunctions.tier3_subGU(**myVars)