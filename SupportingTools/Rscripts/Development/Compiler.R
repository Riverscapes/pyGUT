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

# write out visit summary
write_csv(visit.summary, file.path(metric.path, "VisitSummary.csv"), col_names = TRUE)


# Make spatial data of fish points and habitat polygons from NREI and Fuzzy HSI output ---------------------------

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


# Create maps of fish output overlain on GUT output ---------------------------

# load required script
source(file.path(script.path, "make_gut_maps.R"))

by_row(visit.summary, make.gut.maps, gut.run = gut.run, fig.path = fig.path)


#These didn't produce maps prob no GUT 3297, 2898, 2271, 1971

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
