#Natalie Kramer (n.kramer.andersonn@gmail.com)
#updated Aug 30, 2017

#This script uses these GUT layers:


#GUTrunpath="E:\\Box Sync\\ET_AL\\Projects\\USA\\ISEMP\\GeomorphicUnits\\HundredSites\\Data\\VisitData/VISIT_1027/GUT/Output/GUT_2.1/Run_01"
#layer="Tier2_InChannel_Transition.shp"
#thalweglayer="Thalwegs.shp"

#Output

#BFArea: Bankfull Area in sq meters
#WEArea: Wetted Area in sq meters
#mainThalwegL:  Length in meters of the main Thalweg.
#ThalwegsL: Sum of all Lengths from multiple thalwegs, including the main and any secondary ones
#ThalwegsR: ThalwegsL/mainThalwegL


#Note:The gIntersection in this script isn't working quite properly for all multiple thalweg layers. If running 
#in batch, use CHaMP Thalwegs...

#library dependencies: 
#you need to find and source this script
#source("E:\\Box Sync\\CRB_GU\\wrk_Scripts\\Functions\\extractvisitfrompath.R")
#source("E:\\Box Sync\\CRB_GU\\wrk_Scripts\\Functions\\intersectpts.R")

library(sp)
library(rgdal)
library(rgeos)
library(rmapshaper)
library(raster)



makesiteGUTmetrics=function(GUTrunpath, layer="Tier2_InChannel.shp", thalweglayer="Thalwegs.shp", MultiThalweg=F){
 
  
  visit=extractvisitfrompath(GUTrunpath)
  
  GUTpath=paste(strsplit(GUTrunpath, visit)[[1]][1], visit,"/GUT",sep="")
  Bankfullpath=paste(GUTpath,"\\Inputs\\Bankfull.shp", sep="")
  WaterExtentpath=paste(GUTpath,"\\Inputs\\WaterExtent.shp", sep="")
  ChampThalwegpath=paste(GUTpath,"\\Inputs\\Thalweg.shp", sep="")
  Thalwegspath=paste(GUTpath,"\\Inputs\\Thalwegs.shp", sep="")
  
  

#Reads in GUT Inputs and computes metrics from them
  if(file.exists(Bankfullpath)){
    Bankfull=readOGR(Bankfullpath)
    if(gIsValid(Bankfull)==F){
      Bankfull=gBuffer(Bankfull, byid=TRUE, width=0)
      print("geometry fixed")
    }
    BFArea=round(gArea(Bankfull),0)
  }else{
    BFArea=NA
  }
  
  
  if(file.exists(WaterExtentpath)){
    WaterExtent=readOGR(WaterExtentpath)
    if(gIsValid(WaterExtent)==F){
      WaterExtent=gBuffer(WaterExtent, byid=TRUE, width=0)
      print("geometry fixed")
    }
    WEArea=round(gArea(WaterExtent),0)
  }else{
    WEArea=NA
  }
  
  if(file.exists(ChampThalwegpath)){
    ChampThalweg=readOGR(ChampThalwegpath)
    if(gIsValid(ChampThalweg)==F){
      ChampThalweg=gBuffer(ChampThalweg, byid=TRUE, width=0)
      print("geometry fixed")
    }
    MainThalwegL=round(gLength(ChampThalweg),0)
  } else{
    MainThalwegL=NA
  }
  
  if(file.exists(Thalwegspath)){
    Thalwegs=readOGR(Thalwegspath)
    if(gIsValid(Thalwegs)==F){
      Thalwegs=gBuffer(Thalwegs, byid=TRUE, width=0)
      print("geometry fixed")
    }
    MainThalwegL=round(max(gLength(Thalwegs,byid=T)),0)
    ThalwegsL=round(gLength(Thalwegs),0)
    #ThalwegsR=round(ThalwegsL/MainThalwegL,2)
  }else{
    ThalwegsL=NA
    #ThalwegsR=NA
  }
  
#Reads in Unit Polygon
  if(file.exists(paste(GUTrunpath, layer ,sep="//"))){
    Unit.poly=readOGR(paste(GUTrunpath, layer ,sep="//"))
    if(gIsValid(Unit.poly)==F){
      Unit.poly=gBuffer(Unit.poly, byid=TRUE, width=0)
      print("geometry fixed")
    }
    
    No.GU=length(Unit.poly)
    
    BordersbyArea=round(gLength(rmapshaper::ms_lines(Unit.poly))/gArea(Unit.poly),2)
    
    #Number of crossing of units along thalweg per 10m (Lcomplex) 1
    #Using Champ Thalweg
    GUTinputpath=paste(strsplit(GUTrunpath,paste("VISIT",visit, sep="_"))[[1]][1], "VISIT_",visit, "\\GUT\\Inputs", sep="")
    
    
    if(file.exists(paste(GUTinputpath,"Thalweg.shp",sep="\\"))){
      Champthalweg=readOGR(paste(GUTinputpath,"Thalweg.shp",sep="\\")) 
      #fixes geometry if bad
      if(gIsValid(Champthalweg)==F){
        Champthalweg=gBuffer(Champthalweg, byid=TRUE, width=0)
        print("geometry fixed")
      }
    }
    
    #Using Manual Thalweg. Throws error sometimes on gIntersection But it still works I think 1
    if(MultiThalweg==T){
      if(file.exists(paste(GUTinputpath,thalweglayer,sep="\\"))){
        thalweg=readOGR(paste(GUTinputpath,thalweglayer,sep="\\")) 
        #fixes geometry if bad
        if(gIsValid(thalweg)==F){
          thalweg=gBuffer(thalweg, byid=TRUE, width=0)
          print("geometry fixed")
        }
        
        mainT=thalweg[which(thalweg$ThalwegTyp=="Main"),]
        
        if(exists("mainT")){
          intersects=gIntersection(mainT,Unit.poly, byid=T)
          if(exists("intersects")){
           interpts=intersectpts(intersects, Unit.poly,paste(visit, "Main Thalweg" , sep=" ") )
            if(exists("interpts")){
              EdgeDensMainT=round(length(interpts[,1])/gLength(mainT),2)
              EdgeDensAllT=NA
            }else{EdgeDensMainT=NA}
          }else{EdgeDensMainT=NA}
        } else{EdgeDensMainT=NA}
        
        #gIntersection doesn't always work and I can't figure out how to keep going....not good for batch processing right now.
        if(exists("thalweg")){
          intersects=gIntersection(thalweg, Unit.poly, byid=T)
          if(exists("intersects")){
            interpts=intersectpts(intersects, Unit.poly,paste(visit, "All Thalwegs" , sep=" ") )
            if(exists("interpts")){
              EdgeDensAllT=round(length(interpts[,1])/gLength(thalweg),2)
            }else{EdgeDensAllT=NA}
          }else{EdgeDensAllT=NA}
        } else{EdgeDensAllT=NA}
        
      }else{
        if(exists("Champthalweg")){
          print("calculating mainT from Champ because multiple thalweg layer did not exist")
          intersects=gIntersection(Champthalweg,Unit.poly,byid=T)
          if(exists("intersects")){
            interpts=intersectpts(intersects, Unit.poly,paste(visit, "Champ Thalweg" , sep=" ") )
            if(exists("interpts")){
              EdgeDensMainT=round(length(interpts[,1])/gLength(Champthalweg),2)
            }else{EdgeDensMainT=NA}
          }else{EdgeDensMainT=NA}
        } else{EdgeDensMainT=NA}
      }
      
    } else {
      EdgeDensAllT=NA
      if(exists("Champthalweg")){
        intersects=gIntersection(Champthalweg,Unit.poly,byid=T)
        if(exists("intersects")){
          interpts=intersectpts(intersects, Unit.poly,paste(visit, "Champ Thalweg" , sep=" ") )
          if(exists("interpts")){
            EdgeDensMainT=round(length(interpts[,1])/gLength(Champthalweg),2)
          }else{EdgeDensMainT=NA}
        }else{EdgeDensMainT=NA}
      } else{EdgeDensMainT=NA}
    }
    print("done calculating thalweg crossing metrics")
    ####There may be a faster way if I gIntersect twice,  first with poly and cross sections,
    ###then with the result of that and the poly.  I may be able to then select from the list eviorment 
    ###the object of class "points".  In my current code I am missing some of the intersections.this other 
    ###methods doesn't miss any of them.
    
    #Average number of unit crossings from cross-sections 10m
    if(file.exists(paste(GUTinputpath,"\\BankfullXS.shp",sep=""))){
      xs=readOGR(paste(GUTinputpath,"\\BankfullXS.shp",sep=""))
      #fixes geometry if needed
      if(gIsValid(xs)==F){
        xs=gBuffer(xs, byid=TRUE, width=0)
      }
      xssubset=xs[seq(1, length(xs), floor(length(xs)/20)),] 
      proj4string(xssubset)=crs(Unit.poly)
      if(exists("xssubset")){
        intersects=gIntersection(xssubset,Unit.poly,byid=T)
        if(exists("intersects") & is.null(intersects)==F){
          interpts=intersectpts(intersects, Unit.poly,paste(visit, "Cross Sections" , sep=" ") )
          if(exists("interpts")){
            EdgeDensXS=round(length(interpts[,1])/gLength(xssubset),2)
          }else{EdgeDensXS=NA}
        }else{EdgeDensXS=NA}
      } else{EdgeDensXS=NA}
    } else {
      EdgeDensXS=NA
      print("BankfullXS.shp does not exist")
    }
    print("done calculating cross section crossing metrics")
    
  } else {
    No.GU=NA
    BordersbyArea=NA
    EdgeDensMainT=NA
    EdgeDensAllT=NA
    EdgeDensXS=NA
    print(paste(layer, "does not exist", sep=" "))
  }


    metrics=c("VisitID"=visit,
              "BFArea"=BFArea,
              "WEArea"=WEArea,
              "MainThalwegL"=MainThalwegL,
              "ThalwegsL"=ThalwegsL,
              "ThalwegR"=MainThalwegL/ThalwegsL,
              "BordersbyArea"=BordersbyArea,
              "No.GU"=No.GU,
              "EdgeDensMainT"=EdgeDensMainT,
              #"EdgeDensAllT"=EdgeDensAllT,
              "EdgeDensXS"=EdgeDensXS
              #"GUTrunpath"=GUTrunpath
    )
  
  
return(metrics)
}
   
