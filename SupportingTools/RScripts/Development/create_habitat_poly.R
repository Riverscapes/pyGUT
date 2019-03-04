# Ask NK:
# - why using aggregate function.  it reads raster in at lower cell resolution

#' Create suitable habitat polygon from raster using breaks in data
#'
#' @param visit.dir Full filepath to visit folder 
#' @param visit.crs CRS (projection) for visit
#' @param file.name Name of the raster
#' @param out.name Name of the output shapefile
#'
#' @return Creates a polygon shapefile from the input raster (using breaks) and saves output to same directory as input raster
#' @export
#'
#' @examples
#' #' create.habitat.poly("C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/VISIT_1027", 
#' "+proj=utm +zone=12 +datum=NAD83 +units=m +no_defs +ellps=GRS80 +towgs84=0,0,0",
#' "suitableNreiRaster.tif", "suitableNreiPoly")
create.habitat.poly = function(visit.dir, visit.crs, file.name, out.name){
  
  # get path to raster file
  ras.path = unlist(list.files(path = visit.dir, pattern = file.name, full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  
  # read is raster at lower resolution
  ras.agg = aggregate(raster(ras.path))
  
  # set breaks for splitting raster
  # - if nrei raster use median and max
  # - otherwise set to (0.4, 0.8, 1) -- this assumes fuzzy hsi raster
  if(out.name == "suitableNreiPoly"){
    ras.median = cellStats(ras.agg, median)
    ras.max = cellStats(ras.agg, max)
    ras.breaks = c(0, ras.median, ras.max)
  }else{
    ras.breaks = c(0.4, 0.8, 1.0)
  }
  
  # splits into 2 classes based on breaks
  ras.cut = cut(ras.agg, breaks = ras.breaks)
  
  # convert to polygon
  poly.cut = rasterToPolygons(ras.cut, dissolve = TRUE)
  
  # write output polygon to esri shapefile
  writeOGR(poly.cut, dirname(ras.path), out.name, driver = "ESRI Shapefile", overwrite_layer = TRUE)

}

#' Checks if NREI and/or Fuzzy HIS suitable habitat polygons exist.  Creates them if input raster data exists.
#'
#' @param data Dataframe created from 'check_visit_data.R' script
#'
#' @return Creates suitable habitat polygons if relevant raster exists but polygon doesn't
#' @export
#'
#' @examples
#' check.habitat.poly(visit.summary)
check.habitat.poly = function(data){
  
  # - for nrei
  if(data$suit.nrei.poly == 'No' & data$suit.nrei.raster == 'Yes'){
    create.habitat.poly(data$visit.dir, data$visit.crs, "suitableNreiRaster.tif$", "suitableNreiPoly")
  }
  
  # - for chinook spawner fuzzy hsi
  if(data$ch.suit.poly == 'No' & data$ch.raster == 'Yes'){
    create.habitat.poly(data$visit.dir, data$visit.crs, "FuzzyChinookSpawner_DVSC.tif$", "suitableChnkPoly")
  }
  
  # - for steelhead spawner fuzzy hsi
  if(data$st.suit.poly == 'No' & data$st.raster == 'Yes'){
    create.habitat.poly(data$visit.dir, data$visit.crs, "FuzzySteelheadSpawner_DVSC.tif$", "suitableSthdPoly")
  }  
}

check.habitat.poly(data)

