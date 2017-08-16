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
    # bfXS:			    Bankfull cross sections shapefile [Required field: 'Channel']

# ---------------------------------------------------------------------

#  Project Level Parameters
workspace      = r'C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\TopographicGUs\wrk_Data\01_TestSites\Lemhi\CBW05583-028079\2012\VISIT_1029\ModelRuns'
runFolderName  = 'GUT_2.0//Run_B50P25CT'

#  Tier 1 Parameters
bfPolyShp      = 'Inputs/Bankfull.shp'
bfCL           = 'Inputs/BankfullCL.shp'
wPolyShp       = 'Inputs/WaterExtent.shp'
inDEM          = 'Inputs/DEM.tif'

#  Tier 2 Additional Parameters
createSaddles = 'True' # Default: 'True'
bowlPercentile = 50  # Default: 50
planePercentile = 25 # Default: 25
wallSlopeTh    = '' # Default: '' [if left blank slope distribution [mean + sd] is used to set threshold]
thalwegShp     = 'Inputs/Thalweg.shp'
wCL            = 'Inputs/CenterLine.shp'

#  Tier 3 Additional Parameters
bfXS           = 'Inputs/BankfullXS.shp'

execfile('tier1.py')
execfile('tier2.py')
#execfile('tier3.py')

