# Ask NK:
# - why using aggregate function.  it reads raster in at lower cell resolution

#' Create polygon of raster extent
#'
#' @param visit.dir Full filepath to visit folder 
#' @param visit.crs CRS (projection) for visit
#' @param file.name Name of the raster
#' @param out.name Name of the output shapefile
#'
#' @return Creates a extent polygon shapefile from the input raster and saves output to same directory as input raster
#' @export
#'
#' @examples
#' #' create.habitat.poly("C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/VISIT_1027", 
#' "+proj=utm +zone=12 +datum=NAD83 +units=m +no_defs +ellps=GRS80 +towgs84=0,0,0",
#' "delftDepth.tif$", "delftExtent")
create.delft.poly = function(visit.dir, visit.crs, file.name, out.name){
  
  # get path to raster file
  ras.path = unlist(list.files(path = visit.dir, pattern = file.name, full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  
  # read is raster at lower resolution
  ras.agg = aggregate(raster(ras.path))
  
  # relcassify all raster values to 1
  ras.rc = reclassify(ras.agg, c(-Inf, Inf, 1))
  
  # convert to polygon
  poly.rc = rasterToPolygons(ras.rc, dissolve = TRUE)
  
  # write output polygon to esri shapefile
  writeOGR(poly.rc, dirname(ras.path), out.name, driver = "ESRI Shapefile", overwrite_layer = TRUE)
}

#' Checks if delft extent polygon exists.  Creates it using 'delftDepth.tif' if the raster exists.
#'
#' @param data Dataframe created from 'check_visit_data.R' script
#'
#' @return Creates suitable habitat polygons if relevant raster exists but polygon doesn't
#' @export
#'
#' @examples
#' check.delft.poly(visit.summary)
check.delft.poly = function(data){
  
  # - for nrei
  if(data$delft.poly == 'No' & data$delft.raster == 'Yes'){
    create.delft.poly(data$visit.dir, data$visit.crs, "delftDepth.tif$", "delftExtent")
  }
}

check.delft.poly(data)

