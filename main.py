# Geomorphic Unit Tool Main Model File

# Import required modules
# Check out the required ArcGIS extension licenses
import sys
import arcpy, time, fns, sys, xml, config
import xml.etree.ElementTree as ET
from arcpy.sa import *

# Last updated: 10/14/2015
# Created by: Sara Bangen (sara.bangen@gmail.com)

# -----------------------------------
# Start of script

print 'Model is busy running.....'

print 'Loading XML File'

tree = ET.parse(sys.argv[1])
inputs = tree.getroot().findall('inputs/*')
config.getConfig(inputs, sys.argv[2])

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
