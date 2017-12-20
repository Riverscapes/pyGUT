---
title: Numeric Attributes
---

#####Area (A)
Total area of the unit calculated from shape geometry.	

#####Width (W)
average width of unit calculated as the area of the unit divided by length.	

#####Length (L)		
Maximum length of minimum bounding rectangle.

#####Perimeter (P)
Total length of unit boundary calculated from shape geometry.

#####LtoWRatio
Length of the unit divided by the width of the unit.	

#####ElongRatio
ElongRatio=*2 (sqrt(Area/pi)/L)

Elongation ratio calculated as the diameter of a circle with the same area as that of the shape divided by maximum shape length. 

#####Orient
Orientation of the unit relative to the centerline.  orientations are calculated using minimum bounding geometry.  

#####bfSlope
Bankfull stage water surface slope.  Calculated in degrees.		

#####bfSlopeSm
Average bankfull stage water surface slope.  Calculated over a bankfull width x bankfull width window

#####bedSlope
Average bed slope of the unit.

#####bfwRatio	
Width of the unit divided by the reach averaged bankfull width.	

#####Roundess	
*Roundness=Area/Pc^2*

Where Pc is the convex perimeter of the shape (the perimeter of a rubber band if it was stretched around the shape, resting on the shapes most prominent vertices)

The maximum value is 1, shapes with irregular boundaries have lower values (van der Werff and van der Meer, 2008; Williams, 2014; Meshkova and Carling, 2013).

#####Convexity		
*Convexity= Pc/P* 

where Pc is the convex perimeter of the shape (the perimeter of a rubber band if it was stretched around the shape, resting on the shapes most prominent vertices)

Values of 1 indicate that the curvature of any location on the perimeter is convex (van der Werff and van der Meer, 2008; Williams, 2014; Meshkova and Carling, 2013)

#####Compactness
*Compactness=4pi(A/P^2)*
Denotes how similar the shape is to a circle.  If compactness is one it is a perfect circle.  Lower values are associated with deviations from circles.	(van der Werff and van der Meer, 2008; Williams, 2014; Meshkova and Carling, 2013)

#####Relief (R)
Maximum elevation of unit minus minimum elevation of unit using DEM	

#####Vcompact	
Vertical Compactness as a ratio of relief over maximum length of the unit. Units greater than one are thicker than they are long (Sneed and Folk, 1958; Williams, 2014)	

#####Platyness	
Ratio of relief compared to width.  For values greater than one the unit is thicker than it is wide (Krumbein, 1941; Williams, 2014)		

#####Sphericity		
*Sphericity=(Area/(Length x width))/Relief*
Closeness of the shape to a perfect sphere (Krumbein, 1941; Williams, 2014)	

#####ProfCurv		
Curvature in direction of maximum slope per cell in the DEM averaged over the unit (ESRI, 2016).

#####PlanCurv		
Curvature perpendicular to maximum slope per cell averaged over the unit (ESRI, 2016)		
#####mBend		
Bankfull channel meander bend index value nearest to the unit centroid.  The meander bend index is calculated over a bankfull width by bankfull width moving window. For each bankfull channel edge cell, difference the number of dry (out-of-channel) and wet (in-channel) cells.  Positive values indicate outside of bends, negative values indicate inside of bends, and values near zero indicate straight sections of the channel.	**(add citation)**		

####References

ESRI, 2016. Curvature Function. ArcMap10.3. Accessed Dec., 19, 2017. http://desktop.arcgis.com/en/arcmap/10.3/manage-data/raster-and-images/curvature-function.htm

Krumbein, W. C., 1941. Measurement and geological significance of shape and roundness of sedimentary particles, Journal of Sedimentary Petrology, 11(2), 64- 72.

Meshkova, L.V. & Carling, P.A., 2012. The geomorphological characteristics of the Mekong River in northern Cambodia: A mixed bedrock-alluvial multi-channel network. Geomorphology, 147, pp.2–17.

Sneed, E.D. & Folk, R.L., 1958. Pebbles in the lower Colorado River, Texas a study in particle morphogenesis. The Journal of Geology, 66(2), pp.114–150.

Van der Werff, H. & Van der Meer, F., 2008. Shape-based classification of spectrally identical objects. ISPRS Journal of Photogrammetry and Remote Sensing, 63(2), pp.251–258.

Williams, R., 2014. Two-dimensional numerical modelling of natural braided river morphodynamics.




​			

#Not used anymore....?
####wRatioMin		
The minimum cross section width ratio for the unit.  The cross section width ratio is calculated in the downstream direction for each bankfull cross section as: width(i) - width(i+1).  Values < 1 indicate channel expansion.  Values > 1 indicate channel constriction.		

#####wRatioMax		
The maximum cross section width ratio for the unit.  The cross section width ratio is calculated in the downstream direction for each bankfull cross sections as: width(i) - width(i+1). Values > 1 indicate channel constriction.

Not calculated that could be good					
AvgThickness		Some measure of average thickness.  Take Relief of all cells then average the Reliefs?  Or A/L/W			
Evenness		ratio of average thickness udivided by the maximum thickness. The Lower the number the more the average thickness deviates from the maximum thickness and the more tapered the feature