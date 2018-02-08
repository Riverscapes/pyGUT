#  import required modules and extensions
import os
import fnmatch
import arcpy

rootFolder = 'D:/GUT/Entiat'

#   loop through directory and find all files with the name "Tier2_InChannel.shp"
#   then run the SmoothPolygon tool on each file
#   and create a new file called "Tier2_InChannel_smooth.shp"
for root, dirs, files in os.walk(rootFolder):
	for f in fnmatch.filter(files, 'Tier2_InChannel.shp'):
		# shapefile name without extension  
		shpName = os.path.splitext(f)[0]  
		# absolute file path
		absFile = os.path.abspath(os.path.join(root,f))       
		# output file name
		output_layer = os.path.join(root,(shpName + '_smooth' + '.shp'))
		#smooth polygon
		arcpy.SmoothPolygon_cartography(absFile, output_layer, "PAEK", "1 Meters", "FIXED_ENDPOINT", "FLAG_ERRORS")