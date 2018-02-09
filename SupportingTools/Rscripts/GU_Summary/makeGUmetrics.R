#Natalie Kramer (n.kramer.anderson@gmail.com)
#updated Oct 29, 2017

#This script will take any GUT outuput and with the output layer and attribute specified summarize basic
#geometries by the attribute.

#required input 
#GUTrunpath: a path to the GUT run that the analysist is interested in.
#layer: Which shape file in the run folder is of interest?
#attribute: What is the name of the attribute field that you want to summarize over?

#optional input
#unitcats: what is the full list of attribute category possibible, if not specified will use list based on attribute (right now just coded for basic UnitForm GU)

#Outputs (grouped by attribute class)
#units will depend on input spatial class, gut is in UTM so...
#medArea=median of Area of all polygons (m2)
#medPerim=median of Perimeter of all Polygons (m) 
#avgArea= average area of all polygons  (m2)
#avgPerim=average Perimeter of all polygons (m)
#sdArea=st dev of Area '(m2)
#sdPerim= st dev of Perimeters (m)
#totArea= sum of all areas (m2)
#totPerim= sum of all perimeters (m)
#n= total count of polygons (#)
#PercArea = totArea/sum(totArea)*100 (%)- percent of reach covered by each unity type
#PerimbyArea =avgPerim/avgArea


#library dependencies: 
library(rgdal)
library(rgeos)
library(dplyr)

#you need to find and source this script
source("extractIDfrompath.R")


makeGUmetrics=function(GUTrunpath, layer="", attribute="", unitcats="None"){

  visit=extractvisitfrompath(GUTrunpath)
  GUpath=paste(GUTrunpath, paste(layer, ".shp",sep=""), sep="\\")

  #rm(Unit.poly)
  #rm(Perim)
  #rm(Area1)
  #rm(unitsummary)
  #rm(attributecol)
  
  ################################
  print("Calculating Metrics")
  #reads in Tier2
  if(file.exists(GUpath)){
    Unit.poly=readOGR(GUpath)
    if(gIsValid(Unit.poly)==F){
      Unit.poly=gBuffer(Unit.poly, byid=TRUE, width=0)
      print("geometry fixed")
    }
    #get perimeter data by unit
    Perim=gLength(Unit.poly, byid=T)
    #get Area by unit
    Area1=round(gArea(Unit.poly, byid=T),1) #since it is already in attribute table we don't need this
    
    #Corrects GIS Area output if it doesn't match area calculation above
    if (sum(Area1-Unit.poly@data$Area)!=0) {
      Unit.poly@data$Area=Area1
    }
    
    ##More by unit metrics can be added here--- for shape and etc.
    
   attributecol=which(colnames(Unit.poly@data)==attribute)
          
    #adds column with perimeter data
    data=cbind(Unit.poly@data, "Perim"=round(Perim,1))
    
    #perimeter and area summaries for each UnitForm unit
    medUnit=data %>% group_by(data[,attributecol]) %>% summarize_at(c("Area", "Perim"), median, na.rm = TRUE)
    meanUnit=data %>% group_by(data[,attributecol]) %>% summarize_at(c("Area", "Perim"), mean, na.rm = TRUE)
    sdUnit=data %>% group_by(data[,attributecol]) %>% summarize_at(c("Area", "Perim"), sd, na.rm = TRUE)
    sumUnit=data %>% group_by(data[,attributecol]) %>% summarize_at(c("Area", "Perim"), sum, na.rm = TRUE)
    nUnit=data %>% count(data[,attributecol]) 
    
    
    #combines data
    unitsummary=cbind(medUnit, meanUnit[2:3], sdUnit[,2:3], sumUnit[,2:3],nUnit[,2])
    names(unitsummary)=c("Unit","medArea", "medPerim","avgArea", "avgPerim",  "sdArea","sdPerim", "totArea", "totPerim", "n")
    unitsummary$Unit=as.character(unitsummary$Unit)
   
  if((unitcats=="None")[1]){ 
    if(attribute=="UnitForm"){
    unitcats=c("Saddle", "Bowl","Mound","Plane", "Trough","Mound Transition", "Bowl Transition")
    }
    
    if(attribute=="GU"){
      unitcats=c("Pocket Pool", "Pool", "Pond", "Margin Attached Bar", "Mid Channel Bar" , "Riffle", "Cascade", "Rapid", "Run-Glide", "Transition", "Bank")
    }
  }
    
    for(i in length(unitcats)){
      if (unitcats[i] %in% unitsummary$Unit==F){unitsummary=rbind(unitsummary, c(unitcats[i], NA,NA,NA,NA,NA,NA, 0))}
  }
    
    #METRIC CALCULATIONS####################################################################################3

    unitsummary$percArea=round(as.numeric(unitsummary$totArea)/gArea(Unit.poly)*100,2)
    unitsummary$PeribyArea=round(as.numeric(unitsummary$avgPerim)/as.numeric(unitsummary$avgArea),2)
    unitsummary$VisitID=visit
    unitsummary$GUTrun=GUTrunpath
    
    print("returning unitsummary")
    return(unitsummary)
    print("done")
    
  } #else {print(paste(layer, "does not exist", sep=" "))}
}