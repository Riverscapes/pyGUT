# Ask NK:
# - why using aggregate function.  it reads raster in at lower cell resolution

#' Create polygon of raster extent
#'
#' @param visit.dir Full filepath to visit folder 
#' @param ref.shp Reference shapefile for visit used to set CRS (projection) for output shapefile
#' @param file.name Name of the raster
#' @param out.name Name of the output shapefile
#'
#' @return Creates a extent polygon shapefile from the input raster and saves output to same directory as input raster
#' @export
#'
#' @examples
#' #' create.habitat.poly("C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/VISIT_1027", 
#' "^Thalweg.shp$", "delftDepth.tif$", "delftExtent")
create.delft.poly = function(visit.dir, ref.shp, file.name, out.name){
  
  # get path to raster file
  ras.path = unlist(list.files(path = visit.dir, pattern = file.name, full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  
  # read is raster at lower resolution
  ras.agg = aggregate(raster(ras.path))
  
  # relcassify all raster values to 1
  ras.rc = reclassify(ras.agg, c(-Inf, Inf, 1))
  
  # convert to polygon and transform to correct coordinate system for visit
  poly.rc = rasterToPolygons(ras.rc, dissolve = TRUE) %>% st_as_sf() %>% st_transform(crs = (st_crs(ref.shp)), partial = FALSE)
  
  # write output polygon to esri shapefile
  st_write(poly.rc, file.path(dirname(ras.path), out.name), delete_layer = TRUE)
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
    
    # set reference shp
    ref.shp.path = unlist(list.files(path = data$visit.dir, pattern = "^Thalweg.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
    ref.shp = st_read(ref.shp.path, quiet = TRUE)
    
    create.delft.poly(data$visit.dir, ref.shp, "delftDepth.tif$", "delftExtent.shp")
  }
}

