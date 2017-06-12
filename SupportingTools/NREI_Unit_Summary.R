units = "C:/et_al/Shared/Projects/USA/CHaMP/ResearchProjects/TopographicGUs/wrk_Data/01_TestSites/Wenatchee/LWIN0001-000041/2014/VISIT_2632/ModelRuns/Output/GUT_2.0/Run_001/Tier2_InChannel.shp"
nrei.fishlocs = read.csv("C:/et_al/Shared/Projects/USA/CHaMP/ResearchProjects/TopographicGUs/wrk_Data/01_TestSites/Wenatchee/LWIN0001-000041/2014/VISIT_2632/FHM/NREI/VISIT_2632_predFishLocations.csv", header = TRUE, stringsAsFactors = FALSE)
nrei.pts = read.csv("C:/et_al/Shared/Projects/USA/CHaMP/ResearchProjects/TopographicGUs/wrk_Data/01_TestSites/Wenatchee/LWIN0001-000041/2014/VISIT_2632/FHM/NREI/VISIT_2632_allNreiPts.csv", header = TRUE, stringsAsFactors = FALSE)
out.folder = 'C:/et_al/Shared/Projects/USA/CHaMP/ResearchProjects/TopographicGUs/wrk_Data/01_TestSites/Wenatchee/LWIN0001-000041/2014/VISIT_2632/FHM'

nrei.summary.fn = function(){
  
  # check if required packages are installed
  # if they aren't then install them
  if (!'rgdal' %in% installed.packages()) install.packages('rgdal')
  if (!'rgeos' %in% installed.packages()) install.packages('rgeos')
  if (!'raster' %in% installed.packages()) install.packages('raster')
  if (!'tidyverse' %in% installed.packages()) install.packages('tidyverse')
  if (!'moments' %in% installed.packages()) install.packages('moments')
  
  # load required packages
  library(rgdal)
  library(rgeos)
  library(raster)
  library(tidyverse)
  library(moments)
  
  # read in units as spatial polygons dataframe
  units.spdf = readOGR(units)
    
  # if 'UnitID' or 'Area' field isn't present create it
  units.spdf@data = units.spdf@data %>%
    mutate(UnitID = if (exists('UnitID', where = .)) UnitID else rownames(.),
           Area = if (exists('Area', where = .)) Area else area(units.spdf))
  
  # join nrei data into spatial points data frame
  # add 'fish.loc' column - assign '1' to xy with fish [can't have >1 fish in a xy] and '0' to xy without fish
  # remove champ channel unit number/area/length fields added by eric
  nrei.spdf = nrei.fishlocs %>% 
    mutate(fish.loc = 1) %>%
    dplyr::select(idx, fish.loc) %>%
    right_join(nrei.pts, by = 'idx') %>%
    mutate(fish.loc = ifelse(is.na(fish.loc), 0, fish.loc)) %>%
    select(-Unit_Number, -Shape_Length, -Shape_Area) %>%
    SpatialPointsDataFrame(coords = cbind(.$X, .$Y), data = ., proj4string = CRS(proj4string(units.spdf)))
                          
  
  # assign unit polygon id to each nrei pt
  # remove unecesssary columns
  nrei.units = cbind(nrei.spdf@data, over(nrei.spdf, units.spdf)) %>%
    select(idx, fish.loc, X, Y, Z, nrei_js, UnitID, Area)
  
  write.csv(nrei.units, file.path(out.folder, 'nrei_points_UnitID.csv'), row.names = FALSE)
  
  # create separate df for xy points where fish are located
  nrei.fishloc.units = nrei.units %>% filter(fish.loc == 1)
  
  # nrei summary for each unit
  nrei.summary = nrei.units %>% 
    group_by(UnitID) %>%
    summarise(nrei.n.pts = n(),
              nrei.min = round(min(nrei_js), 4),
              nrei.med = round(median(nrei_js), 4),
              nrei.max = round(max(nrei_js), 4),
              nrei.mean = round(mean(nrei_js), 4),
              nrei.sd = round(sd(nrei_js), 4),
              nrei.skew = round(skewness(nrei_js), 4),
              nrei.kurt = round(kurtosis(nrei_js), 4))
  
  # nrei summary for fish locations
  nrei.fishloc.summary = nrei.fishloc.units %>% 
    group_by(UnitID, Area) %>%
    summarise(nrei.n.fish = sum(fish.loc), 
              nrei.fish.min = round(min(nrei_js), 4),
              nrei.fish.med = round(median(nrei_js), 4),
              nrei.fish.max = round(max(nrei_js), 4),
              nrei.fish.mean = round(mean(nrei_js), 4),
              nrei.fish.sd = round(sd(nrei_js), 4),
              nrei.fish.skew = round(skewness(nrei_js), 4),
              nrei.fish.kurt = round(kurtosis(nrei_js), 4)) %>%
    mutate(nrei.fish.dens.m2 = round(nrei.n.fish/Area), 4) 
  
  # join both summaries into single df
  out.summary = nrei.summary %>% left_join(nrei.fishloc.summary, by = c('UnitID'))
  
  write.csv(out.summary, file.path(out.folder, 'nrei_gu_summary.csv'), row.names = FALSE)
  
  # # plot unit data
  # plot.data = out.summary %>%
  #   left_join(units.spdf@data, by = 'UnitID')
  # 
  # p1 = ggplot(plot.data, aes(x = Tier2, y = nrei.fish.dens.m2)) +
  #   geom_boxplot()
}

nrei.summary.fn()
