# Code runs summary metrics ---------------------------

# Load required packages ---------------------------

library(tidyverse)
library(ggplot2)
library(ggspatial)
library(ggpubr)
library(purrr)
library(purrrlyr)
library(raster)
library(sf)
library(stars)
library(lwgeom)


# Set required paths ---------------------------

data.path = "C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data"
metric.path = "C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/00_Projectwide/Metrics"
script.path = "C:/etal/LocalCode/pyGUT/SupportingTools/RScripts/Development"
fig.path = "C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/00_Projectwide/Figs"
gut.run = "GUT_2.1/Run_01"

# Create summary of which data exist for each visit  ---------------------------

# load required script
source(file.path(script.path, "check_visit_data.R"))

# get list of all directories
dirs = list.dirs(data.path, recursive = FALSE)

# create tibble of visit directories
visit.dirs = tibble(visit.dir = grep(pattern = "VISIT", dirs, value = TRUE))

# run summary on all visit directories
visit.summary = map_dfr(visit.dirs$visit.dir, check.visit.data, gut.run = gut.run)


# Make spatial data of fish points and habitat polygons from NREI and Fuzzy HSI output ---------------------------

# NKs Note: 2014(i=23),2019(i=24),2021(i=25),2028 (i=28) spatial points are off

# load required scripts
source(file.path(script.path, "create_fish_pts.R"))
source(file.path(script.path, "create_habitat_poly.R"))
source(file.path(script.path, "create_delft_poly.R"))

# create predicted fish and redd location shapefiles
# todo: change plot.nrei parameter back to 'FALSE' after testing
by_row(visit.summary, check.fish.pts, zrank = "max", plot.nrei = TRUE)

# re-run visit summary to update whether the suitable NREI raster now exists on file
visit.summary = map_dfr(visit.dirs$visit.dir, check.visit.data, gut.run = gut.run)

# create habitat polygons
by_row(visit.summary, check.habitat.poly)

# create delft extent polygons
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

# load required script
source(file.path(script.path, "make_gut_maps.R"))

by_row(visit.summary, make.gut.maps, gut.run = gut.run, fig.path = fig.path)


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

# load required script
source(file.path(script.path, "make_site_gut_metrics.R"))

# Tier 2 (hardcoded for transitions)
site.t2.metrics = map_dfr(visit.summary$visit.dir, calc.site.gut.metrics, run.dir = gut.run, gut.layer = "Tier2_InChannel_Transition") %>% 
  bind_rows() %>%
  write_csv(file.path(metric.path, "Site_GUTMetrics_Tier2_InChannel_Transition.csv"), col_names = TRUE)

# Tier 3 
site.t3.metrics = map_dfr(visit.summary$visit.dir, calc.site.gut.metrics, run.dir = gut.run, gut.layer = "Tier3_InChannel_GU") %>% 
  bind_rows() %>%
  write_csv(file.path(metric.path, "Site_GUTMetrics_Tier3_InChannel_GU.csv"), col_names = TRUE)

# Unit GUT metrics ---------------------------
# todo: NK had set sd to zero for items with only one value but this is misleading since really should be NAs

# load required script
source(file.path(script.path, "make_unit_gut_metrics.R"))

# Tier 2 (hardcoded for transitions)
unit.t2.metrics = map_dfr(visit.summary$visit.dir, make.gut.unit.metrics, run.dir = gut.run, gut.layer = "Tier2_InChannel_Transition") %>% 
  bind_rows() %>%
  write_csv(file.path(metric.path, "Unit_GUTMetrics_Tier2_InChannel_Transition.csv"), col_names = TRUE)

# Tier 3 
unit.t3.metrics = map_dfr(visit.summary$visit.dir, make.gut.unit.metrics, run.dir = gut.run, gut.layer = "Tier3_InChannel_GU") %>% 
  bind_rows() %>%
  write_csv(file.path(metric.path, "Unit_GUTMetrics_Tier3_InChannel_GU.csv"), col_names = TRUE)

# Site fish metrics ---------------------------

# load required script
source(file.path(script.path, "make_site_fish_metrics.R"))

site.fish.metrics = map_dfr(visit.summary$visit.dir, calc.site.fish.metrics) %>% 
  bind_rows() %>%
  write_csv(file.path(metric.path, "Site_Fish_Metrics.csv"), col_names = TRUE)

fish.metrics.visit = site.fish.metrics %>%
  unite("variable", c("layer", "var", "category", "species", "lifestage"), sep = ".", remove = TRUE) %>%
  mutate(variable = str_replace_all(variable, ".NA", "")) %>%
  spread(variable, value) %>%
  write_csv(file.path(metric.path, "Site_Fish_Metrics_byVisit.csv"), col_names = TRUE)
  
# Unit fish metrics ---------------------------

# load required script
source(file.path(script.path, "make_unit_fish_metrics.R"))

unit.fish.metrics = map_dfr(visit.summary$visit.dir, make.unit.fish.metrics) %>% 
  bind_rows() %>%
  write_csv(file.path(metric.path, "Unit_Fish_Metrics_Tier2_InChannel_Transition.csv"), col_names = TRUE)
