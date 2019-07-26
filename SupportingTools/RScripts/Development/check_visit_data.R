#' Check visit folder for file
#'
#' @param visit.dir Full filepath to visit folder
#' @param file.name Name of file to search for
#' @param gut.run Name of gut run
#'
#' @return 'Outputs 'have.file' variable with 'Yes' if file exists and 'No' if it does not exist 
#' @export
#'
#' @examples
#' check.data("C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/VISIT_1027", ""NREI_All_Pts.shp")
#' 
check.data = function(visit.dir, file.name, gut.run = NA){
  
  files = unlist(list.files(path = visit.dir, pattern = file.name, recursive = TRUE, include.dirs = FALSE))
  if(!is.na(gut.run)){files = grep(gut.run, files, value = TRUE)}
  
  if(length(files) > 0){
    have.file = 'Yes'
  }else{
    have.file = 'No'
  }
  
  return(have.file)
  
}  

#' Create tibble of data for each visit
#'
#' @param visit.dir Full filepath to visit folder 
#'
#' @return A tibble with visit path, visit ID, visit CRS, and 'Yes/No' if files found
#' @export
#'
#' @examples
#' check.visit.data("C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/VISIT_1027")
#' 
check.visit.data = function(visit.dir, gut.run){
  
  # get visit id from visit directory
  visit.id = as.numeric(unlist(str_split(visit.dir, "VISIT_"))[2])
  
  # search for relevant data (shapefiles, csvs, rasters):
  
  # - nrei juvenile predicted fish locations
  nrei.locs.csv = check.data(visit.dir, "^predFishLocations.csv$")
  nrei.locs.shp = check.data(visit.dir, "^NREI_FishLocs.shp$")
  
  # - nrei all data
  all.nrei.pts.csv = check.data(visit.dir, "^allNreiPts.csv$")
  all.nrei.pts.shp = check.data(visit.dir, "^NREI_All_Pts.shp$")
  
  # - suitable nrei data
  suit.nrei.pts.shp = check.data(visit.dir, "^NREI_Suitable_Pts.shp$")
  suit.nrei.poly = check.data(visit.dir, "^NREI_Suitable_Poly.shp$")
  suit.nrei.raster = check.data(visit.dir, "^NREI_Suitable_Ras.tif$")
  
  # - chinook spawner data
  ch.redd.locs.csv = check.data(visit.dir, "^ChinookSpawner_PredReddLocations.csv$")
  ch.redd.locs.shp = check.data(visit.dir, "^Fuzzy_ReddLocs_Chinook.shp$")
  ch.suit.poly = check.data(visit.dir, "^Fuzzy_Suitable_Poly_Chinook.shp$")
  ch.raster = check.data(visit.dir, "^FuzzyChinookSpawner_DVSC.tif$")
  
  # - chinook juvenile data
  ch.juv.locs.csv = check.data(visit.dir, "^ChinookJuvenile_PredFishLocations.csv$")
  ch.juv.locs.shp = check.data(visit.dir, "^Fuzzy_JuvenileLocs_Chinook.shp$")
  ch.juv.suit.poly = check.data(visit.dir, "^Fuzzy_Suitable_Poly_ChinookJuvenile.shp$")
  ch.juv.raster = check.data(visit.dir, "^FuzzyChinookJuvenile_DVS.tif$")
  
  # - steelhead spawner locations
  st.redd.locs.csv = check.data(visit.dir, "^SteelheadSpawner_PredReddLocations.csv$")
  st.redd.locs.shp = check.data(visit.dir, "^Fuzzy_ReddLocs_Steelhead.shp$")
  st.suit.poly = check.data(visit.dir, "^Fuzzy_Suitable_Poly_Steelhead.shp$")
  st.raster = check.data(visit.dir, "^FuzzySteelheadSpawner_DVSC.tif$")
  
  # - delft data
  delft.poly = check.data(visit.dir, "^Delft_Extent.shp$")
  delft.raster = check.data(visit.dir, "^delftDepth.tif$")
  
  # - gut output
  gut.t2 = check.data(visit.dir, "^Tier2_InChannel.shp$", gut.run = gut.run)
  gut.t2.trans = check.data(visit.dir, "^Tier2_InChannel_Transition.shp$", gut.run = gut.run)
  gut.t3 = check.data(visit.dir, "^Tier3_InChannel_GU.shp$", gut.run = gut.run)

  data = tibble(visit.dir, visit.id, nrei.locs.csv, nrei.locs.shp, all.nrei.pts.csv, all.nrei.pts.shp, 
                suit.nrei.pts.shp, suit.nrei.poly, suit.nrei.raster, 
                ch.redd.locs.csv, ch.redd.locs.shp, ch.suit.poly, ch.raster,
                ch.juv.locs.csv, ch.juv.locs.shp, ch.juv.suit.poly, ch.juv.raster,
                st.redd.locs.csv, st.redd.locs.shp, st.suit.poly, st.raster, 
                delft.raster, delft.poly, 
                gut.run, gut.t2, gut.t2.trans, gut.t3)
  
  return(data)
  
}
