#This function Makes map of GUT output and provides an example script on how to batch process"

#Natalie Kramer (n.kramer.anderson@gmail.com)
#updated Nov 9, 2018

#This function Relies on the GUT data files. If any are missing, the code
#should still run and a map file produced as a placeholder, but nothing will be drawn on the output map.

#This function also Relies on files in the file structure of GUT. With three directories of Inputs, OUtput and Evidence.  
#Within the output directory there should be a run folder that contains the outputs.

#####Variables
#GUTrunpath: The file path to output files from a GUT run (e.g. ".../GUT/Output/GUT_2.1/Run_01" )
#layer: Specify which GUT output layer you want to summarize (e.g. "Tier3_InChannel_GU" )
#figdir: the filepath to the directory to print the maps to (e.g....)
#unitcolors: specify a vector the colors for each unit type. It does this automatically for Tier 2 and Tier 3, if set to NA.
#overlaypath: path to desired overlay shapefile to be plotted on top of the GUT basemap.  If no overlay desired, set to NA.
#plotthalweg: T/F if you want to plot the main CHaMP Thalweg
#plotthalwegs: T/F if you want to plot the multiple thalweg layer (all thalwegs)
#plotcontour: T/F for plotting the contours.
#type: specify output as either ".pdf" of ".png" or ".jpg"
#extractID: a number which specifies which element from the full path name to extract as an ID label for the figure.  Elements are counted backwards from the end of the path.  
#         For example to extract 12 from path 'E:\A\12\b' you would define extractID to be 2, since it is the second from the end. If extractID=0, then it will automatically extract the visit number XXXX if in the format VISIT_XXXX.  
#extractID: a number which specifies another element from the full path name to extract as an ID lable for the figure. IF extractID=F then no element is extracted.
#####

makeGUTmaps=function(GUTrunpath, layer, figdir, unitcolors=NA, overlaypath=NA,
                     plotthalweg=T, plotthalwegs=T, plotcontour=T, type=".pdf",  extractID=F, extractID2=F){
 
  ###dependencies
  
  library(rgdal)
  library(rgeos)
  library(raster)
  
  
  split_path <- function(path) {
    if (dirname(path) %in% c(".", path)) return(basename(path))
    return(c(basename(path), split_path(dirname(path))))
  }
   
  #Extracts visit number from path name
    if(extractID!=F){
     ID1=split_path(GUTrunpath)[extractID]
     }
  
  #extracts a second id from the path name if desired
    if(extractID2!=F){
      ID2=split_path(GUTrunpath)[extractID2]
    }
  
  #Creates path to general GUT folder from your run path
  GUTpath=strsplit(GUTrunpath, "Output")[[1]][1]
  #Extracts name of your run folder to label titles on figures
  Run=split_path(GUTrunpath)[1]
  
  #specifies locations and paths to shape files to plot
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
  
  if(is.na(overlaypath)==F){
    if(file.exists(overlaypath)){
      myoverlay=readOGR(overlaypath)
    }
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
  
  if(extractID==F & extractID2==F){
    mytitle=paste(Run ,"_",layer, sep="")
  }
  
  if(extractID!=F & extractID2==F){
    mytitle=paste(ID1,"_",Run ,"_",layer, sep="")
  }
  
  if(extractID2!=F & extractID!=F){
    mytitle=paste(ID1,"_", ID2, "_",Run ,"_",layer, sep="")
  }
  
  filename=paste(figdir,"\\" ,"GUmap_", mytitle, type, sep="")

  if(type==".pdf"){
  pdf(filename, width=11.5, height=8)
  }
  
  if(type==".png"){
  png(filename, width=1275, height=850)
  }
  
  if(type==".jpg"){
    jpeg(filename, width=1275, height=850)
  }
  
  if(type==".tif"){
    tiff(filename,width=1275, height=850)
  }
  
  par(mfrow=c(1,1), mar=c(3,6,3,0), oma=c(0,0,0,10))
  
  if(exists("GU.poly")){
    plot(GU.poly, col=GU.poly@data$GUcolor)
    title(mytitle, cex.sub=3)
    
    #adding Coordinates
    xat <- pretty(extent(GU.poly)[1:2])
    xlab <- paste0(xat, " E")
    yat <- pretty(extent(GU.poly)[3:4])
    ylab <- paste0(yat, " N")
    box()
    axis(1, at=xat, labels=xlab)
    axis(2, las=TRUE, at=yat, labels=ylab)

    print("plotting contours and thalwegs")
    if(exists("contours")){
      plot(contours, add=T, cex=.7, col="black")}
    if(exists("thalweg")){
      plot(thalweg, add=T, cex=.7, lty=2, lwd=2, col="blue")}
    if(exists("thalwegs")){
      plot(thalwegs, add=T, cex=.7, lty=2, col="black")}
   
     print("plotting overlay data")
    if(exists("myoverlay")){
      plot(myoverlay, add=T, cex=.7, lty=2, col="black")}
    
    
     print("plotting legend")
    #adds legend
  #  legend("bottomright",
    legend(par('usr')[2], par('usr')[4], bty='n',
           legend=c(names(unitcolors)),  ncol=1, xpd=NA,
           col=c(unitcolors),  pch=rep(15,6), pt.cex=2, cex=1.2)

  }
  
  dev.off()
  
  
}



#Example Usage for batch processing of multiple GUT runs

##Create a list of all file paths to all GUT Runs you are interested in
#Datapath='E:\\Box Sync\\ET_AL\\Projects\\USA\\ISEMP\\GeomorphicUnits\\Data\\VisitData'
#GUTrunlist=list.dirs(Datapath)[grep("Run_01",list.dirs(Datapath))] 

#Datapath="E:\\Box Sync\\ET_AL\\Projects\\USA\\ISEMP\\GeomorphicUnits\\Data\\AsotinGUTfromAndy\\GUT_Natalie\\GUT\\Asotin"
#GUTrunlist=list.dirs(Datapath)[grep("Run_05",list.dirs(Datapath))] 

##Define local variables
#figdir="E:\\Box Sync\\ET_AL\\Projects\\USA\\ISEMP\\GeomorphicUnits\\Data\\AsotinGUTfromAndy\\GUT_Natalie\\GUT\\AsotinMaps\\Tier2_Transition"
#layer="Tier2_InChannel_Transition"

##Loop function through list

#for (i in c(1:length(GUTrunlist))){
# print(paste("i=",i, "starting", GUTrunlist[i]))
#  makeGUTmaps(GUTrunlist[i], layer, figdir, plotthalweg=T, plotthalwegs=T, plotcontour=F, overlaypath=NA, type=".pdf", extractID=5, extractID2=4)
#}
