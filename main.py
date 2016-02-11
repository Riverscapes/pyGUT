# Geomorphic Unit Tool Main Model File

# Import required modules
# Check out the required ArcGIS extension licenses
import arcpy, time, fns, sys, prepfromXML
from arcpy.sa import *

# Last updated: 10/14/2015
# Created by: Sara Bangen (sara.bangen@gmail.com)

# -----------------------------------
# Start of script
print "a little xml prep"
config = prepfromXML.prep(sys.argv)


print 'Model is busy running.....'

arcpy.CheckOutExtension('Spatial')
arcpy.CheckOutExtension('3D')

# Start timer
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

# Call model functions from functions file
fns.setConfig(config)
fns.EvidenceRasters(config.inDEM, config.inDet, config.bfPoints,
                       config.bfPolyShp, config.wePolyShp, config.intBFW,
                       config.intWW, config.fwRelief)

fns.Tier2()

fns.guMerge()

fns.Tier3()

# End timer
# Print model run time.
print 'Model run completed.'
print 'It took', time.time()-start, 'seconds.'
