# Geomorphic Unit Tool Configuration File

# Last updated: 1/25/2017
# Created by: Sara Bangen (sara.bangen@gmail.com)

# ---------------------------------------------------------------------
# User-defined input parameters that must be set before each model run.  Include file extension in all filenames.

# workspace: 	    Path to where the inputs are stored.  This is same path where output will be written.
# bfw:              Site integrated bankfull width (m)
# ww:			    Site integrated wetted width (m)
# memTh:			Membership threshold for crisp output
# bfCL:			    Bankfull centerline shapefile [Required fields: 'Channel', 'CLID']
# bfPolyShp:	    Bankfull polygon shapefile.
# bfXS:			    Bankfull cross sections shapefile [Required field: 'Channel']
# inDet: 		    Detrended DEM raster
# inDEM:            DEM raster
# thalwegShp:       Thalweg polyline shapefile
# wePolyShp:	    Wetted polygon shapefile
# ***Optional inputs***
# champUnits:       Champ channel units shapefile
# inWaterD:		    Water depth raster
# champGrainSize:   Champ grain size *.csv.  Must have columns: 'ChannelUnitID', 'ChannelUnitNumber', 'D84'.  Filename must end with '*GrainSizeDistributionResults.csv'.
# ---------------------------------------------------------------------

workspace    = r'C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\TopographicGUs\wrk_Data\Logan\LRB_64423\2015\VISIT_3416\ModelRuns\30Jan2017'
bfw          = 13.1
ww   	     = 11.4
memTh        = 0.8
bfCL         = r'C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\TopographicGUs\wrk_Data\Logan\LRB_64423\2015\VISIT_3416\Topo\Centerline.shp'
bfPolyShp    = r'C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\TopographicGUs\wrk_Data\Logan\LRB_64423\2015\VISIT_3416\Topo\Bankfull.shp'
bfXS         = r'C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\TopographicGUs\wrk_Data\Logan\LRB_64423\2015\VISIT_3416\Topo\BankfullXS.shp'
inDEM        = r'C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\TopographicGUs\wrk_Data\Logan\LRB_64423\2015\VISIT_3416\Topo\DEM.tif'
inDet        = r'C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\TopographicGUs\wrk_Data\Logan\LRB_64423\2015\VISIT_3416\Topo\Detrended.tif'
thalwegShp   = r'C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\TopographicGUs\wrk_Data\Logan\LRB_64423\2015\VISIT_3416\Topo\Thalweg.shp'
wePolyShp    = r'C:\et_al\Shared\Projects\USA\CHaMP\ResearchProjects\TopographicGUs\wrk_Data\Logan\LRB_64423\2015\VISIT_3416\Topo\WaterExtent.shp'

# Optional: Tier 3 Low Flow Roughness
lowFlowRoughness = 'FALSE'
champUnits   = 'Inputs/xxx.shp'
inWaterD	 = 'Inputs/xxx.img'
champGrainSize = 'Inputs/xxx.csv'

#execfile('tier1.py')
#execfile('tier2.py')
execfile('tier3.py')

