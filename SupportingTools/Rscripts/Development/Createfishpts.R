#Creates shape files of predicted fish points from HSI and NREI as well as NREI points.
#Also creates a raster of NREI values within the suitable habitat regions.

#Natalie Kramer (n.kramer.anderson@gmail.com)
#updated Oct 28, 2017

####inputs#####
#fisrunpath: a path to the NREI visit folder.  To run HSI must be in file structure as is.  
#Script will break if file structure changes.
#example:
#fishrunpath="E:\\Box Sync\\ET_AL\\Projects\\USA\\ISEMP\\GeomorphicUnits\\FifteenStartingSites\\Data\\VisitData/VISIT_1029/NREI"

#GUTrunpath: a path to the GUT run that the analysist is interested in.
#example: 
#GUTrunpath="E:\\Box Sync\\ET_AL\\Projects\\USA\\ISEMP\\GeomorphicUnits\\FifteenStartingSites\\Data\\VisitData/VISIT_1029/GUT/Output/GUT_2.0/EqTransMT_01"


####outputs#####
#predFishLocations.shp: ESRI shapefile of predicted fish points from predFishLocations.csv
#predReddLocs.shp: ESRI Shapefile of predicted redd locations from predReddLocs.csv
#predReddLocs.shp: ESRI Shapefile of predicted redd locations from predReddLocs.csv
#allNreiPts.csv: ESRI Shapefile of all NREI pts from allNreiPts.csv
#SuitableNreiPts.shp: ESRI Shapefile of NREI pts >0 and above 40%pval threshold. 
#These are the pool of points that the predicted fish locs were chosen from.
#Only one point per x,y is chosen based on optional argument zrank
#zrank="max" which takes the maximum NREI from the water column at each location
#zrank="XX" takes a number specifying the water column placement. 1= bed of stream.
#suitableNreiRaster.tiff: GeoTiff created from SuitableNreiPts.shp. 
#This raste is used to create the habitat polygons.


library(sp)
library(tidyverse)
library(raster)
library(rgeos)
library(rgdal)

Createfishpts=function(fishrunpath, zrank="max", plotNREI=F){  
  
  #extracts just the visit number 
  visit=extractvisitfrompath(fishrunpath)
  
  #Creates path to GUT data based on NREI path
  GUTpath=paste(strsplit(fishrunpath, "NREI"),"GUT",sep="")
  HSIpath=paste(strsplit(fishrunpath, "NREI"),"HSI//Output",sep="")
  Reddpath=paste(strsplit(Fishrunlist[i], "NREI"),"HSI//reddPlacement",sep="")

  
  
  #calls in GUT for same visit and extracts coordinate information
  if(file.exists(paste(GUTpath, "Inputs\\Thalweg.shp",sep="\\"))){
    form.poly=readOGR(paste(GUTpath, "Inputs\\Thalweg.shp",sep="\\"))
    if(gIsValid(form.poly)==F){
      form.poly=gBuffer(form.poly, byid=TRUE, width=0)
      print("geometry fixed")
    }
    proj <- crs(form.poly)
    print(proj)
    
    
    #making predicted fish locations from NREI
  #  if(file.exists(paste(fishrunpath, "\\predFishLocations.shp",sep=""))==F){   
    if(file.exists(paste(fishrunpath, "\\predFishLocations.csv", sep=""))==T){ 
      #reads in fish locations and creates spatial points data frame
      fish=read.csv(paste(fishrunpath,"\\predFishLocations.csv", sep=""), stringsAsFactors = FALSE)
      if(length(fish[,1])>0){
        if(exists("proj")){
          fish.pts <- SpatialPointsDataFrame(fish[,2:3],fish, proj4string = proj)
        } else {print("unable to determine projection for data")}
        print("writing NREI predFishLocations.shp")
        writeOGR(fish.pts, fishrunpath, "predFishLocations", driver="ESRI Shapefile", overwrite_layer = TRUE)
      } else {print("no NREI predicted fish")}
    } else {print("no NREI predicted fish locations datafile")}
 #   }
    
    #"making predicted redd locations from HSI"
    #if(file.exists(paste(HSIpath, "\\predReddLocs.shp", sep=""))==F){ 
    #
    #  if(file.exists(paste(HSIpath, "\\predReddLocs.csv", sep=""))==T){ 
    #    #reads in fish locations and creates spatial points data frame
    #    fish=read.csv(paste(HSIpath,"\\predReddLocs.csv", sep=""), stringsAsFactors = FALSE)
    #    if(length(fish[,1])>0){
    #      if(exists("proj")){
    #        fish.pts <- SpatialPointsDataFrame(fish[,2:3],fish, proj4string = proj)
    #      } else {print("unable to determine projection for data")}
    #      print("writing HSI predReddLocs.shp")
    #      writeOGR(fish.pts, HSIpath, "predReddLocs", driver="ESRI Shapefile", overwrite_layer = TRUE)
    #    } else {print("no HSI predicted redd")}
    #  } else {print("no HSI predicted redd locations datafile")}
    #}
    
    
    #for (i in c(1:length(Fishrunlist))){

      #if(file.exists(paste(Reddpath, "\\chkPredReddLocs.shp",sep=""))==F){
      if(file.exists(paste(Reddpath, "\\chkPredReddLocs.csv", sep=""))==T){ 
        #reads in fish locations and creates spatial points data frame
        fish=read.csv(paste(Reddpath,"\\chkPredReddLocs.csv", sep=""), stringsAsFactors = FALSE)
        if(length(fish[,1])>0){
          if(exists("proj")){
            fish.pts <- SpatialPointsDataFrame(fish[,2:3],fish, proj4string = proj)
          } else {print("unable to determine projection for data")}
          print("writing chnk HSI predReddLocs.shp")
          writeOGR(fish.pts, Reddpath, "chkpredReddLocs", driver="ESRI Shapefile", overwrite_layer = TRUE)
        } else {print("no chnk HSI predicted redd")}
      } else {print("no HSI chnk predicted redd locations datafile")}
      #}
      
      #if(file.exists(paste(Reddpath, "\\sthdPredReddLocs.shp",sep=""))==F){
      if(file.exists(paste(Reddpath, "\\sthdPredReddLocs.csv", sep=""))==T){ 
        #reads in fish locations and creates spatial points data frame
        fish=read.csv(paste(Reddpath,"\\sthdPredReddLocs.csv", sep=""), stringsAsFactors = FALSE)
        if(length(fish[,1])>0){
          if(exists("proj")){
            fish.pts <- SpatialPointsDataFrame(fish[,2:3],fish, proj4string = proj)
          } else {print("unable to determine projection for data")}
          print("writing sthd HSI predReddLocs.shp")
          writeOGR(fish.pts, Reddpath, "sthdpredReddLocs", driver="ESRI Shapefile", overwrite_layer = TRUE)
        } else {print("no sthd HSI predicted redd")}
      } else {print("no HSI sthd predicted redd locations datafile")}
      #}
    #}
    
    
    if(plotNREI==T){
      #makes NREI points
      #if(file.exists(paste(fishrunpath, "\\allNreiPts.shp", sep=""))==F){ 
      if(file.exists(paste(fishrunpath, "\\allNreiPts.csv", sep=""))==T){ 
        
        data=read.csv(paste(fishrunpath,"\\allNreiPts.csv", sep=""), stringsAsFactors = FALSE)
        
        if(exists("proj")){
          nrei.pts <- SpatialPointsDataFrame(data[,2:3],data, proj4string = proj)
        } else {print("unable to determine projection for data")}
        
        print("writing allNreiPts.shp")
        writeOGR(nrei.pts, fishrunpath, "allNreiPts", driver="ESRI Shapefile", overwrite_layer = TRUE)
        
        data0=data[which(data$rad.step.gte.user.pval>0 & data$nrei_Jph>0),]
        
        
        #making suitable NREI points
        #Chooses NREI to be max at each water columnn depth when creating raster
        if(zrank=="max"){
          data1 <- data0 %>%
            dplyr::group_by(X, Y) %>%
            dplyr::mutate(
              max.nrei = max(nrei_Jph),
              is.max.nrei = near(max.nrei, nrei_Jph)
            ) %>%
            dplyr::filter(is.max.nrei) %>%
            dplyr::mutate(nrei_js = max.nrei) %>%
            dplyr::select(idx, X, Y, Z, zrank,rad.step.gte.user.pval, nrei_Jph)
        }
        
        #chooses NREI to be from a specific z rank value
        if(is.numeric(zrank)==T){
          data1=data0[which(data0$nrei_Jph>0 & data0$zrank==zrank),]
        }
        
        
        if(file.exists(paste(fishrunpath, "\\suitableNreiPts.shp", sep=""))==F){ 
          if(dim(data1)[1]>0){
            if(exists("proj")){
              fish.pts2 <- SpatialPointsDataFrame(data1[,2:3],data1, proj4string = proj)
              print("writing suitableNreiPts.shp")
              writeOGR(fish.pts2, fishrunpath, "suitableNreiPts", driver="ESRI Shapefile", overwrite_layer = TRUE)
            } else {print("unable to determine projection for data did not create shapefile")}
            
            #making suitable NREI raster
            if(dim(data1)[1]>1){
              pixels <- SpatialPixelsDataFrame(fish.pts2, tolerance=.001, fish.pts2@data)
              data.raster <- raster(pixels[,'nrei_Jph'])
              print("writing suitableNreiRaster.tif")
              raster::writeRaster(data.raster, paste(fishrunpath,"//suitableNreiRaster", sep=""), format="GTiff", overwrite = TRUE)
            }  else {print("One or less good NREI -- unable to make NREI RASTER") }
          } else {print("no suitable pts")}
        }
      }
    }
    
  } else {print("Thalweg.shp does not exist can't define projection")}  
  
  
  
}
