#' Create points shapefile from csv
#'
#' @param visit.dir Full filepath to visit folder 
#' @param visit.crs CRS (projection) for visit
#' @param file.name Name of the csv
#' @param out.name Name of the output shapefile
#'
#' @return Creates a points shapefile from the csv and saves output to same directory as csv
#' @export
#'
#' @examples
#' create.pts("C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/VISIT_1027", 
#' "+proj=utm +zone=12 +datum=NAD83 +units=m +no_defs +ellps=GRS80 +towgs84=0,0,0",
#' "predFishLocations.csv", "predFishLocations")
create.pts = function(visit.dir, visit.crs, file.name, out.name){
  
  # get path to csv file
  pts.csv = unlist(list.files(path = visit.dir, pattern = file.name, full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  
  # read in csv 
  pts.tb = read_csv(pts.csv)
  
  # if 'X' or 'Y' are lowercase change to uppercase
  if('x' %in% colnames(pts.tb)){pts.tb = rename(pts.tb, X = x)}
  if('y' %in% colnames(pts.tb)){pts.tb = rename(pts.tb, Y = y)}
  
  # convert to spatial points data frame
  coords = cbind(pts.tb$X, pts.tb$Y)
  pts.spdf = SpatialPointsDataFrame(coords, pts.tb, proj4string = CRS(visit.crs))
  
  # write output to esri shapefile
  writeOGR(pts.spdf, dirname(pts.csv), out.name, driver="ESRI Shapefile", overwrite_layer = TRUE)
  
}


#' Checks if fish/redd points shapefile exists.  Creates relevant shapefile if csv input data exists.
#'
#' @param data Dataframe created from 'check_visit_data.R' script
#' @param zrank Value user to select single NREI value for each xy point.  Either set to "max" or numeric value.
#' @param plot.nrei If set to TRUE will output suitable NREI points shapefile and raster
#'
#' @return
#' Returns following if shapefiles if they don't exist on file:
#' predFishLocations.shp: ESRI shapefile of predicted fish points from predFishLocations.csv
#' chkPredReddLocs.shp: ESRI Shapefile of predicted Chinook redd locations from chkPredReddLocs.csv
#' sthdPredReddLocss.shp: ESRI Shapefile of predicted steelhead redd locations from sthdPredReddLocs.csv
#' allNreiPts.shp: ESRI Shapefile of all NREI pts from allNreiPts.csv
#' 
#' Returns folloiwng if files don't exist and 'plot.nrei' argument set to TRUE
#' SuitableNreiPts.shp: ESRI Shapefile of NREI pts > 0 and above 40% pval threshold. 
#'                      These are the pool of points that the predicted fish locs were chosen from
#'                      Only one point per x,y is chosen based on optional argument zrank
#'                      zrank="max" which takes the maximum NREI from the water column at each location
#'                      zrank="XX" takes a number specifying the water column placement. 1 = bed of stream.
#' suitableNreiRaster.tiff: GeoTiff created from SuitableNreiPts.shp. Used to create habitat polygons. 
#' @export
#'
#' @examples
#' check.fish.pts(visit.summary, zrank = "max", plot.nrei = TRUE)
check.fish.pts = function(data, zrank = "max", plot.nrei = FALSE){
  
  # get visit id from visit directory
  visit.id = as.numeric(unlist(str_split(data$visit.dir, "VISIT_"))[2])
  
  # if shapefile doesn't exist but there's csv point data then create and output points shapefile:
  
  # - for nrei predicted fish locations
  if(data$nrei.locs.shp == 'No' & data$nrei.locs.csv == 'Yes'){
    create.pts(data$visit.dir, data$visit.crs, "predFishLocations.csv$", "predFishLocations")
  }

  # - for chinook predicted redd locations
  if(data$ch.redd.locs.shp == 'No' & data$ch.redd.locs.csv == 'Yes'){
    create.pts(data$visit.dir, data$visit.crs, "chkPredReddLocs.csv$", "chkPredReddLocs")
  }
  
  # - for steelhead predicted redd locations
  if(data$st.redd.locs.shp == 'No' & data$st.redd.locs.csv == 'Yes'){
    create.pts(data$visit.dir, data$visit.crs, "sthdPredReddLocs.csv$", "sthdPredReddLocs")
  }  
  
  # - for nrei all points
  if(plot.nrei == TRUE & data$all.nrei.pts.csv == 'No'){
    print('Cannot create points because all NREI points csv does not exist for visit ' + str(visit.id))
  }
  
  if(plot.nrei == TRUE & data$all.nrei.pts.csv == 'Yes'){
    create.pts(data$visit.dir, data$visit.crs, "allNreiPts.csv$", "allNreiPts")
  }
  
  # create nrei suitable points shp and nrei raster
  if(plot.nrei == TRUE & data$all.nrei.pts.csv == 'Yes'){
    
    # get path to csv file
    pts.csv = unlist(list.files(path = visit.dir, pattern = "allNreiPts.csv$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
    
    # read in csv and subset by pval and Jph columns
    pts.tb = read_csv(pts.csv) %>%
      dplyr::filter(rad.step.gte.user.pval > 0 & nrei_Jph > 0)
    
    # for each xy nrei point, there are multiple values throughout the water column (z)
    # this workflow selects a single z value based on user defined argument 'zmax'
    if(zrank == "max"){
      pts.zrank = pts.tb %>%
        group_by(X, Y) %>%
        mutate(max.nrei = max(nrei_Jph),
          is.max.nrei = near(max.nrei, nrei_Jph)) %>% # ask NK why this line is necessary
        filter(is.max.nrei) %>%
        mutate(nrei_js = max.nrei) %>%
        select(idx, X, Y, Z, zrank, rad.step.gte.user.pval, nrei_Jph)
    }else if(is.numeric(zrank) == TRUE){
      my.zrank = zrank
      pts.zrank = pts.tb %>%
        dplyr::filter(zrank == my.zrank)
    }else{
      "Warning: zrank parameter must either be set to 'max' or a numeric value"
    }
    
    # get count of number of rows in zrank points
    # ...may be instances where reach has no 'suitable' nrei values
    n.rows = dim(pts.zrank)[1]
    
    # create nrei suitable points shapefile and raster it don't already exist
    if(data$suit.nrei.pts.shp == 'No' & n.rows > 0){
      coords = cbind(pts.zrank$X, pts.zrank$Y)
      zrank.spdf = SpatialPointsDataFrame(coords, pts.zrank, proj4string = CRS(data$visit.crs))
      writeOGR(zrank.spdf, dirname(pts.csv), "suitableNreiPts", driver="ESRI Shapefile", overwrite_layer = TRUE)
      zrank.pixels = SpatialPixelsDataFrame(zrank.spdf, tolerance=.001, zrank.spdf@data)
      zrank.raster = raster(zrank.pixels[,'nrei_Jph'])
      raster::writeRaster(zrank.raster, file.path(dirname(pts.csv), "suitableNreiRaster"), format = "GTiff", overwrite = TRUE)
    }
  }
}

check.fish.pts(data, zrank, plot.nrei)