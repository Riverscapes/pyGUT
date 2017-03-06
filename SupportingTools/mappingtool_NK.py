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
#workspace="E:/GUT/_Wenatchee/LWIN0001-000001/2014/VISIT_2633"


#if sys.argv[2]==""
Lyrdir=r"E:/GUT/GUTSymbology/LYR"
#r"C:\Users\A02252705\Desktop\Box Sync\CRB_GU\wrk_Data\GUT\GUTSymbology"
#Lyrdir=sys.argv[2]
#Lyrdir=GetParameterAsText(1)


env.workspace=workspace

print "making list of input layer filepaths..."
layerfiles=os.listdir(Lyrdir)


layers=['ev_Hillshade.lyr','out_Membership.lyr', 'out_Membership.lyr','out_Membership.lyr',
        'out_Tier2_Position.lyr', 'out_Tier2_InChannel',
        'ev_riffleCrest.lyr', 'out_Contour.lyr']

#inlyrs=[]

#for item in inputlist:
#    inlyrs[i]=workspace+ "/" +str(inputlist[i])
#    
#print inlyrs


#Tier3=Lyrdir+ "/" +layerfiles[layerfiles.index('out_Tier3_InChannel.lyr')]    
#Tier2=Lyrdir+ "/" +layerfiles[layerfiles.index('out_Tier2_InChannel.lyr')]
#Tier2pos=Lyrdir+ "/"+layerfiles[layerfiles.index('out_Tier2_Position.lyr')]
#membership=Lyrdir+ "/"+layerfiles[layerfiles.index('out_Membership.lyr')]
#detDEM=Lyrdir+ "/"+layerfiles[layerfiles.index('in_detDEM.lyr')]
#detDEM=Lyrdir+ "/"+layerfiles[layerfiles.index('in_detDEM.lyr')]
#riffles=Lyrdir+ "/"+layerfiles[layerfiles.index('ev_riffleCrest.lyr')]
#contour=Lyrdir+ "/"+layerfiles[layerfiles.index('ev_Contour.lyr')]
#hillshade=Lyrdir+ "/"+layerfiles[layerfiles.index('ev_Hillshade.lyr')]


Tier3=Lyrdir+ "/" +'out_Tier3_InChannel.lyr'   
Tier2=Lyrdir+ "/" +'out_Tier2_InChannel.lyr'
Tier2pos=Lyrdir+ "/"+'out_Tier2_Position.lyr'
membership=Lyrdir+ "/"+'out_Membership.lyr'
detDEM=Lyrdir+ "/"+'in_detDEM.lyr'
detDEM=Lyrdir+ "/"+'in_detDEM.lyr'
riffles=Lyrdir+ "/"+'ev_riffleCrest.lyr'
contour=Lyrdir+ "/"+'ev_Contour.lyr'
hillshade=Lyrdir+ "/" +'ev_Hillshade.lyr'

inputlist=[hillshade, membership, membership, membership, Tier2pos, Tier2, riffles, contour]
print "done"

print "making list of input shapefile paths..."
dTier3=workspace+"/Output/Tier3_InChannel.shp"
dTier2=workspace+"/Output/Tier2_InChannel.shp"
dConcavity=workspace+"/Output/Tier2_InChannel_Concavity_Membership.tif"
dConvexity=workspace+"/Output/Tier2_InChannel_Convexity_Bars_Membership.tif"
dPlanar=workspace+"/Output/Tier2_InChannel_Planar_Membership.tif"
ddetDEM=workspace+"/Inputs/detDEM.img"
detrended=workspace+"/Inputs/Detrended.tif"
driffles=workspace+"/EvidenceLayers/potentialRiffCrests.shp"
dcontour=workspace+"/EvidenceLayers/contour.shp"
dhillshade=workspace+"/EvidenceLayers/hillshade.tif"

datalist=[dhillshade, dConcavity, dConvexity, dPlanar, dTier3, dTier2, driffles, dcontour]

print "done"


print "setting up mapdoc"
#mapdoc=mapping.MapDocument("E:/GUT/GUT.mxd") #script can run outside of ArcMap
mapdoc=mapping.MapDocument("CURRENT")  # if this is used script must be run from within ArcMap
# I can use execfile(r'E:/GUT/mapping2.py') in the python windo to accomplish this.
print "done"
df = arcpy.mapping.ListDataFrames(mapdoc)[0]

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

#this is my aborted attempt at copying and pasting the Tier 3 level and then attributing on Tier 2...
#def CopyPasteLayer(CopyLayer, PastedLayerName):
 #   mxd = arcpy.mapping.MapDocument("Current")
 #   df = arcpy.mapping.ListDataFrames(mxd)[0]
 #   CopyLayer2 = [arcpy.mapping.Layer(str(CopyLayer))]
 #   CopyLayer2.name = str(PastedLayerName)
 #   InsertRef = [arcpy.mapping.Layer(str(CopyLayer2))]
 #   arcpy.mapping.InsertLayer(df, InsertRef, CopyLayer2, "BEFORE")
 #arcpy.RefreshTOC()
 #arcpy.RefreshActiveView()

#CopyPasteLayer("Tier3_InChannel", "Tier3_InChannel Tier2 Attributed")

#if os.path.exists(datalist[-3])== False:
#    if os.path.exists(datalist[-4])== True:
#        newlayer = arcpy.mapping.Layer(inputlist[-3])
#        arcpy.mapping.InsertLayer(df, "potentialRiffCrests", newlayer, "AFTER")
#        arcpy.mapping.UpdateLayer(df, "potentialRiffCrests", newlayer))

print "now labelling Tier 3..."
lyrlist=arcpy.mapping.ListLayers(mapdoc)
for lyr in lyrlist:
    if lyr.name == "Tier3_InChannel":
        if lyr.supports("LABELCLASSES"):
            print "label classes supported"
            for lblclass in lyr.labelClasses:
                lblclass.className="Tier3"
                lblclass.expression="[Tier3]"
        lyr.showLabels = True
del lyrlist
print "done"

def contourfromDEM(inRaster):
    arcpy.CheckOutExtension("3D")
    if os.path.exists(datalist[-1])== False:
        contourInterval = 0.1
        baseContour = 0
        outContours = workspace + "/EvidenceLayers/contour.shp"
        arcpy.Contour_3d(inRaster, outContours, contourInterval, baseContour)
        # Name: Contour_3d_Ex_02.py
        updateLyr = arcpy.mapping.Layer(datalist[-1])
        if os.path.exists(inputlist[-1]):
            sourceLayer = arcpy.mapping.Layer(inputlist[-1])
            arcpy.mapping.UpdateLayer(df, updateLyr, sourceLayer)
        arcpy.mapping.AddLayer(df,updateLyr,"TOP")
        del updateLyr, sourceLayer
    

def hillshadefromDEM(inRaster):
    if os.path.exists(datalist[0])== False:
        outHillshade = workspace + "/EvidenceLayers/hillshade.tif"
        arcpy.HillShade_3d(inRaster, outHillshade)
        updateLyr = arcpy.mapping.Layer(datalist[0])
        if os.path.exists(inputlist[0]):
            sourceLayer = arcpy.mapping.Layer(inputlist[0])
            arcpy.mapping.UpdateLayer(df, updateLyr, sourceLayer)
        arcpy.mapping.AddLayer(df,updateLyr,"BOTTOM")
        del updateLyr, sourceLayer                                   

print "creating contour and Hillshade layers if missing from detDEM...."

if os.path.exists(workspace + "/Inputs/detDEM.img")==True:
    print "creating Contour and Hillshade layers (if missing) from detDEM.."
    contourfromDEM(workspace+"/Inputs/detDEM.img")
    print "contours finished"
    hillshadefromDEM(workspace+"/Inputs/detDEM.img")
    print "hillshade finished"
else:
    print "did not create due to missing DEM"
    if os.path.exists(workspace + "/Inputs/Detrended.tif")==True:
        print "creating Hillshade layers (if missing)from Detrended.."
        contourfromDEM(workspace+"/Inputs/Detrended.tif")
        print "contours finished"
        hillshadefromDEM(workspace+"/Inputs/Detrended.tif")
        print "hillshade finished"
    else:
        print "did not create due to missing Detrended"

#print "Refreshing Active View"
#arcpy.RefreshActiveView()
#print "done"

#print "now saving"
mapdoc.save() #saves over existing except it isn't working because it says I don't have write access...


print "getting rid of locks on mxd"
del mapdoc, df, datalist, inputlist, layers, workspace # this will unlock the map doc so I can use it again outside of python during rest of script
print "done"
