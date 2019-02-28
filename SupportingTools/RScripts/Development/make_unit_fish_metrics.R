#This script summarizes response by individual geomorphic units.   I need to add Average values from Rasters for NREI and HSI to output.

library(raster)
library(sp)
library(dplyr)
library(rgeos)
library(rgdal)

makeUnitFishmetrics=function(GUTrunpath, layer, figdir="NA", Model="NREI", species="", ModelMedians=T){
  
  units=paste(GUTrunpath, paste(layer, ".shp", sep=""), sep="/")
  visit=extractvisitfrompath(GUTrunpath)
  
  VISITpath=strsplit(GUTrunpath, "GUT")[[1]][1]
  
  HSIpath=paste(strsplit(GUTrunpath, visit)[[1]][1], visit,"/HSI",sep="")
  GUTpath=paste(strsplit(GUTrunpath, visit)[[1]][1], visit,"/GUT",sep="")
  NREIpath=paste(strsplit(GUTrunpath, visit)[[1]][1], visit,"/NREI",sep="")
  
  # reads in GUT  -------------------------------------------------------
  
  
  print("reading in GUT spatial data")
  # read in units as spatial polygons dataframe
  if (file.exists(units)){
    units.poly = readOGR(units)
    if(gIsValid(units.poly)==F){
      units.poly=gBuffer(units.poly, byid=TRUE, width=0)
      print("geometry fixed")
    }
    
    #which(names(unit.poly))
    
    #cropping GUT t
    
    Delftpath=paste(NREIpath, "\\DelftExtent.shp", sep="")
    if(file.exists(Delftpath)){
      Extent=readOGR(Delftpath)
      if(gIsValid(Extent)==F){
        Extent=gBuffer(Extent, byid=TRUE, width=0)
        print("geometry fixed")
      }
      proj4string(Extent)=crs(proj4string(units.poly))
    }
    
    print("cropping to Delft Extent")
    if(exists("Extent")){
      units.spdf=raster::crop(units.poly, Extent)
      
      if(is.null(units.spdf)==F){
        # Re-calc Area field.
        units.spdf@data = units.spdf@data%>%
          mutate(AreainDelft = gArea(units.spdf,byid=T))
        
        #function that computes the summaries by unit.
        habsumfunc=function(habpath, fishpath, Model=Model, species=species){
          
          #reads in habitat polygons of best and suitable area if exists
          if(file.exists(habpath)){
            hab.spdf = readOGR(habpath)
            proj4string(hab.spdf)=crs(proj4string(units.spdf))
            if(gIsValid(hab.spdf)==F){
              hab.spdf=gBuffer(hab.spdf, byid=TRUE, width=0)
              print("geometry fixed")
            }
            
            #intersects hab data with unit data
            hab=raster::intersect(units.spdf, hab.spdf)
            
            
            if(exists("hab")==T){
            # Re-calc Area field.
            hab@data=mutate(hab@data, HabArea=gArea(hab,byid=T), 
                            HSIID = rownames(hab@data)) #[,-c(1,2,3,5)]
            
            
            a=hab@data%>%
              group_by(UnitID)%>%
              summarize(SuitArea=sum(HabArea))
            
            b=hab@data%>%
              filter(layer==2)%>%
              group_by(UnitID)%>%
              summarize(BestArea=sum(HabArea))
            
            hab.sum=a%>%
              full_join(b, by="UnitID")
            } else {hab.sum=tibble(UnitID=units.spdf@data$UnitID, SuitArea=NA, BestArea=NA )}
          } else {hab.sum=tibble(UnitID=units.spdf@data$UnitID, SuitArea=NA, BestArea=NA )}
          
          #Summarizes predicted fish by Unit ID
          if(file.exists(predfishpath)){
            fishlocs= read.csv(predfishpath, header=T, stringsAsFactors=F)
            
            #Reads in fishlocation points into spatial dataframe and combines it with geomorphic attribute
            if(exists("fishlocs")){
              if(dim(fishlocs)[1]>0){
                
                fish.spdf = fishlocs %>%
                  mutate(fish.loc = 1)%>%
                  #SpatialPointsDataFrame(coords = cbind(.$x, .$y), data = ., proj4string = CRS(proj4string(units.spdf)))
                  SpatialPointsDataFrame(coords = cbind(.$X, .$Y), data = ., proj4string = CRS(proj4string(units.spdf)))
                  
                
                fish.units = cbind(over(fish.spdf, units.spdf),fish.loc= fish.spdf@data$fish.loc)#[,-c(1,2,3,5)]
                
                a=fish.units%>%
                  group_by(UnitID)%>%
                  summarize(No.Fish=sum(fish.loc, na.rm=T))
           
                #print("dimensions of hab with best before smmary")
                #print(dim(hab[which(hab$layer==2),]))
                
                if(exists("hab")){
              if(dim(hab[which(hab$layer==2),])[1]>0){
                  
                
                print("dimensions of hab with best")
                print(dim(hab[which(hab$layer==2),]))
                                                        
                #plot(hab[which(hab$layer==2),])
                #points(fish.spdf, col="yellow")
                
                besthab=hab[which(hab$layer==2),]
                #plot(besthab)
                #print("besthab")
                #head(besthab)
                
                #proj4string(hab)=crs(proj4string(fish.spdf))
                bestfish.units0=cbind(over(fish.spdf, besthab), fish.loc= fish.spdf@data$fish.loc) 
                
                 #  print("cbind selected fish over best hab")
                #  print(bestfish.units0)
                  
                  bestfish.units = bestfish.units0[-which(is.na(bestfish.units0$UnitID)),]
                  
                  #print("length of bestfish.units=")
                  #print(bestfish.units)
                  
                  b=bestfish.units%>%
                    group_by(UnitID)%>%
                    summarize(No.FishBest=sum(fish.loc))
                  
              }else {b=tibble(UnitID=a$UnitID, No.FishBest=NA)}
                } else {b=tibble(UnitID=a$UnitID, No.FishBest=NA)}
                
                predfish.sum=a%>%
                  full_join(b, by="UnitID")
              } else {predfish.sum=tibble(UnitID=units.spdf@data$UnitID, No.Fish=0, No.FishBest=NA )}
            } else {predfish.sum=tibble(UnitID=units.spdf@data$UnitID, No.Fish=NA, No.FishBest=NA )} 
          }else {predfish.sum=tibble(UnitID=units.spdf@data$UnitID, No.Fish=NA, No.FishBest=NA )} 
          
            print("head(predfish.sum)")
            print(head(predfish.sum))
            #print(predfish.sum$No.FishBest)
            #print("tail(fish.sum)")
            #print(tail(fish.sum))
          
          if(ModelMedians==T){
          if(Model=="NREI"){
            print("computing NREI Medians")
            if(file.exists(paste(NREIpath,"\\allNreiPts.csv", sep=""))){
              nrei.pts=read.csv(paste(NREIpath, "\\allNreiPts.csv", sep=""), header=T, stringsAsFactors=F)}
            if (exists("nrei.pts")){
              if(dim(nrei.pts)[1]>0){
                
                nreipts.spdf = SpatialPointsDataFrame(data=nrei.pts, coords = cbind(nrei.pts$X, nrei.pts$Y), proj4string = CRS(proj4string(units.spdf)))
                
                #extracts and summarizes form and NREI for all points
                nrei.units = cbind(over(nreipts.spdf, units.spdf),nrei_Jph= nreipts.spdf@data$nrei_Jph)#[,-c(1,2,3,5)]
                
                a=nrei.units%>%
                  group_by(UnitID)%>%
                  summarize(MedModelVal=median(nrei_Jph, na.rm=T))
                
                #extracts form and NREI for points overlain by best habitat polygon
                if(exists("hab")==T){
                if(dim(hab[which(hab$layer==2),])[1]>0){
                  proj4string(hab) = CRS(proj4string(nreipts.spdf))
                  best.units = cbind(over(nreipts.spdf, hab[which(hab$layer==2),]),nrei_Jph= nreipts.spdf@data$nrei_Jph)
                  
                  b=best.units%>%
                    group_by(UnitID)%>%
                    summarize(MedModelValBest=median(nrei_Jph, na.rm=T))
                } else {b=tibble(UnitID=a$UnitID, MedModelValBest=NA)}
                } else {b=tibble(UnitID=a$UnitID, MedModelValBest=NA)}
                
                medians.sum=a%>%
                  full_join(b, by="UnitID")
                
              } else {medians.sum=tibble(UnitID=units.spdf@data$UnitID, MedModelVal=NA, MedModelValBest=NA )} 
            }else {medians.sum=tibble(UnitID=units.spdf@data$UnitID, MedModelVal=NA, MedModelValBest=NA )} 
            
          }
          
          if(Model=="HSI"){
            print("computing HSI Medians")
            
            if(species=="chnk"){rasterpath=paste(HSIpath,"\\Output\\FuzzyChinookSpawner_DVSC.tif", sep="")}
            
            if(species=="sthd"){rasterpath=paste(HSIpath,"\\Output\\FuzzySteelheadSpawner_DVSC.tif", sep="")}
            
            if(file.exists(rasterpath)){
              hsi.raster=raster(rasterpath)
              proj4string(hsi.raster)=CRS(proj4string(units.spdf))
              
              MHSI=raster::extract(hsi.raster, units.spdf, fun=median, na.rm=T, df=T)
              names(MHSI)=c("ID", "MedModelVal")
              medians.sum=cbind(units.spdf@data,MHSI)
              medians.sum=medians.sum[,c(which(names(medians.sum)=="UnitID"),which(names(medians.sum)=="MedModelVal"))]
              
            } else {medians.sum=tibble(UnitID=units.spdf@data$UnitID, MedModelVal=NA )}
            
          } 
            
        } else {medians.sum=tibble(UnitID=units.spdf@data$UnitID, MedModelVal=NA )}
            
          
          fish.sum=predfish.sum%>%
            full_join(hab.sum, by="UnitID")%>%
            full_join(medians.sum, by="UnitID")
          
          #print("head(fish.sum)")
          #print(head(fish.sum))
          #print("tail(fish.sum)")
          #print(tail(fish.sum))
          
          if(exists("hab")){
            if(is.na(figdir)==F){
              print("plotting fish data")
              pdf(paste(figdir,"\\VISIT_" ,visit,"_", Model, layer, species ,".pdf", sep=""), width=11, height=11)
              par(mfrow=c(1,1))
              
              #plot(units.spdf, main=visit)
              #plot(hab, col=c(5,3), add=T)
              
              if(exists("hab")==T){
              plot(hab, col=c(5,4), main=visit)
              if(exists("fish.spdf")==T){
              points(fish.spdf, pch=16, col="yellow", cex=.7)
              }}
              dev.off()  
            }
          }
   
          return(fish.sum)
        }
        
        
        if(Model=="NREI") {
          print("summarizing NREI data")
          habpath=paste(NREIpath, "\\suitableNreiPoly.shp", sep="")
          predfishpath=paste(NREIpath, "\\predFishLocations.csv", sep="")
          
        }
        
        if(Model=="HSI") { 
          print("summarizing HSI data")
          if(species=="chnk"){
            habpath=paste(HSIpath, "\\Output\\suitableChnkPoly.shp", sep="")
            predfishpath=paste(HSIpath, "\\reddPlacement\\chkPredReddLocs.csv", sep="")
          }
          if(species=="sthd"){
            habpath=paste(HSIpath, "\\Output\\suitableSthdPoly.shp", sep="")
            predfishpath=paste(HSIpath, "\\reddPlacement\\sthdPredReddLocs.csv", sep="")
            
          }
        }
        
        fish.sum= habsumfunc(habpath, predfishpath, Model=Model, species=species)
        
        
        #Plot figure to cross check validity of spatial reference and extraction
        #print("head(fish.sum) after function return")
        #print(head(fish.sum))

        #joins data with attributes from Unit shapefile  
        form.units=units.spdf@data%>%
          full_join(fish.sum, by="UnitID")
        
        #print("head(form.units) after full join with unitdata")
        #print(head(form.units))
        
        #Sets fish and habitat values to zero where Model values exist
        if(ModelMedians==T){
        form.units$SuitArea[which(is.na(form.units$SuitArea) & is.na(form.units$MedModelVal)==F)]=0
        form.units$BestArea[which(is.na(form.units$BestArea)& is.na(form.units$MedModelValBest)==F)]=0
        form.units$No.Fish[which(is.na(form.units$No.Fish)& is.na(form.units$MedModelVal)==F)]=0
        form.units$No.FishBest[which(is.na(form.units$No.FishBest)&is.na(form.units$MedModelValBest)==F)]=0
        }
        
        #print("head(form.units)")
        #print(head(form.units))
        
        #adds visit ID
        form.units$VisitID=visit
        
        return(form.units)
      } else {print("No results when cropping GUT by Delft extent")}
     # } else {print("crop did not produce units.spdf")}
    } else {print("unable to crop due to missing DELFT extent")}
  } else {print("GUT output did not exist")}
}



#