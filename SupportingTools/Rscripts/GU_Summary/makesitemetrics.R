#Natalie Kramer (n.kramer.andersonn@gmail.com)
#updated Feb 7, 2018

########Input Dependencies#########

#This script Relys on the following GUT data files. If any of these are missing, the code
#should still run but will return NA or zero in output tables.

#"Thalwegs.shp"
#"Thalweg.shp"
#"Bankfull.shp"
#"WaterExtent.shp"
#"BankfullXS.shp"


########Output Dependencies#########

#Output

#"VisitID"=numerical visit identifier of field visit when topographic survey was done 
#BFArea: Bankfull Area in sq meters
#WEArea: Wetted Area in sq meters
#mainThalwegL:  Length in meters of the main Thalweg.
#ThalwegsL: Sum of all Lengths from multiple thalwegs, including the main and any secondary ones
#ThalwegsR: ThalwegsL/mainThalwegL
#BordersbyArea: Total length of all borders divided by Bankfull area
#No.GU"=Number of geomorphic unit polygons
#EdgeDensMainT= Number of intersections that unit borders have with the main thalweg per unit length of the thalweg.
#EdgeDensXS= Average number of intersections that unit borders have with per unit length of a cross section.  Averaged over 20 cross-sections.
#"GUTrunpath"=path to source data that metrics are calculated from

#library dependencies: 
#you need to find and source this script

source("extractIDfrompath.R")
source("intersectpts.R")
library(sp)
library(rgdal)
library(rgeos)
library(rmapshaper)
library(raster)


makesitemetrics=function(GUTrunpath, layer="", thalweglayer="Thalwegs.shp", MultiThalweg=F){
 
  
  visit=extractvisitfrompath(GUTrunpath)
  
  GUTpath=strsplit(GUTrunpath, "Output")[[1]][1] 
  Bankfullpath=paste(GUTpath,"Inputs\\Bankfull.shp", sep="")
  WaterExtentpath=paste(GUTpath,"Inputs\\WaterExtent.shp", sep="")
  ChampThalwegpath=paste(GUTpath,"Inputs\\Thalweg.shp", sep="")
  Thalwegspath=paste(GUTpath,"Inputs", thalweglayer, sep="\\")
  XSpath=paste(GUTpath,"Inputs\\BankfullXS.shp",sep="\\")
  GUpath=paste(GUTrunpath, paste(layer, ".shp",sep=""), sep="\\") #Geomorphic unit geometry
  

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
  
#Reads in Geomorphic Unit geometry Polygons
  if(file.exists(GUpath)){
    Unit.poly=readOGR(GUpath)
    if(gIsValid(Unit.poly)==F){
      Unit.poly=gBuffer(Unit.poly, byid=TRUE, width=0)
      print("geometry fixed")
    }
    
    No.GU=length(Unit.poly)
    
    BordersbyArea=round(gLength(rmapshaper::ms_lines(Unit.poly))/gArea(Unit.poly),2)
    
    #Number of crossing of units along thalweg per 10m (Lcomplex) 1
    #Using Champ Thalweg

     #Using Manual Thalweg. Throws error sometimes on gIntersection But it still works I think 1
    if(MultiThalweg==T){
      
        if(exists("Thalwegs")){  
      
        mainT=Thalwegs[which(Thalwegs$ThalwegTyp=="Main"),]
        
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
        
        ##Note:The gIntersection in this script isn't working quite properly for all thalwegs, so multi thalweg is set to False
        #and this is suppressed as an output. 
        if(exists("Thalwegs")){
          intersects=gIntersection(Thalwegs, Unit.poly, byid=T)
          if(exists("intersects")){
            interpts=intersectpts(intersects, Unit.poly,paste(visit, "All Thalwegs" , sep=" ") )
            if(exists("interpts")){
              EdgeDensAllT=round(length(interpts[,1])/gLength(Thalwegs),2)
            }else{EdgeDensAllT=NA}
          }else{EdgeDensAllT=NA}
        } else{EdgeDensAllT=NA}
        
      }else{
        if(exists("ChampThalweg")){
          print("calculating mainT from Champ because multiple thalweg layer did not exist")
          intersects=gIntersection(ChampThalweg,Unit.poly,byid=T)
          if(exists("intersects")){
            interpts=intersectpts(intersects, Unit.poly,paste(visit, "Champ Thalweg" , sep=" ") )
            if(exists("interpts")){
              EdgeDensMainT=round(length(interpts[,1])/gLength(ChampThalweg),2)
            }else{EdgeDensMainT=NA}
          }else{EdgeDensMainT=NA}
        } else{EdgeDensMainT=NA}
      }
      
    } else {
      EdgeDensAllT=NA
      if(exists("ChampThalweg")){
        intersects=gIntersection(ChampThalweg,Unit.poly,byid=T)
       if(exists("intersects")){
          interpts=intersectpts(intersects, Unit.poly,paste(visit, "Champ Thalweg" , sep=" ") )
          if(exists("interpts")){
            EdgeDensMainT=round(length(interpts[,1])/gLength(ChampThalweg),2)
          }else{EdgeDensMainT=NA}
        }else{EdgeDensMainT=NA}
      } else{EdgeDensMainT=NA}
    }
    print("done calculating thalweg crossing metrics")
    ##In the current code  some of the intersections aren't selected.! 
    #There is likely a beter way.  Maybe I could use gIntersect twice,  first with poly and cross sections,
    ###then with the result of that and the poly.  I then may be able to then select from the list eviorment 
    ###the object of class "points".  
    
    #Average number of unit crossings from cross-sections 10m
    if(file.exists(XSpath)){
      xs=readOGR(XSpath)
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
              "ThalwegR"=round(ThalwegsL/MainThalwegL,2),
              "BordersbyArea"=BordersbyArea,
              "No.GU"=No.GU,
              "EdgeDensMainT"=EdgeDensMainT,
              #"EdgeDensAllT"=EdgeDensAllT, #output suppressed because not working properly
              "EdgeDensXS"=EdgeDensXS,
              "GUTrunpath"=GUTrunpath
    )
  
return(metrics)
}
   
