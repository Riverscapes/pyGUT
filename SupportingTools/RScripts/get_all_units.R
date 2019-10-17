library(sf)
library(tidyverse)
require(stringr)

pf = "C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data"
out.f = 'C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/00_Projectwide/Metrics'


# get list of all directories
dirs = list.dirs(data.path, recursive = FALSE)

# create tibble of visit directories
visit.dirs = tibble(visit.dir = grep(pattern = "VISIT", dirs, value = TRUE))


runCheck.fn = function(x, pattern){
  
  print(x)
  
  visit.id = as.numeric(str_split(x, "VISIT_")[[1]][2])
  
  shp = list.files(as.character(x), pattern, recursive = TRUE, full.names = TRUE)
  print(shp)
  if(length(shp) > 0){
    shp.df = st_read(shp) %>% st_drop_geometry() %>% mutate(VisitID = visit.id)
  }
  
 
  return(shp.df)
  
}

map_dfr(visit.dirs$visit.dir, runCheck.fn, pattern = "Tier2_InChannel.shp$") %>%
  bind_rows() %>% 
  write_csv(file.path(out.f, "AllVisits_Tier2_InChannel.csv"))

map_dfr(visit.dirs$visit.dir, runCheck.fn, pattern = "Tier3_InChannel_GU.shp$") %>%
  bind_rows() %>% 
  write_csv(file.path(out.f, "AllVisits_Tier3_InChannel_GU.csv"))

