
#Creates A table of data from GUT and Habitat inputs.  You need to specify the VISIT path that houses the GUT, NREI and HSI folders.
#Natalie Kramer (n.kramer.andersonn@gmail.com)
#updated Aug 30, 2017

#It will generate 
#DelftArea: Area of Fish Modelling extent
#NreiSuitArea:  Area within NREI useable habitat
#NreiBestArea: Area within best NREI useable habitat
#HSIPredRedd: Total Predicted Reds from HSI model 
#HSIBestPredRedd: Total PRedicted Reds within Best HSI regions.
#HSISuitArea_ch: Area within Chinook Spawner useable habitat
#HSIBestArea_ch:  Area within best Chinook Spawner useable habitat
#HSISuitArea_st:  Area within useable Steelhead habitat
#HSIBestArea_st: Area within best Steelhead Spawner useable habitat

#if present will compute using:
#NREIExtent.shp
#Thalwegs.shp
#goodNreiPoly.shp
#ChinookSpawnerpoly.shp
#SteelheadSpawnerpoly.shp

#library dependencies: 
library(rgdal)
library(rgeos)


#example input
#VISITpath="E:\\Box Sync\\ET_AL\\Projects\\USA\\ISEMP\\GeomorphicUnits\\FifteenStartingSites\\Data\\VisitData\\VISIT_1029"

#you also need this little code.
#source("E:\\Box Sync\\CRB_GU\\wrk_Scripts\\Functions\\extractvisitfrompath.R")

makesiteFISHmetrics=function(Fishrunpath){
  
  visit=extractvisitfrompath(Fishrunpath)
  
  NREIpath=Fishrunpath
  HSIpath=paste(strsplit(Fishrunpath, visit)[[1]][1], visit,"/HSI",sep="")
  GUTpath=paste(strsplit(Fishrunpath, visit)[[1]][1], visit,"/GUT",sep="")
  
  Delftpath=paste(NREIpath, "\\DelftExtent.shp", sep="")
  ChampThalwegpath=paste(GUTpath, "\\Inputs\\Thalweg.shp", sep="")
  Thalwegspath=paste(GUTpath, "\\Inputs\\Thalwegs.shp", sep="")
  nreipolypath=paste(NREIpath, "\\SuitableNreiPoly.shp", sep="")
  nreifishpath=paste(NREIpath, "\\predFishLocations.shp", sep="")
  chkpolypath=paste(HSIpath, "\\Output\\suitableChnkPoly.shp", sep="")
  sthdpolypath=paste(HSIpath, "\\Output\\suitableSthdPoly.shp", sep="")
  chkfishpath=paste(HSIpath, "\\reddPlacement\\chkpredReddLocs.shp", sep="")
  sthdfishpath=paste(HSIpath, "\\reddPlacement\\sthdpredReddLocs.shp", sep="")
  
  if(file.exists(Delftpath)){
    Extent=readOGR(Delftpath)
    if(gIsValid(Extent)==F){
      Extent=gBuffer(Extent, byid=TRUE, width=0)
      print("geometry fixed")
    }
    DelftArea=round(gArea(Extent),0)
    
    if(file.exists(ChampThalwegpath)){
      ChampThalweg=readOGR(ChampThalwegpath)
      if(gIsValid(ChampThalweg)==F){
        ChampThalweg=gBuffer(ChampThalweg, byid=TRUE, width=0)
        print("geometry fixed")
      }
      
      ChampThalweg1=raster::crop(ChampThalweg, Extent)
      
      if(exists("ChampThalweg1")){
        MainThalwegL=round(gLength(ChampThalweg1),0)
      } else{ MainThalwegL=NA}
    } else{ MainThalwegL=NA
    }
    
    if(file.exists(Thalwegspath)){
      Thalwegs=readOGR(Thalwegspath)
      if(gIsValid(Thalwegs)==F){
        Thalwegs=gBuffer(Thalwegs, byid=TRUE, width=0)
        print("geometry fixed")
      }
      
      Thalwegs1=raster::crop(Thalwegs, Extent)
      
      if(exists("Thalwegs1")){
        if(dim(Thalwegs1)[1]>0){
        MainThalwegL=round(max(gLength(Thalwegs1,byid=T)),0)
        ThalwegsL=round(gLength(Thalwegs1),0)
        #ThalwegsR=round(ThalwegsL/MainThalwegL,2)
        }else{ThalwegsL=NA}
        }else{ThalwegsL=NA}
    }else{ThalwegsL=NA
    #ThalwegsR=NA
    }
    
  }else{
    DelftArea=NA
    ThalwegsL=NA
    MainThalwegL=NA
  }
  
  
  if(file.exists(nreipolypath)){
    #Reads in Shapefiles and fixes geometry if needed
    hab.poly=readOGR(nreipolypath)
    if(gIsValid(hab.poly)==F){
      hab.poly=gBuffer(hab.poly, byid=TRUE, width=0)
      print("geometry fixed")
    }
    NreiArea=gArea(hab.poly)
    
    if(length(which(hab.poly$layer==2))>0){
      NreiBestArea=gArea(hab.poly[which(hab.poly$layer==2),])
    } else {NREIBestArea=0}
    
  } else {
    NreiArea=NA
    NreiBestArea=NA
  }
  
  if(file.exists(nreifishpath)){
    fish=readOGR(nreifishpath)
    capacity=length(fish)
    NreiPredFish=capacity
    if(capacity==0 | capacity==1){
      NreiArea=0
      NreiBestArea=0
    }
    if(is.na(NreiBestArea)==F){
      if(NreiBestArea!=0 & length(which(hab.poly$layer==2))>0 ){
        NreiBestPredFish=length(gIntersection(fish, hab.poly[which(hab.poly$layer==2),]))
      } else {NreiBestPredFish=0}
    } else {NreiBestPredFish=NA}
  } else {
    NreiPredFish=NA
    NreiBestPredFish=NA
  }
  
  
  
  
  if(file.exists(gsub("suitableChnkPoly.shp", "FuzzyChinookSpawner_DVSC.tif", chkpolypath))){
    if(file.exists(chkpolypath)){
      #Reads in Shapefiles and fixes geometry if needed
      hab.poly=readOGR(chkpolypath)
      if(gIsValid(hab.poly)==F){
        hab.poly=gBuffer(hab.poly, byid=TRUE, width=0)
        print("geometry fixed")
      }
      chkArea=gArea(hab.poly)
      
      if(length(which(hab.poly$layer==2))>0){
        chkBestArea=gArea(hab.poly[which(hab.poly$layer==2),])
      } else {chkBestArea=0}
    } else {
      chkArea=0
      chkBestArea=0
    }
  } else {
    chkArea=NA
    chkBestArea=NA
  }
  
  
  
  if(file.exists(gsub("suitableSthdPoly.shp", "FuzzySteelheadSpawner_DVSC.tif", sthdpolypath))){
    if(file.exists(sthdpolypath)){
      #Reads in Shapefiles and fixes geometry if needed
      hab.poly=readOGR(sthdpolypath)
      if(gIsValid(hab.poly)==F){
        hab.poly=gBuffer(hab.poly, byid=TRUE, width=0)
        print("geometry fixed")
      }
      sthdArea=gArea(hab.poly)
      
      if(length(which(hab.poly$layer==2))>0){
        sthdBestArea=gArea(hab.poly[which(hab.poly$layer==2),])
      } else {sthdBestArea=0}
      
    } else {
      sthdArea=0
      sthdBestArea=0
    }
  } else {
    sthdArea=NA
    sthdBestArea=NA
  }
  
  if(file.exists(chkfishpath)){
    redds=readOGR(chkfishpath)
    capacity=length(redds)
    HSIPredRedd_ch=capacity
    if(capacity==0 | capacity==1){
      chkArea=0
      chkBestArea=0
    }
    if(is.na(chkBestArea)==F){
      if(chkBestArea!=0 & length(which(redds@data$hsi_cat=="best"))>0){
        HSIBestPredRedd_ch=length(which(redds@data$hsi_cat=="best"))
      } else {HSIBestPredRedd_ch=0}
    }else {HSIBestPredRedd_ch=NA}
  } else {
    HSIPredRedd_ch=NA
    HSIBestPredRedd_ch=NA
  }
  
  if(file.exists(sthdfishpath)){
    redds=readOGR(sthdfishpath)
    capacity=length(redds)
    HSIPredRedd_st=capacity
    if(capacity==0 | capacity==1){
      sthdArea=0
      sthdBestArea=0
    }
    if(is.na(sthdBestArea)==F){
      if(sthdBestArea!=0 & length(which(redds@data$hsi_cat=="best"))>0){
        HSIBestPredRedd_st=length(which(redds@data$hsi_cat=="best"))
      } else {HSIBestPredRedd_st=0}
    }else {HSIBestPredRedd_st=NA}
  } else {
    HSIPredRedd_st=NA
    HSIBestPredRedd_st=NA
  }
  
  sitemetrics=c("Visit"=visit,
                "DelftArea"=as.numeric(DelftArea), 
                "MainThalwegL"=MainThalwegL,"ThalwegsL"=ThalwegsL, 
                "NreiPredFish"=NreiPredFish, "NreiBestPredFish"=NreiBestPredFish,  
                "NreiSuitArea"=NreiArea, "NreiBestArea"=NreiBestArea,
                "HSIPredRedd_ch"=HSIPredRedd_ch, "HSIBestPredRedd_ch"=HSIBestPredRedd_ch,
                "HSIPredRedd_st"=HSIPredRedd_st, "HSIBestPredRedd_st"=HSIBestPredRedd_st,
                "HSISuitArea_ch"=chkArea,  "HSIBestArea_ch"=chkBestArea,
                "HSISuitArea_st"=sthdArea, "HSIBestArea_st"=sthdBestArea
  )
  #,"ThalwegR"=ThalwegsR)
  return(sitemetrics)
  
}



