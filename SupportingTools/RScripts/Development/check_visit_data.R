#' Check visit folder for file
#'
#' @param visit.dir Full filepath to visit folder
#' @param file.name Name of file to search for
#'
#' @return 'Outputs 'have.file' variable with 'Yes' if file exists and 'No' if it does not exist 
#' @export
#'
#' @examples
#' check.data("C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/VISIT_1027", ""allNreiPts.shp")
#' 
check.data = function(visit.dir, file.name){
  

  if(length(unlist(list.files(path = visit.dir, pattern = file.name, recursive = TRUE, include.dirs = FALSE))) > 0){
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
check.visit.data = function(visit.dir){
  
  # get visit id from visit directory
  visit.id = as.numeric(unlist(str_split(visit.dir, "VISIT_"))[2])
  
  # get visit crs from thalweg shp in gut inputs
  
  # - search for thalweg shapefile
  have.thalweg = check.data(visit.dir, "Thalweg.shp")
  
  # if there's a thawleg shapefile get the crs
  if(have.thalweg == "Yes"){
    thalweg.path = unlist(list.files(path = visit.dir, pattern = "Thalweg.shp", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))[1]
    thalweg.shp = readOGR(dirname(thalweg.path), unlist(str_split(basename(thalweg.path), "\\."))[1])
    visit.crs = proj4string(thalweg.shp)
  }else{
    visit.crs = NA
  }
  
  # search for relevant shapefiles and csvs:
  
  # - nrei juvenile predicted fish locations
  nrei.locs.csv = check.data(visit.dir, "predFishLocations.csv")
  nrei.locs.shp = check.data(visit.dir, "predFishLocations.shp")
  
  # - nrei all points
  all.nrei.pts.csv = check.data(visit.dir, "allNreiPts.csv")
  all.nrei.pts.shp = check.data(visit.dir, "allNreiPts.shp")
  
  # - suitable nrei points
  suit.nrei.pts.shp = check.data(visit.dir, "suitableNreiPts.shp")
  
  # - chinook redd locations
  ch.redd.locs.csv = check.data(visit.dir, "chkPredReddLocs.csv")
  ch.redd.locs.shp = check.data(visit.dir, "chkPredReddLocs.shp")
  
  # - steelhead redd locations
  st.redd.locs.csv = check.data(visit.dir, "sthdPredReddLocs.csv")
  st.redd.locs.shp = check.data(visit.dir, "sthdPredReddLocs.shp")
  

  data = tibble(visit.dir, visit.id, visit.crs, nrei.locs.csv, nrei.locs.shp, all.nrei.pts.csv, all.nrei.pts.shp, suit.nrei.pts.shp,
                ch.redd.locs.csv, ch.redd.locs.shp, st.redd.locs.csv, st.redd.locs.shp)
  
  return(data)
  
}

check.visit.data(visit.dir)

