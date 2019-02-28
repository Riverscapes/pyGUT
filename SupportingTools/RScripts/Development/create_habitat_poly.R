#Creates polygons from raster based on user defined splits.

#Natalie Kramer (n.kramer.anderson@gmail.com)
#updated Oct 28, 2017

####inputs#####
#inraster: the name of the inpt raster (ex. "suitableNreiRaster.tif")
#dir: The path to the input raster
#mybreaks: a vector of numbers specifying on what values to split the raster.
          #Default is c(0, median, max) which gives two categories.

###Example####
#dir='E:\\Box Sync\\ET_AL\\Projects\\USA\\ISEMP\\GeomorphicUnits\\FifteenStartingSites\\Data\\VisitData\\VISIT_3415\\HSI\\Sims\\FIS\\Output'
#inraster="FuzzyChinookSpawner_DVSC.tif"
#mybreaks=c(0.4,0.8,1)

Createhabitatpoly=function(inraster, dir, layer="habpoly", mybreaks=c(0,
                                                      cellStats(data.raster,median),
    
                                                      cellStats(data.raster,max))){  #add optional argument to threshold at would be nice
  #setwd(dir)
  #rm(data.raster)
  
    if(file.exists(paste(dir,inraster, sep="//"))){
      
      print(extractvisitfrompath(dir))
      data.raster=aggregate(raster(paste(dir,inraster, sep="//")))
        
       #splits into two classes based on Good-Median and Median to Max and makes a polygon shapefile
      data.cut=cut(data.raster, mybreaks)
      data.poly=rasterToPolygons(data.cut, dissolve = TRUE)
      
      print("writing files")
      
      #dsn=strsplit(inrasterpath, "\\VISIT")[[1]][1]
      
      writeOGR(data.poly, dir, layer=layer , overwrite_layer=TRUE, driver="ESRI Shapefile")
      
    } else {print("unable to run due to missing raster input file")} 
}


#dir='E:\\Box Sync\\ET_AL\\Projects\\USA\\ISEMP\\GeomorphicUnits\\FifteenStartingSites\\Data\\VisitData\\VISIT_3415\\HSI\\Sims\\FIS\\Output'
#inraster="FuzzyChinookSpawner_DVSC.tif"
#mybreaks=c(0.4,0.8,1)