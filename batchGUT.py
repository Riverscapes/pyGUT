# Geomorphic Unit Tool Batch run script

# Created by: Leif Anderson famousleif@gmail.com

#Folder of visits to run: 
# E:\Box Sync\ET_AL\Projects\USA\ISEMP\GeomorphicUnits\HundredSites\Data\VisitData
startingpath='E:\Box Sync\ET_AL\Projects\USA\ISEMP\GeomorphicUnits\HundredSites\Data\VisitData'

import arcpy
import os
import fnmatch
import tempfile
from arcpy.sa import *
arcpy.CheckOutExtension('Spatial')

import config #config should be a bucket of parameters.
from tier1 import tier1 #imports only the function we want
from tier2 import tier2
from tier3 import tier3

#print(os.listdir(startingpath))

siteslist=os.listdir(startingpath)
siteslist.remove('visitlist.csv')#doesn't erase the file, just removes it from our list.
# siteslist should now contain all the subfolders, nothing else.

#manually ignoring problem sites:
siteslist.remove('VISIT_1008')#no GUT inputs
siteslist.remove('VISIT_1720') #no GUT inputs
siteslist.remove('VISIT_1720') #no GUT inputs
siteslist.remove('VISIT_2447') #ERR in previous run
siteslist.remove('VISIT_2447') #ERR in previous run
siteslist.remove('VISIT_4179') #ERR in previous run
siteslist.remove('VISIT_2898') #ERR in previous run
siteslist.remove('VISIT_1494') #ERR in previous run


for site in siteslist:
    #sitefolder=startingpath+site+'\GUT'
    #freaking slashes, backslashes, gah
    sitefolder=os.path.join(startingpath,site,'GUT')
    config.workspace=sitefolder
    tier1()
    tier2()
    tier3()
    
#with a custom class, this could look like:
#for sitefolder in siteslist:
#   tempsite=site(folder=sitefolder)
#   tempsite.tier1()
