import arcpy
from arcpy import mapping
from arcpy import env #as *  will import modules from env into workspace, I will leave as is

import sys
import types
import locale
import os
import arcgisscripting

#gp=arcgisscripting.create()

workspace=sys.argv[1]
#workspace=arcpy.GetParameterAsText(0)
#workspace=r'E:/GUT/_Asotin/ASW00001-NF-F2P2/VISIT_3949'

runfolder=sys.argv[2]
#runfolder=r'E:/GUT/_Asotin/ASW00001-NF-F2P2/VISIT_3949/Output/GUT_2.0/Run_005'

Lyrdir=sys.argv[3]
# Change this to hard code it to your symbology directory if you don't want to change it every time
Lyrdir=r"E:/GUT/pyGUT/GUTSymbology/LYR"

env.workspace=workspace

print "making list of input layer filepaths..."
layerfiles=os.listdir(Lyrdir)


layers=['ev_Hillshade.lyr',
        'out_Tier2_UnitForm.lyr', 'out_FlowUnit.lyr',
        'ev_Contour.lyr', 'in_Thalweg.lyr']

#Tier3=Lyrdir+ "/" +'out_Tier3_InChannel.lyr'   
Tier2=Lyrdir+ "/" +'out_Tier2_UnitForm.lyr'
Tier1=Lyrdir+ "/" +'out_FlowUnit.lyr'
contour=Lyrdir+ "/"+'ev_Contour.lyr'
hillshade=Lyrdir+ "/" +'ev_Hillshade.lyr'
thalweg=Lyrdir+ "/" +'in_Thalweg.lyr'

inputlist=[hillshade, Tier2, Tier1, contour, thalweg]
print "done"

print "making list of input shapefile paths..."
dTier2=runfolder+"/Tier2_InChannel.shp"
dTier1=runfolder + "/Tier1.shp"
dcontour=workspace+"/EvidenceLayers/DEM_Contours.shp"
dhillshade=workspace+"/EvidenceLayers/hillshade.tif"
dthalweg=workspace+"/Inputs/Thalweg.shp"

datalist=[dhillshade, dTier2, dTier1, dcontour, dthalweg]

print "done"


print "setting up mapdoc"
#mapdoc=mapping.MapDocument("E:/GUT/GUT.mxd") #script can run outside of ArcMap
mapdoc=mapping.MapDocument("CURRENT")  # if this is used script must be run from within ArcMap
# I can use execfile(r'E:/GUT/mapping2.py') in the python windo to accomplish this.
print "done"
df = arcpy.mapping.ListDataFrames(mapdoc)[0]


#def hillshadefromDEM(inRaster):
 #   if os.path.exists(datalist[0])== False:
#        outHillshade = workspace + "/EvidenceLayers/hillshade.tif"
#        arcpy.HillShade_3d(inRaster, outHillshade)
#        updateLyr = arcpy.mapping.Layer(datalist[0])
#        updateLyr = arcpy.mapping.Layer(UpdateLyr)
        #if os.path.exists(inputlist[0]):
            #sourceLayer = arcpy.mapping.Layer(inputlist[0])
            #arcpy.mapping.UpdateLayer(df, updateLyr, sourceLayer)
        #arcpy.mapping.AddLayer(df,updateLyr)
#        del updateLyr, sourceLayer

#if os.path.exists(workspace + "/Inputs/DEM.tif")==True:
#    hillshadefromDEM(workspace+"/Inputs/DEM.tif")
#    print "hillshade finished"

print "adding layers to map with appropriate symbology"
for i in range(len(inputlist)):
    if os.path.exists(datalist[i]):
        updateLyr = arcpy.mapping.Layer(datalist[i])
        sourceLayer = arcpy.mapping.Layer(inputlist[i])
        #lyrlist=mapping.ListLayers(mapdoc)
        arcpy.mapping.UpdateLayer(df, updateLyr, sourceLayer)
        arcpy.mapping.AddLayer(df,updateLyr,"TOP")
        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()
        del updateLyr, sourceLayer
    else:
        print "i="
        print layers[i]
        print "missing"
print"done"


#print "Refreshing Active View"
#arcpy.RefreshActiveView()
#print "done"

#print "now saving"
mapdoc.save() #saves over existing except it isn't working because it says I don't have write access...


print "getting rid of locks on mxd"
del mapdoc, df, datalist, inputlist, layers, workspace # this will unlock the map doc so I can use it again outside of python during rest of script
print "done"
