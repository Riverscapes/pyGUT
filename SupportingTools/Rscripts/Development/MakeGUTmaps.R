#This script Makes map of GUT output whith fish pts plotted on top"

#Natalie Kramer (n.kramer.andersonn@gmail.com)
#updated Aug 30, 2017


library(rgdal)
library(rgeos)

#Inputs
#GUTrunpath: path to GUT run folder
GUTrunpath= "E:\\Box Sync\\ET_AL\\Projects\\USA\\ISEMP\\GeomorphicUnits\\Data\\VisitData/VISIT_1027/GUT/Output/GUT_2.1/Run_01"
#optional- specify colors for attribute classes in a vector 
#for example: shape.colors=c(Planar="khaki1", Convexity="orange2", Concavity="royalblue")

#spits out figure in specified directory as VISIT_####.pdf

MakeGUTmaps=function(GUTrunpath, figdir, shape.colors=NA, form.colors=NA, GU.colors=NA,
                     plotfish=F, plotthalweg=T, plotcontour=T){
  
  rm(fish)
  rm(thalwegs)
  rm(contours)
  rm(GU.poly)
  rm(WE.poly)
  rm(form.poly)
  rm(nrei.poly)
  
  visit=extractvisitfrompath(GUTrunpath)
  
  #Creates path to NREI data based on GUT path
  NREIpath=paste(strsplit(GUTrunpath, visit)[[1]][1], visit,"/NREI",sep="")
  #Creates path to general GUT folder
  GUTpath=paste(strsplit(GUTrunpath, visit)[[1]][1], visit,"/GUT",sep="")
  
  
  #reads in polygon of just submerged flow from Tier1
  if(file.exists(paste(GUTrunpath, "Tier1.shp",sep="\\"))){
    WE.poly=readOGR(paste(GUTrunpath, "Tier1.shp",sep="\\"))
    if(gIsValid(WE.poly)==F){
      WE.poly=gBuffer(WE.poly, byid=TRUE, width=0)
      print("geometry fixed")
    }
  } else {print("Tier1.shp does not exist")}
  
  
  #reads in contour file from evidence folder
  if(plotcontour==T){
    if(file.exists(paste(GUTpath,"EvidenceLayers", "DEM_Contours.shp", sep="\\"))){
      contours=readOGR(paste(GUTpath,"EvidenceLayers", "DEM_Contours.shp", sep="\\"))
      #   if(gIsValid(contour)==F){
      #     contours=gBuffer(contours, byid=TRUE, width=0)
      #     print("geometry fixed")
      #   }
    } else {print("DEM_Contours.shp does not exist")}
  }
  
  
  #reads in polygon of Tier2 forms
  if(file.exists(paste(GUTrunpath, "Tier2_InChannel_Transition.shp",sep="\\"))){
    form.poly=readOGR(paste(GUTrunpath, "Tier2_InChannel_Transition.shp",sep="\\"))
    if(gIsValid(form.poly)==F){
      form.poly=gBuffer(form.poly, byid=TRUE, width=0)
      print("geometry fixed")
    }
  } else {print("Tier2_InChannel.shp does not exist")}
  
  #reads in polygon of Tier3 GUs
  if(file.exists(paste(GUTrunpath, "Tier3_InChannel_GU.shp",sep="\\"))){
    GU.poly=readOGR(paste(GUTrunpath, "Tier3_InChannel_GU.shp",sep="\\"))
    if(gIsValid(GU.poly)==F){
      GU.poly=gBuffer(GU.poly, byid=TRUE, width=0)
      print("geometry fixed")
    }
  } else {print("Tier3_InChannel_GU.shp does not exist")}
  
  
  #reads in fish locations and creates spatial points data frame
  if(plotfish==T){
    if(file.exists(paste(NREIpath,"predFishLocations.shp", sep="\\"))){
      fish=readOGR(paste(NREIpath,"predFishLocations.shp", sep="\\"))
    }
    if(file.exists(paste(NREIpath,"NREIextent.shp", sep="\\"))){
      nrei.poly=readOGR(paste(NREIpath,"NREIextent.shp", sep="\\"))
    }
  }
  
  #if(file.exists(paste(GUTpath,"Inputs", "Bankfull.shp", sep="\\"))){
  #  bankfull=readOGR(paste(GUTpath,"Inputs", "Bankfull.shp", sep="\\"))
  #  }
  
  if(plotthalweg==T){
    if(file.exists(paste(GUTpath,"Inputs", "Thalwegs.shp", sep="\\"))){
      thalwegs=readOGR(paste(GUTpath,"Inputs", "Thalwegs.shp", sep="\\"))
    } 
  }
  
  
  
  #sets colors for tier 2 output
  if(exists("form.poly")){
    if(is.na(shape.colors)==T){
      shape.colors=c(Planar="khaki1", Convexity="orange2", Concavity="royalblue")
    }
    
    if(is.na(shape.colors)==T){
      form.colors=c(Bowl="royalblue",Mound="darkred",Plane="khaki1",Saddle="orange2",Trough="lightblue",Wall= "darkgrey",
                    `Bowl Transition`="aquamarine", `Mound Transition`="pink")
    }
    form.poly@data$formcolor=form.colors[match(as.character(form.poly@data$UnitForm), names(form.colors))]
    form.poly@data$shapecolor=shape.colors[match(as.character(form.poly@data$UnitShape), names(shape.colors))]
  }
  
  if(exists("GU.poly")){
    if(is.na(shape.colors)==T){
      GU.colors=c(`Pocket Pool`="light blue", Pool="royalblue", Pond="dark green", `Margin Attached Bar`="dark red", `Mid Channel Bar`="brown" , 
                  Riffle="orange2", Cascade="white", Rapid="turquoise", Chute="aquamarine" ,
                  `Glide-Run`="khaki1", Transition="grey", Bank="dark grey")
    }
    GU.poly@data$GUcolor=GU.colors[match(as.character(GU.poly@data$GU), names(GU.colors))]
  }
  
  
  
  
  print("creating summary plot")
  pdf(paste(figdir,"\\Maps\\VISIT_" ,visit,".pdf", sep=""), width=24, height=11)
  par(mfrow=c(1,3))
  
  if(exists("form.poly")){
    plot(form.poly, col=form.poly@data$shapecolor)
    title(paste("VISIT_", visit," Tier2 Shape", sep=""), cex.sub=3)
    if(exists("fish")){
      plot(fish, add=T, pch=16, cex=.7, col="white")}
    if(exists("contours")){
      plot(contours, add=T, cex=.7, col="black")}
    if(exists("thalwegs")){
      plot(thalwegs, add=T, cex=.7, lty=2, col="black")}
    if(exists("nrei.poly")){
      plot(nrei.poly, add=T, cex=.7, lty=1, lwd=3)}
    legend("bottomright",
           legend=c(names(shape.colors)), horiz=T,
           col=c(shape.colors),  pch=rep(15,6), cex=1.2, pt.cex=2)
    
    
    plot(form.poly, col=form.poly@data$formcolor)
    title(paste("VISIT_", visit," Tier2 Form", sep=""), cex.sub=3)
    if(exists("fish")){
      points(fish,  pch=16, cex=.7, col="black")}
    if(exists("contours")){
      plot(contours, add=T, cex=.7, col="black")}
    if(exists("thalwegs")){
      plot(thalwegs, add=T, cex=.7, lty=2, col="black")}
    if(exists("nrei.poly")){
      plot(nrei.poly, add=T, cex=.7, lty=1, lwd=3)}
    legend("bottomright",
           legend=c(names(form.colors)),  ncol=2,
           col=c(form.colors),  pch=rep(15,6), pt.cex=2, cex=1.2)
  }
  
  if(exists("GU.poly")){
    plot(GU.poly, col=GU.poly@data$GUcolor)
    title(paste("VISIT_", visit," Tier3 GU", sep=""), cex.sub=3)
    if(exists("fish")){
      points(fish,  pch=16, cex=.7, col="black")}
    if(exists("contours")){
      plot(contours, add=T, cex=.7, col="black")}
    if(exists("thalwegs")){
      plot(thalwegs, add=T, cex=.7, lty=2, col="black")}
    if(exists("nrei.poly")){
      plot(nrei.poly, add=T, cex=.7, lty=1, lwd=3)}
    legend("bottomright",
           legend=c(names(GU.colors)),  ncol=2,
           col=c(GU.colors),  pch=rep(15,6), pt.cex=2, cex=1.2)
  }
  
  dev.off()
  
  
}


MakeUNITIDboxplots=function(datapath, colors=GU.colors, datatyp="GU", extent="suitable"){
  
  data=read.csv(datapath, )
  
  s.data=filter(data, Extent=="Suitable")
  b.data=filter(data, Extent=="Best")
  w.data=filter(data, Extent=="Water")
  
  attributecol=which(names(data)==attribute)
  
  if(attribute=="UnitForm"){
    unit.colors=c(Bowl="royalblue",Mound="darkred",Plane="khaki1",Saddle="orange2",
                  Trough="lightblue",Wall= "dark grey", `Bowl-Trough`="turquoise", `Plane-Mound`="pink", 
                  `Trough-Plane`="green", Transition="beige", `Bowl Transition`="turquoise", 
                  `Mound Transition`="pink", `Bed Transition`="green", 'NA'="white")}
  
  if(attribute=="GU"){
    unit.colors=c(`Pocket Pool`="blue", Pool="dark blue", Pond="green", `Margin Attached Bar`="darkred", `Mid Channel Bar`="brown" , 
                  Riffle="orange2", Step="pink", Cascade="dark green", Rapid="turquoise", `Glide-Run`="yellow", Chute="lightblue", Transition="grey", Bank="dark grey")}
  
  
  
  pdf(paste(figdir, "NoFishpsqm.pdf", sep="//"))
  par(mfrow=c(1,3), mar=c(8,4,2,1))
  
  #    boxplot(w.data$No.Fish/w.data$Area~w.data[,attributecol], las=2, col=as.character(w.data$formcolor), ylab="No.Fish/sq.m", main="Wetted Extent")
  boxplot(w.data$No.Fish/w.data$Area~w.data[,attributecol], las=2, col=unit.colors[match(as.factor(w.data$formcolor), names(form.colors))], ylab="No.Fish/sq.m", main="Wetted Extent")
  outliers=w.data[which(w.data$No.Fish/w.data$Area>0.6),]
  if(dim(outliers)[1]>0){text(outliers[,attributecol], outliers$No.Fish/outliers$Area, outliers$visit)}
  
  boxplot(s.data$No.Fish/s.data$Area~s.data[,attributecol], las=2, col=as.character(s.data$formcolor), ylab="No.Fish/sq.m", main="Suitable Area")
  outliers=s.data[which(s.data$No.Fish/s.data$Area>2),]
  if(dim(outliers)[1]>0){text(outliers[,attributecol], outliers$No.Fish/outliers$Area, outliers$visit)}
  
  boxplot(b.data$No.Fish/b.data$Area~b.data[,attributecol], las=2, col=as.character(b.data$formcolor), ylab="No.Fish/sq.m", main="Best Area")
  outliers=b.data[which(b.data$No.Fish/b.data$Area>2),]
  if(dim(outliers)[1]>0){text(outliers[,attributecol], outliers$No.Fish/outliers$Area, outliers$visit)}
  dev.off()
  