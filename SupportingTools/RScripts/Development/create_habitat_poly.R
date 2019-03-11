# Ask NK:
# - why using aggregate function.  it reads raster in at lower cell resolution

#' Create suitable habitat polygon from raster using breaks in data
#'
#' @param visit.dir Full filepath to visit folder 
#' @param ref.shp Reference shapefile for visit used to set CRS (projection) for output shapefile
#' @param file.name Name of the raster
#' @param out.name Name of the output shapefile
#'
#' @return Creates a polygon shapefile from the input raster (using breaks) and saves output to same directory as input raster
#' @export
#'
#' @examples
#' #' create.habitat.poly("C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/VISIT_1027", 
#' "^Thalweg.shp$", "suitableNreiRaster.tif", "suitableNreiPoly")
create.habitat.poly = function(visit.dir, ref.shp, file.name, out.name){
  
  # get path to raster file
  ras.path = unlist(list.files(path = visit.dir, pattern = file.name, full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  
  # read in raster
  ras = raster(ras.path)
  
  # set raster crs (raster package does not always read in datum)
  crs(ras) = crs(ref.shp)
  
  # read is raster at lower resolution
  ras.agg = aggregate(ras)
  
  # set breaks for splitting raster
  # - if nrei raster use median and max
  # - otherwise set to (0.4, 0.8, 1) -- this assumes fuzzy hsi raster
  if(out.name == "suitableNreiPoly.shp"){
    ras.median = cellStats(ras.agg, median)
    ras.max = cellStats(ras.agg, max)
    ras.breaks = c(0, ras.median, ras.max)
  }else{
    ras.breaks = c(0.4, 0.8, 1.0)
  }
  
  # splits into 2 classes based on breaks
  ras.cut = cut(ras.agg, breaks = ras.breaks)
  
  # convert to polygon
  poly.cut = rasterToPolygons(ras.cut, dissolve = TRUE) %>% st_as_sf() %>% st_transform(crs = (st_crs(ref.shp)), partial = FALSE)
  
  # write output polygon to esri shapefile
  st_write(poly.cut, file.path(dirname(ras.path), out.name), delete_layer = TRUE)

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
  
  # set reference shp
  ref.shp.path = unlist(list.files(path = data$visit.dir, pattern = "^Thalweg.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  ref.shp = st_read(ref.shp.path, quiet = TRUE)
  
  # - for nrei
  if(data$suit.nrei.poly == 'No' & data$suit.nrei.raster == 'Yes'){
    create.habitat.poly(data$visit.dir, ref.shp, "suitableNreiRaster.tif$", "suitableNreiPoly.shp")
  }
  
  # - for chinook spawner fuzzy hsi
  if(data$ch.suit.poly == 'No' & data$ch.raster == 'Yes'){
    create.habitat.poly(data$visit.dir, ref.shp, "FuzzyChinookSpawner_DVSC.tif$", "suitableChnkPoly.shp")
  }
  
  # - for steelhead spawner fuzzy hsi
  if(data$st.suit.poly == 'No' & data$st.raster == 'Yes'){
    create.habitat.poly(data$visit.dir, ref.shp, "FuzzySteelheadSpawner_DVSC.tif$", "suitableSthdPoly.shp")
  }  
}
