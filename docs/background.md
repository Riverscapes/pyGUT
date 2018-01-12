---
title: Background
---

The Geomorphic Unit Tool (GUT) workflow is structured around a 3-tiered hierarchcial classification (Figure 1) adapted from  [Wheaton et al (2015)](https://doi.org/10.1016/j.geomorph.2015.07.010).  The Wheaton classification was modified to include attributes from the Geomorphic Unit Survey ([Belletti et al, 2017](https://doi.org/10.1016/j.geomorph.2017.01.032); [Rinaldi et al, 2015](http://www.reformrivers.eu/system/files/6.2%20Methods%20to%20assess%20hydromorphology%20of%20rivers%20part%20III%20revised_0.pdf)) to better handle variations in flow stage.  

[![GUT_Framework]({{site.baseurl}}/assets/images/GUT_Framework.png)]({{site.baseurl}}/assets/images/hr/GUT_Framework.png)
Figure 1. Hierarchichal framework adapted from Wheaton et al (2015).

## Wheaton Fluvial Taxonomy

Wheaton’s fluvial taxonomy [(Wheaton et al., 2015)](https://doi.org/10.1016/j.geomorph.2015.07.010)  differentiates geomorphic units based on stage height (Tier 1), topographic shape (Tier 2), geomorphic attributes such as position and orientation (Tier 3), and patch characteristics such as vegetation and grain size (Tier 4). Furthermore, instream elements which are not shaped by the deposition and erosion of sediments are mapped as structural elements (e.g. logs, boulders, vegetation and man-made structures) and used to further differentiate geomorphic unit type (e.g., dam forced pool). The advantages of this scheme are: 1) after in-channel regions are identified at Tier 1, the delineation of units, such as the extent of bars, is flow independent, and 2) geomorphic units can be examined in relation to the spatial distribution of structural elements.   At this time, we have not incorporated Tier 4 patch attributes such as vegetation and grain size, but a workflow could be easily added that uses the output from Tier 3 along with additional patch characteristic input file to create patch level geomorphic units.  

## Geomorphic Unit System (GUS)

The Geomorphic Unit System (GUS) was developed independently around the same time as the Wheaton taxonomy and shares several similarities.  However, rather than focusing on deriving units from topography, GUS focuses on first classifying units from satellite and aerial imagery [(Belletti et al, 2017)](https://doi.org/10.1016/j.geomorph.2017.01.032). Once a region is mapped at the macro level, it is visited and mapped in finer detail at a unit or subunit scale based on identifying characteristics such as hydraulic conditions and process of formation. Units and subunits are identified using a guidebook of all possible units and subunits within each macro unit [(Rinaldi et al, 2015)](http://www.reformrivers.eu/system/files/6.2%20Methods%20to%20assess%20hydromorphology%20of%20rivers%20part%20III%20revised_0.pdf). This approach is flow dependent rather than independent, which is advantageous for exploring questions relating flow to geomorphic units.  

## Topographic Form Classification

GUT includes a new topographic form attribute classification scheme at the Tier 2 level (Bangen et al, In Prep) that further differentiates topogaphic shapes into forms with similar topographic signatures: bowls, mounds, planes, troughs and walls (Figure 2).   During development, we discovered that these forms were needed to better segment topography prior to unit designation at the Tier 3 level.  Because the boundaries between these forms are inherently fuzzy, we also output a Tier 2 transitions shapefile which includes bowl transitions and mound transitions.  Boundaries are placed based on user-defined thresholds set in the configure file.  Analysis of transition zones can be conducted by adjusting these dials and comparing output. 

[![shapeContour]({{site.baseurl}}/assets/images/shapeContour.png)]({{site.baseurl}}/assets/images/hr/shapeContour.png)
Figure 2.  Generalized topographic shape (top) and contour signatures (bottom) for each of the main forms delineated by GUT.
