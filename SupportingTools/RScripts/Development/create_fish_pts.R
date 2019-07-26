# todo: filter nrei points by rad.step.gte.user.pval > 0.4

# ask NK: had filter to select rows with rad.step.gte.user.pval > 0, but aren't any rows that meet this condition
#         there are rows with NA values.  should those be removed?  not sure what this field pertains to. also...
#         not all visits have this field (e.g., visit 1587 NREI all pts doesn't have pval fields)

# note: some of the redd locs csvs produced by eric are empty.  i still read them in, but it the nrow for csv is 0
#       then shp is no longer written (no point in creating a empty shapefile).  however, a warning is produced 
#       e.g., "In min(x[[coords[1]]], na.rm = TRUE) : no non-missing arguments, returning NA"

#' Create points shapefile from csv
#'
#' @param visit.dir Full filepath to visit folder 
#' @param ref.shp Reference shapefile for visit used to set CRS (projection) for output shapefile
#' @param file.name Name of the csv
#' @param out.name Name of the output shapefile
#'
#' @return Creates a points shapefile from the csv and saves output to same directory as csv
#' @export
#'
#' @examples
#' create.pts("C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/VISIT_1027", 
#' "^Thalweg.shp$", "predFishLocations.csv", "NREI_FishLocs.shp")
create.pts = function(visit.dir, ref.shp, file.name, out.name){
  
  # get path to pts csv
  pts.csv = unlist(list.files(path = visit.dir, pattern = file.name, full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  
  # read in pts csv and convert to shp
  # note: need separate parsing call for NREI All Points bc read_csv only looks at first 1000 rows (if all NA column read as logical which don't want)
  if(out.name == "NREI_All_Pts.shp"){
    pts = read_csv(pts.csv, col_types = cols(.default = col_double())) %>%
      rename_at(vars(matches("^x$")), funs(str_replace(., "x", "X"))) %>%
      rename_at(vars(matches("^y$")), funs(str_replace(., "y", "Y"))) %>% 
      st_as_sf(coords = c("X", "Y"), crs = (st_crs(ref.shp)), remove = FALSE)
  }else{
    pts = read_csv(pts.csv) %>%
      rename_at(vars(matches("^x$")), funs(str_replace(., "x", "X"))) %>%
      rename_at(vars(matches("^y$")), funs(str_replace(., "y", "Y"))) %>% 
      st_as_sf(coords = c("X", "Y"), crs = (st_crs(ref.shp)), remove = FALSE)
  }

  # save output shp
  if(nrow(pts) > 0){st_write(pts, file.path(dirname(pts.csv), out.name), delete_layer = TRUE)}
  
}


#' Checks if fish/redd points shapefile exists.  Creates relevant shapefile if csv input data exists.
#'
#' @param data Dataframe created from 'check_visit_data.R' script
#' @param zrank Value user to select single NREI value for each xy point.  Either set to "max" or numeric value.
#' @param plot.nrei If set to TRUE will output suitable NREI points shapefile and raster
#'
#' @return
#' Returns following if shapefiles if they don't exist on file:
#' NREI_FishLocs.shp: ESRI shapefile of predicted fish points from predFishLocations.csv
#' Fuzzy_ReddLocs_Chinook.shp: ESRI Shapefile of predicted Chinook redd locations from ChinookSpawner_PredReddLocations.csv
#' Fuzzy_ReddLocs_Steelhead.shp: ESRI Shapefile of predicted steelhead redd locations from SteelheadSpawner_PredReddLocations.csv
#' Fuzzy_JuvenileLocs_Chinook.shp: ESRI Shapefile of predicted steelhead redd locations from ChinookJuvenile_PredFishLocations.csv
#' NREI_All_Pts.shp: ESRI Shapefile of all NREI pts from allNreiPts.csv
#' 
#' Returns folloiwng if files don't exist and 'plot.nrei' argument set to TRUE
#' NREI_Suitable_Pts.shp: ESRI Shapefile of NREI pts > 0 and above 40% pval threshold. 
#'                      These are the pool of points that the predicted fish locs were chosen from
#'                      Only one point per x,y is chosen based on optional argument zrank
#'                      zrank="max" which takes the maximum NREI from the water column at each location
#'                      zrank="XX" takes a number specifying the water column placement. 1 = bed of stream.
#' NREI_Suitable_Ras.tif: GeoTiff created from SuitableNreiPts.shp. Used to create habitat polygons. 
#' @export
#'
#' @examples
#' check.fish.pts(visit.summary, zrank = "max", plot.nrei = TRUE)
check.fish.pts = function(data, zrank = "max", plot.nrei = FALSE){
  
  # get visit id from visit directory
  visit.id = as.numeric(unlist(str_split(data$visit.dir, "VISIT_"))[2])
  
  # set reference shp
  ref.shp.path = unlist(list.files(path = data$visit.dir, pattern = "^Thalweg.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  ref.shp = st_read(ref.shp.path, quiet = TRUE)
  
  # if shapefile doesn't exist but there's csv point data then create and output points shapefile:
  
  # - for nrei predicted fish locations
  if(all(data$nrei.locs.shp == 'No' & data$nrei.locs.csv == 'Yes')){
    create.pts(data$visit.dir, ref.shp, "^predFishLocations.csv$", "NREI_FishLocs.shp")
  }

  # - for chinook predicted redd locations
  if(all(data$ch.redd.locs.shp == 'No' & data$ch.redd.locs.csv == 'Yes')){
    create.pts(data$visit.dir, ref.shp, "^ChinookSpawner_PredReddLocations.csv$", "Fuzzy_ReddLocs_Chinook.shp")
  }
  
  # - for steelhead predicted redd locations
  if(all(data$st.redd.locs.shp == 'No' & data$st.redd.locs.csv == 'Yes')){
    create.pts(data$visit.dir, ref.shp, "^SteelheadSpawner_PredReddLocations.csv$", "Fuzzy_ReddLocs_Steelhead.shp")
  }  
  
  # - for chinook juvenile predicted fish locations
  if(all(data$ch.juv.locs.shp == 'No' & data$ch.juv.locs.csv == 'Yes')){
    create.pts(data$visit.dir, ref.shp, "^ChinookJuvenile_PredFishLocations.csv$", "Fuzzy_JuvenileLocs_Chinook.shp")
  } 
  
  # - for nrei all points
  if(all(plot.nrei == TRUE & data$all.nrei.pts.csv == 'No')){
    print(paste('Cannot create points because all NREI points csv does not exist for visit', as.character(visit.id)))
  }
  
  if(all(plot.nrei == TRUE & data$all.nrei.pts.csv == 'Yes' & data$all.nrei.pts.shp == 'No')){
    create.pts(data$visit.dir, ref.shp, "^allNreiPts.csv$", "NREI_All_Pts.shp")
  }
  
  # create nrei suitable points shp and nrei raster
  if(all(plot.nrei == TRUE & data$all.nrei.pts.csv == 'Yes')){
    
    # get path to pts csv
    pts.csv = unlist(list.files(path = data$visit.dir, pattern = "^allNreiPts.csv$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
    
    # read in pts csv and convert to shp
    pts = read_csv(pts.csv, col_types = cols(.default = col_double())) %>%
      rename_at(vars(matches("^x$")), funs(str_replace(., "x", "X"))) %>%
      rename_at(vars(matches("^y$")), funs(str_replace(., "y", "Y"))) %>% 
      st_as_sf(coords = c("X", "Y"), crs = (st_crs(ref.shp)), remove = FALSE)

    # for each xy nrei point, there are multiple values throughout the water column (z)
    # this workflow selects a single z value based on user defined argument 'zmax'
    if(zrank == "max"){
      pts.zrank = pts %>%
        group_by(X, Y) %>%
        mutate(max.nrei_Jph = max(nrei_Jph, na.rm = TRUE)) %>%
        dplyr::filter(nrei_Jph == max.nrei_Jph) %>%
        dplyr::select(idx, X, Y, Z, zrank, rad.step.gte.user.pval, nrei_Jph, max.nrei_Jph)
    }else if(is.numeric(zrank) == TRUE){
      my.zrank = zrank
      pts.zrank %>%
        mutate(max.nrei_Jph = nrei_Jph)
        dplyr::filter(zrank == my.zrank)
    }else{
      "Warning: zrank parameter must either be set to 'max' or a numeric value"
    }
    
    # get count of number of rows in zrank points with suitable values (nrei_Jph > 0 and rad.step.gte.user.pval > 0.4)
    # ...may be instances where reach has no 'suitable' nrei values
    n.rows = pts.zrank %>% dplyr::filter(nrei_Jph > 0 & rad.step.gte.user.pval > 0.4) %>% nrow()
    
    # create nrei suitable points shapefile and raster it don't already exist
    if(n.rows > 0){
      
      # write out just points that have nrei_Jph > 0
      pts.zrank %>% dplyr::filter(max.nrei_Jph > 0 & rad.step.gte.user.pval > 0.4) %>% st_write(file.path(dirname(pts.csv), "NREI_Suitable_Pts.shp"), delete_layer = TRUE)
      
      # write out zrank raster
      # zrank.raster = pts.zrank %>% dplyr::filter(max.nrei_Jph > 0 & rad.step.gte.user.pval > 0.4) %>% dplyr::select(X, Y, max.nrei_Jph) %>% as.data.frame() %>% dplyr::select(-geometry) %>% rasterFromXYZ(res = c(0.1, 0.1), crs = crs(pts.zrank))
      zrank.raster = pts.zrank %>% mutate(ras.val = ifelse(max.nrei_Jph > 0 & rad.step.gte.user.pval > 0.4, max.nrei_Jph, NA)) %>% dplyr::select(X, Y, ras.val) %>% as.data.frame() %>% dplyr::select(-geometry) %>% rasterFromXYZ(res = c(0.1, 0.1), crs = crs(pts.zrank))
      raster::writeRaster(zrank.raster, file.path(dirname(pts.csv), "NREI_Suitable_Ras"), format = "GTiff", overwrite = TRUE)
      
    }
  }
}
