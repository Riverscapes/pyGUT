#############################################################
#function for returning intersection pts between poly and line
########################################################
#Note- I'm not entirely pleased with this, it does miss some intersections.  I think that there must be a better way to do this.


intersectpts=function(intersectedline, inputpoly, plottitle=""){
  x=2*rep(NA, length(intersectedline))
  y=2*rep(NA, length(intersectedline))
  xylast=cbind(x,y)
  xy1=cbind(x,y)
  
  for(i in 1:length(intersectedline)){
    xy1[i,] <- coordinates(intersectedline)[[i]][[1]][1,]
    lastpoint=length(coordinates(intersectedline)[[i]][[1]][,1])
    xylast[i,] <- coordinates(intersectedline)[[i]][[1]][lastpoint,]
    i=i+1
  }
  
  xy=rbind(xy1,xylast)
  
  #pdf(paste(plottitle,"pdf", sep="."))
  plot(inputpoly, main=plottitle)
  lines(intersectedline, col="red")
  points(xy, col="blue")
 # dev.off()
  
  return(xy)
}
