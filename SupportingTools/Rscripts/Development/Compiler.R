# Code runs summary metrics ---------------------------

# Load required packages ---------------------------

library(tidyverse)
library(ggplot2)
library(purrr)
library(purrrlyr)
library(raster)
library(sf)

# Set required paths ---------------------------

data.path = "C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data"
metric.path = "C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/00_Projectwide/Metrics"
script.path = "C:/etal/LocalCode/pyGUT/SupportingTools/RScripts/Development"
fig.path = "C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/00_Projectwide/Figs"

# Load required scripts ---------------------------
source(file.path(script.path, "check_visit_data.R"))
source(file.path(script.path, "create_fish_pts.R"))
source(file.path(script.path, "create_habitat_poly.R"))
source(file.path(script.path, "create_delft_poly.R"))
source(file.path(script.path, "create_figures.R"))
source(file.path(script.path, "make_gut_overlay_maps.R"))
source(file.path(script.path, "make_site_gut_metrics.R"))
source(file.path(script.path, "intersect_pts.R"))
source(file.path(script.path, "make_site_fish_metrics.R"))
source(file.path(script.path, "make_unit_fish_metrics.R"))


# Create tibble of data for each visit  ---------------------------

# get list of all directories
dirs = list.dirs(data.path, recursive = FALSE)

# create tibble of visit directories
visit.dirs = tibble(visit.dir = grep(pattern = "VISIT", dirs, value = TRUE))

# subset just for some testing
visit.dirs = visit.dirs %>% slice(2:2)

# create summary of which data exist for each visit
visit.summary = map_dfr(visit.dirs$visit.dir, check.visit.data)

# Make spatial data of fish points and habitat polygons from NREI and HSI output ---------------------------

#2014(i=23),2019(i=24),2021(i=25),2028 (i=28) spatial points are off

# Create predicted fish locations
# todo: change plot.nrei parameter back to 'FALSE' after testing
by_row(visit.summary, check.fish.pts, zrank = "max", plot.nrei = TRUE)

# Re-run visit summary to update whether the suitable NREI raster now exists on file
visit.summary = map_dfr(visit.dirs$visit.dir, check.visit.data)

# Create habitat polygons
by_row(visit.summary, check.habitat.poly)

# Create delft extent polygons
by_row(visit.summary, check.delft.poly)



# Data clean-up and QA/QC ---------------------------

# # commenting this out for now
# # todo: ask NK if she wants this written to a csv and if so over haul
# # these have no predicted juveniles
# for (i in c(1:length(Fishrunlist))){
# if(file.exists(paste(Fishrunlist[i], "\\predFishLocations.shp",sep=""))==F & file.exists(paste(Fishrunlist[i], "\\predFishLocations.csv", sep=""))==T){   
#   visit=extractvisitfrompath(Fishrunlist[i])  
#   fish=read.csv(paste(Fishrunlist[i],"\\predFishLocations.csv", sep=""), stringsAsFactors = FALSE)
#   if(dim(fish)[1]==0){print(paste("visit" , visit, "has no predicted fish"))}
# }
# }
# 
# # these have no predicted redds
# for (i in c(1:length(Fishrunlist))){
#   visit=extractvisitfrompath(Fishrunlist[i])  
#   HSIpath=paste(strsplit(Fishrunlist[i], visit)[[1]][1], visit,"/HSI",sep="")
#   if(file.exists(paste(HSIpath, "/reddPlacement/chkPredReddLocs.shp",sep=""))==F & file.exists(paste(HSIpath, "/reddPlacement/chkPredReddLocs.csv", sep=""))==T){   
#     chk=read.csv(paste(HSIpath, "/reddPlacement/chkPredReddLocs.csv", sep=""), stringsAsFactors = FALSE)
#     if(dim(chk)[1]==0){print(paste("visit" , visit, "has no predicted chk redds"))}
#   }
#     if(file.exists(paste(HSIpath, "/reddPlacement/sthdPredReddLocs.shp",sep=""))==F & file.exists(paste(HSIpath, "/reddPlacement/sthdPredReddLocs.csv", sep=""))==T){   
#       sth=read.csv(paste(HSIpath, "/reddPlacement/sthdPredReddLocs.csv", sep=""), stringsAsFactors = FALSE)
#       if(dim(sth)[1]==0){print(paste("visit" , visit, "has no predicted sth redds"))}
#     }
#   }

# Create maps of fish output overlain on GUT output ---------------------------


# 
# for (i in c(1:length(GUTrunlist))){
#   MakeGUTmaps(GUTrunlist[i],fig.path, form.colors=form.colors, GU.colors=GU.colors,
#               shape.colors=shape.colors, plotfish=T, plotcontour=F, plotthalweg=F)
# } 
# 
# # for this map crop gut the NREI extent...after fixing projection for a couple of sites. -- ?? Not sure what this refers to ??
# 
# for (i in c(1:length(GUTrunlist))){
#   MakeGUTmaps(GUTrunlist[i],fig.path=fig.path, form.colors=form.colors, GU.colors=GU.colors,
#               shape.colors=shape.colors, plotfish=F, plotcontour=T, plotthalweg=T)
# } 
# 
# # These maps have a scale and only show one type of GUT output
# 
# layer="Tier3_InChannel_GU" #Specify which GUT output layer you want to summarize 
# attribute="GU"
# fig.path="E:\\Box Sync\\ET_AL\\Projects\\USA\\ISEMP\\GeomorphicUnits\\Figs\\Maps\\T3withJuv"
# #you have to be connected to the internet for this to work due to a package dependency.  Sorry.
# overlaylist=paste(Fishrunlist, "predFishLocations.shp", sep="/")
# 
# for (i in c(1:length(overlaylist))){
#   print(paste("i=",i, "starting", overlaylist[i]))
#   makeGUToverlaymaps(overlaylist[i],overlaydir="NREI", overlayname="Juveniles", layer, fig.path, Run="Run_01", plotthalweg=F, plotthalwegs=F, plotcontour=F)
# }

#These didn't produce maps prob no GUT 3297, 2898, 2271, 1971

#2014,2019,2021,2028 spatial points are off

# Site GUT metrics ---------------------------


#you have to be connected to the internet for this to work
for (i in c(1:length(GUTrunlist))){
#for (i in runlist){
  print(i)
  v=makesiteGUTmetrics(GUTrunlist[i], layer=paste(layer, ".shp",sep=""))
  if (i==1){metrics=v} else {metrics=rbind(metrics,v)} 
} 

rownames(metrics)=seq(1,length(GUTrunlist))

#metrics1=as.data.frame(metrics)[-c(10,12)]#getsridof EdgeDensAllT runpathfromtable
metrics1=as.data.frame(metrics)
metrics1$ThalwegR=round(1/as.numeric(as.character(metrics1$ThalwegR)),2)

layer="Tier2_InChannel_Transition"
write.csv(metrics1, paste(metric.path, "\\GUTMetrics\\GUT2.1Run01\\siteGUTmetrics_", layer, ".csv" ,sep=""))

layer="Tier3_InChannel_GU"
write.csv(metrics1, paste(metric.path, "\\GUTMetrics\\GUT2.1Run01\\siteGUTmetrics_Tier3GU.csv", sep=""))

#Datacleanup and check

#Fixing and checking stuff


#i=1
#for (i in c(1:length(GUTrunlist))){
#  visit=extractvisitfrompath(GUTrunlist[i])
#  if(i==1){visitlist=visit}else{visitlist=c(visitlist, visit)}
#}

#site=read.csv(paste(metric.path, "\\GUTMetrics\\GUT2.1Run01\\siteGUTmetrics_", layer, ".csv" ,sep=""))
#write.csv(metrics, paste(metric.path, "\\GUTMetrics\\GUT2.1Run01\\siteGUTmetrics_", layer, ".csv" ,sep=""))


#match(visitlist, site$VisitID)
#match(site$VisitID, visitlist)
#length(site$VisitID)
#length(visitlist)

#runlist=which(is.na(metrics1$No.GU))
#GUTrunlist[runlist]
#runvisits=metrics1[runlist,]$VisitID

#metrics=site[-runlist,-1]#removes visits with no Bankfull XS stats

#names(site)[2]="VisitID"
#site=site[,-1]
#site[9,]=v

#list.dirs(data.path)
#GUTrunlist[9]           

# Site GUT unit metrics ---------------------------



for (i in c(1:length(GUTrunlist))){
  v=makesiteGUTunitmetrics(GUTrunlist[i], layer=paste(layer, ".shp",sep=""), attribute=attribute, unitcats=unitcats)
  if (i==1){metrics=v} else {metrics=rbind(metrics,v)} 
} 

metrics1=as.data.frame(metrics)[-c(14)]#getsridof runpathfromtable
if((length(grep("exist", metrics1$Unit))>0)==T){metrics1[-grep("exist", metrics1$Unit),]} #cleans out lines printing that they didn't exist
metrics1[which(metrics1$n==1),]$sdArea=0 #sets sd to zero for items with only one value
metrics1[which(metrics1$n==1),]$sdPerim=0 #sets sd to zero for items with only one value

layer="Tier2_InChannel_Transition"
attribute="UnitForm"
unitcats=formcats
write.csv(metrics1, paste(metric.path, "\\GUTMetrics\\GUT2.1Run01\\siteGUTunitmetrics_", layer, ".csv" ,sep=""))

layer="Tier3_InChannel_GU"  
unitcats=GUcats
attribute="GU"
write.csv(metrics1, paste(metric.path, "\\GUTMetrics\\GUT2.1Run01\\siteGUTunitmetrics_", layer, ".csv", sep=""))

# Site fish metrics ---------------------------


#re-run after HSI hab polys are run.
i=1
for (i in c(42:length(Fishrunlist))){
  print(paste("i=",i))
  v=makesiteFISHmetrics(Fishrunlist[i])
  if (i==1){metrics=v} else {metrics=rbind(metrics,v)} 
}

metrics4=metrics
rownames(metrics4)=seq(1,length(metrics4[,1]))
metrics4=as.data.frame(metrics4)
write.csv(metrics4, paste(metric.path, "\\ReachMetrics\\reachmetrics_fishresponse.csv", sep=""))
str(metrics4)

# By GUT FISH by UNIT ---------------------------
# THIS IS THE ONE I AM MOST INTERSTED IN QA QC

rm(list=ls())



i=1
#ilist=seq(1,100,1)[-c(16,20, 42, 45,54,73,109,112)] Trouble sites
#ilist=c(NA,4,12,19,20,22,32,39)
for (i in c(1:length(GUTrunlist))){
#for (i in c(1:length(ilist))){
  print(paste("i=",i))
  #v=makeUnitFishmetrics(GUTrunlist[ilist[i]], layer=paste(layer, ".shp", sep="") , Model=Model, species=species)
  v=makeUnitFishmetrics(GUTrunlist[i], layer=layer , 
            fig.path=paste(fig.path,"\\Maps\\Fish\\", Model, "\\Tier3GU\\", species, sep=""), Model=Model, species=species, ModelMedians=T)
  if(length(grep("Forc",names(v)))>0){  v1=v[,-grep("Forc",names(v))]}  # Not sure what this does
  if(length(grep("SubGU",names(v1)))>0){v2=v1[,-grep("SubGU",names(v1))]} # Not sure what this does
  if (i==1){metrics=v2} else {metrics=rbind(metrics,v2)} 
}

#cleanup=function(metrics){ 
#  metrics1=metrics[-grep("exist", metrics$UnitID),] #cleans out lines printing that they didn't exist
#  metrics2=metrics1[-grep("extent", metrics$UnitID),] #cleans out lines printing that delft extent was missing
#  metrics1=metrics[which(is.na(metrics1$UnitID)),] #cleans out lines with UnitID=NA
#}
#cleanup(metrics2)

# NREI ---------------------------

Model="NREI"
species=""

#layer="Tier2_InChannel_Transition"
#UnitIDT2=cleanup(metrics)
#write.csv(UnitIDT2, paste(metric.path, "\\GUTMetrics\\GUT2.1Run01\\UnitID_Juvmetrics_", layer, ".csv" ,sep=""))
#str(metrics)

layer="Tier3_InChannel_GU" #48-104,106 hab not found then pred fsh not found
metrics1=metrics[,-c(4:13,15:20)]
metrics2=metrics1[-c(which(is.na(metrics1$GU)& is.na(metrics1$No.Fish)& metrics1$No.FishBest==0) ),]
metrics3=metrics2[-c(which(is.na(metrics2$GU)& metrics2$No.Fish==0) ),]
metrics4=metrics3[-(which(is.na(metrics3$GU) & metrics3$UnitID==1)),] #gets rid of sliver of unidentified GU with no fish. Visit 547
metrics5=metrics4[-c(which(is.na(metrics4$GU))[c(4:6,13,22:23)]),]#gets rid of repeated entries for NA Unit IDs with no Delft exnt
badspatial=c(which(metrics5$VisitID==2014 | metrics5$VisitID==2019 |metrics5$VisitID==2021|metrics5$VisitID==2026|metrics5$VisitID==2028 ))
metrics6=metrics5
metrics6[badspatial,5:11]=NA #gets rid of visits with bad spatial alignment

write.csv(metrics6, paste(metric.path, "\\GUTMetrics\\GUT2.1Run01\\UnitID_NREImetrics_", layer, ".csv" ,sep=""), row.names=F)

dim(metrics5)

# HSI STHD, GU ---------------------------

layer="Tier3_InChannel_GU"
Model="HSI"
species="chnk"

#metrics1=metrics #does not include i 14 (different T3 Fields, rbind failed)
#metrics0=metrics[-grep("exist", metrics$UnitID),] #cleans out lines printing that they didn't exist
metrics0=metrics0[-which(is.na(metrics0$UnitID)),] #cleans out lines with GU=NA

write.csv(metrics1, paste(metric.path, "\\GUTMetrics\\GUT2.1Run01\\UnitID_",Model, species, "metrics_", layer, ".csv" ,sep=""))
str(metrics)

layer="Tier3_InChannel_GU"
Model="HSI"
species="chnk"

#metrics1=metrics #does not include i 14 (different T3 Fields, rbind failed)
#metrics0=metrics[-grep("exist", metrics$UnitID),] #cleans out lines printing that they didn't exist
metrics0=metrics0[-which(is.na(metrics0$UnitID)),] #cleans out lines with GU=NA

write.csv(metrics1, paste(metric.path, "\\GUTMetrics\\GUT2.1Run01\\UnitID_",Model, species, "metrics_", layer, ".csv" ,sep=""))
str(metrics)

