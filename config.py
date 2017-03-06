# Geomorphic Unit Tool Configuration File

# Last updated: 1/25/2017
# Created by: Sara Bangen (sara.bangen@gmail.com)

# ---------------------------------------------------------------------
# User-defined input parameters that must be set before each model run.  Include file extension in all filenames.

# workspace: 	    Path to where the inputs are stored.  This is same path where output will be written.
# runFolderName:    GUT run output folder name.  If set to 'Default' sequential folder name will be used (e.g., Run_001).
# bfw:              Site integrated bankfull width (m)
# ww:			    Site integrated wetted width (m)
# memTh:			Membership threshold for crisp output
# bfCL:			    Bankfull centerline shapefile [Required fields: 'Channel', 'CLID']
# bfPolyShp:	    Bankfull polygon shapefile.
# bfXS:			    Bankfull cross sections shapefile [Required field: 'Channel']
# inDet: 		    Detrended DEM raster
# inDEM:            DEM raster
# thalwegShp:       Thalweg polyline shapefile
# wCL               Wetted centerline shapefile
# wPolyShp:	        Wetted polygon shapefile
# ***Optional inputs***
# champUnits:       Champ channel units shapefile
# inWaterD:		    Water depth raster
# champGrainSize:   Champ grain size *.csv.  Must have columns: 'ChannelUnitID', 'ChannelUnitNumber', 'D84'.  Filename must end with '*GrainSizeDistributionResults.csv'.
# ---------------------------------------------------------------------

workspace     = r'C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\TopographicGUs\wrk_Data\01_TestSites\SFSalmon\CBW05583-206111\2014\VISIT_2057\ModelRuns'
runFolderName = 'GUT_2.0\\Run_001'
memTh         = 0.8
bfCL          = 'Inputs/BankfullCL.shp'
bfPolyShp     = 'Inputs/Bankfull.shp'
bfXS          = 'Inputs/BankfullXS.shp'
inDEM         = 'Inputs/DEM.tif'
inDet         = 'Inputs/Detrended.tif'
thalwegShp    = 'Inputs/Thalweg.shp'
wCL           = 'Inputs/CenterLine.shp'
wPolyShp      = 'Inputs/WaterExtent.shp'

# Optional: Tier 3 Low Flow Roughness
lowFlowRoughness = 'FALSE'
champUnits   = 'Inputs/xxx.shp'
inWaterD	 = 'Inputs/xxx.img'
champGrainSize = 'Inputs/xxx.csv'

#execfile('tier1.py')
#execfile('tier2.py')
execfile('tier3.py')

