#This script Makes map of GUT output whith fish pts plotted on top"

#Natalie Kramer (n.kramer.andersonn@gmail.com)
#updated March 12, 2018


library(rgdal)
library(rgeos)
library(raster)

#source('extractIDfrompath.R')

#This script Relys on the following GUT data files. If any of these are missing, the code
#should still run nothing will be drawn on the output map.

makeGUToverlaymaps=function(overlaypath, overlaydir="NREI", overlayname="", layer, figdir, Run, unitcolors=NA,
                     plotthalweg=F, plotthalwegs=F, plotcontour=F){
  
  visit=extractvisitfrompath(overlaypath)
  
  GUTrunpath=paste(strsplit(overlaypath, overlaydir)[[1]][1],"GUT/Output/GUT_2.1/", Run, sep="") 
  
  
  #Creates path to general GUT folder from your run path
  GUTpath=strsplit(GUTrunpath, "Output")[[1]][1]
  WaterExtentpath=paste(GUTrunpath, "Tier1.shp",sep="\\")
  contourpath=paste(GUTpath,"EvidenceLayers", "DEM_Contours.shp", sep="\\")
  GUpath=paste(GUTrunpath, "\\" , layer, ".shp",sep="")
  thalwegpath=paste(GUTpath,"Inputs", "Thalweg.shp", sep="\\")
  thalwegspath=paste(GUTpath,"Inputs", "Thalwegs.shp", sep="\\")
  
    #reads in polygon of just submerged flow from Tier1
  if(file.exists(WaterExtentpath)){
    WE.poly=readOGR(WaterExtentpath)
    if(gIsValid(WE.poly)==F){
      WE.poly=gBuffer(WE.poly, byid=TRUE, width=0)
      print("geometry fixed")
    }
  } else {print("Tier1.shp does not exist")}
  
  
  #reads in contour file from evidence folder
  if(plotcontour==T){
    if(file.exists(contourpath)){
      contours=readOGR(contourpath)
      #   if(gIsValid(contour)==F){
      #     contours=gBuffer(contours, byid=TRUE, width=0)
      #     print("geometry fixed")
      #   }
    } else {print("DEM_Contours.shp does not exist")}
  }
  
  
  #reads in polygon of GUT output
  if(file.exists(GUpath)){
    GU.poly=readOGR(GUpath)
    if(gIsValid(GU.poly)==F){
      GU.poly=gBuffer(GU.poly, byid=TRUE, width=0)
      print("geometry fixed")
    }
  } else {print(paste(layer, "does not exist"))}
  

  
  if(plotthalweg==T){
    if(file.exists(thalwegpath)){
      thalwegs=readOGR(thalwegpath)
    } 
  }
  
if(plotthalwegs==T){
  if(file.exists(thalwegspath)){
      thalwegs=readOGR(thalwegspath)
    } 
  }
  
  if(file.exists(overlaypath)){
      overlay=readOGR(overlaypath)
    }

  
  #sets colors output
  
  if(exists("GU.poly")){
    if(length(grep("Tier2",layer))>0 ){
      if(is.na(unitcolors)[1]==T){
        
        
        unitcats=c("Saddle", "Bowl","Mound","Plane", "Trough", 
                   "Bowl Transition", "Mound Transition")
        
        unitcolors=c(Bowl="royalblue",Mound="darkred",Plane="khaki1",Saddle="orange2",Trough="lightblue",Wall= "grey10",
                     `Bowl Transition`="aquamarine", `Mound Transition`="pink")
      }
      GU.poly@data$GUcolor=unitcolors[match(as.character(GU.poly@data$UnitForm), names(unitcolors))]
    }
    
    if(length(grep("Tier3",layer))>0 ){
      if(is.na(unitcolors)[1]==T){
        unitcats=c("Pocket Pool", "Pool", "Pond", "Margin Attached Bar", "Mid Channel Bar" ,
                   "Riffle", "Cascade", "Rapid", "Run-Glide", "Chute", "Transition", "Bank")
        unitcolors=c(`Pocket Pool`="light blue", Pool="royalblue", Pond="dark green", `Margin Attached Bar`="darkred", `Mid Channel Bar`="brown2" , 
                     Riffle="orange2", Cascade="pink", Rapid="green", Chute="aquamarine" ,
                     `Glide-Run`="khaki1", Transition="grey90", Bank="grey10")
      }
      
      GU.poly@data$GUcolor=unitcolors[match(as.character(GU.poly@data$GU), names(unitcolors))]
    }
  }
    
  
  print("creating summary plot")
  pdf(paste(figdir,"\\" ,"GUmap_",overlaydir, "_Visit_" , visit,  "_" ,Run ,"_",layer, ".pdf", sep=""), width=11.5, height=8)
  par(mfrow=c(1,1), mar=c(3,6,3,0), oma=c(0,0,0,12))
  
  if(exists("GU.poly")){
    plot(GU.poly, col=GU.poly@data$GUcolor)
    title(paste("VISIT", visit, Run, layer, sep=" "), cex.sub=3)
    
    #adding Coordinates
    xat <- pretty(extent(GU.poly)[1:2])
    xlab <- paste0(xat, " E")
    yat <- pretty(extent(GU.poly)[3:4])
    ylab <- paste0(yat, " N")
    box()
    axis(1, at=xat, labels=xlab)
    axis(2, las=TRUE, at=yat, labels=ylab)

    #plotting overlay data
    if(exists("contours")){
      plot(contours, add=T, cex=.7, col="black")}
    if(exists("thalweg")){
      plot(thalweg, add=T, cex=.7, lty=2, lwd=2, col="blue")}
    if(exists("thalwegs")){
      plot(thalwegs, add=T, cex=.7, lty=2, col="black")}
    if(exists("overlay")){
      points(overlay, pch=21, cex=.0001*gArea(WE.poly), lty=2, col="blue", bg="white")}
      #points(overlay, pch=21, cex=.7, lty=2, col="blue", bg="white")}
    
    #adds legend
  #  legend("bottomright",
    legend(par('usr')[2], par('usr')[4], bty='n',
           legend=c(names(unitcolors), overlayname),  ncol=1, xpd=NA,
           col=c(c(unitcolors),"blue"), bg=c(rep(NA,length(unitcolors)),"white"), pch=c(rep(15,length(unitcolors)),21), pt.cex=2, cex=1.2)

  }
  
  dev.off()
  
  
}
