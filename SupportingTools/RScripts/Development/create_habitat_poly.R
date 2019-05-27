# Ask NK:
# - why using aggregate function.  it reads raster in at lower cell resolution

#' Create suitable habitat polygon from raster using breaks in data
#'
#' @param visit.dir Full filepath to visit folder 
#' @param ref.shp Reference shapefile for visit used to set CRS (projection) for output shapefile
#' @param file.name Name of the raster
#' @param out.name Name of the output shapefile
#'
#' @return Creates a extent polygon shapefile from the input raster and a olygon shapefile from the input raster (using breaks) and saves output to same directory as input raster.
#' @export
#'
#' @examples
#' #' create.habitat.poly("C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/VISIT_1027", 
#' "^Thalweg.shp$", "NREI_Suitable_Ras.tif", "NREI_Suitable_Poly.shp")
create.habitat.poly = function(visit.dir, ref.shp, file.name, out.name, out.extent.name = NA){
  
  # get path to raster file
  ras.path = unlist(list.files(path = visit.dir, pattern = file.name, full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  
  # read in raster
  in.ras = raster(ras.path)
  
  # replace any negative values with NA
  ras = reclassify(in.ras, c(-Inf, 0, NA), right = FALSE)
  
  # set raster crs (raster package does not always read in datum)
  crs(ras) = crs(ref.shp)
  
  # set breaks for splitting raster
  # - if nrei raster use median and max
  # - otherwise set to (0.4, 0.8, 1) -- this assumes fuzzy hsi raster
  if(out.name == "NREI_Suitable_Poly.shp"){
    ras.median = cellStats(ras, median)
    ras.max = cellStats(ras, max)
    ras.breaks = c(0, ras.median, ras.max)
  }else{
    ras.breaks = c(0.4, 0.8, 1.0)
  }
  
  # splits into 2 classes based on breaks
  ras.cut = cut(ras, breaks = ras.breaks)
  ras.max = cellStats(ras.cut, stat = "max", na.rm = TRUE)
  
  # if ras.cut raster isn't all NAs then convert to polygons and save output
  # note: entire raster of NAs will only occur is nrei raster values are all negative or fuzzy raster values < 0.4
  if(ras.max >= 0){
    # convert to polygon
    ras.cut.s = st_as_stars(ras.cut, crs = crs(ref.shp))
    poly.cut = st_as_sf(ras.cut.s, as_points = FALSE, merge = TRUE, na.rm = TRUE, use_integer = TRUE) %>% 
      group_by(layer) %>%
      summarize() %>%
      st_transform(crs = (st_crs(ref.shp)), partial = FALSE)
    # poly.cut = rasterToPolygons(ras.cut, na.rm = TRUE, dissolve = TRUE) %>% st_as_sf()
    
    # write output polygon to esri shapefile
    st_write(poly.cut, file.path(dirname(ras.path), out.name), delete_layer = TRUE)
  }
  
  if(!is.na(out.extent.name)){
    # relcassify all raster values to 1
    ras.rc = reclassify(in.ras, c(-Inf, Inf, 1))
    
    # convert to polygon and transform to correct coordinate system for visit
    ras.rc.s = st_as_stars(ras.rc, crs = crs(ref.shp))
    poly.rc = st_as_sf(ras.rc.s, as_points = FALSE, merge = TRUE) %>%
      group_by(layer) %>%
      summarize() %>%
      st_transform(crs = (st_crs(ref.shp)), partial = FALSE)
    
    # write output polygon to esri shapefile
    st_write(poly.rc, file.path(dirname(ras.path), out.extent.name), delete_layer = TRUE)
  }
}

#' Checks if NREI and/or Fuzzy Habitat Quality (FHQ) suitable habitat polygons exist.  Creates them if input raster data exists.
#'
#' @param data Dataframe created from 'check_visit_data.R' script
#'
#' @return Creates suitable habitat polygons if relevant raster exists but polygon doesn't
#' @export
#'
#' @examples
#' check.habitat.poly(visit.summary)
check.habitat.poly = function(data){
  
  print(data$visit.dir)
  
  # set reference shp
  ref.shp.path = unlist(list.files(path = data$visit.dir, pattern = "^Thalweg.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  ref.shp = st_read(ref.shp.path, quiet = TRUE)
  
  # - for nrei
  if(data$suit.nrei.poly == 'No' & data$suit.nrei.raster == 'Yes'){
    create.habitat.poly(data$visit.dir, ref.shp, "^NREI_Suitable_Ras.tif$", "NREI_Suitable_Poly.shp")
  }
  
  # - for chinook spawner fuzzy hsi
  if(data$ch.suit.poly == 'No' & data$ch.raster == 'Yes'){
    create.habitat.poly(data$visit.dir, ref.shp, "^FuzzyChinookSpawner_DVSC.tif$", "Fuzzy_Suitable_Poly_Chinook.shp", "Fuzzy_Chinook_Extent.shp")
  }
  
  # - for steelhead spawner fuzzy hsi
  if(data$st.suit.poly == 'No' & data$st.raster == 'Yes'){
    create.habitat.poly(data$visit.dir, ref.shp, "^FuzzySteelheadSpawner_DVSC.tif$", "Fuzzy_Suitable_Poly_Steelhead.shp", "Fuzzy_Steelhead_Extent.shp")
  }  
}
