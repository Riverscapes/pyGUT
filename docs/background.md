---
title: Background
---

[![GUTLogo]({{site.baseurl}}/assets/images/GUTLogo.png)]({{site.baseurl}}/assets/images/hr/GUTLogo.png)

The geomorphic unit tool (GUT) uses a workflow structured around a tiered framework from  [(Wheaton et al., 2015)](https://doi.org/10.1016/j.geomorph.2015.07.010) (Figure 1).  The Wheaton framework has been modified with attributes from the Geomorphic Unit Survey (GUS) ( [(Belletti et al., 2015)](http://www.reformrivers.eu/characterising-physical-habitats-and-fluvial-hydromorphology-new-system-survey-and-classification]); Rinaldi et al., 2015) to better handle variations in flow and includes a new scale invariant extraction of topographically defined forms.  

[![GUT_Framework]({{site.baseurl}}/assets/images/GUT_Framework.png)]({{site.baseurl}}/assets/images/hr/GUT_Framework.png)
Figure 1. Hierarchichal framework adapted from [(Wheaton et al., 2015)](https://doi.org/10.1016/j.geomorph.2015.07.010)

We provide further documentation on:
1. How to [run GUT]({{ site.baseurl }}/1.RunningGUT/index.md)
2. Descriptions of [GUT output]({{ site.baseurl }}/2.GUToutput/index.md)
3. Example [applications]({{ site.baseurl }}/3.Applications/index.md).
4. The [nuts and bolts]({{ site.baseurl }}/4.guDescriptions/index.md)  behind the algorithms.

####Wheaton Fluvial Taxonomy

Wheaton’s fluvial taxonomy  [(Wheaton et al., 2015)](https://doi.org/10.1016/j.geomorph.2015.07.010)  identifies shapes of landforms based on stage height (Tier 1), topographic expression (Tier 2), geomorphic attributes such as position and orientation (Tier 3), and patch characteristicssuch as vegetation and grain size (Tier 4). Furthermore, instream elements which are not shaped by the deposition and erosion of sediments are mapped as structural elements separately from geomorphic units (e.g. logs, boulders, vegetation and man-made structures). The advantages of this scheme are that, 1.) after in-channel regions are identified at Tier 1, the delineation channel units, such as the extent of bars, is flow independent, and 2.) geomorphic units can be examined in relation to the spatial distribution of structural elements.   At this time, we have not incorporated Tier 4 patch attributes such as vegetation and grain size, but a workflow could be easily added that uses the output from Tier 3 along with additional patch characteristic input file to create patch level geomorphic units.  

####Geomorphic Unit System (GUS)

GUS was developed independently, but around the same time as the Wheaton taxonomy and has many similarities, but rather than focusing on deriving units from topography, it focuses on first classifying units from satellite and aerial imagery [(Belletti et al., 2015)](http://www.reformrivers.eu/characterising-physical-habitats-and-fluvial-hydromorphology-new-system-survey-and-classification]). Once a region is mapped at the macro level, it is visited and mapped in finer detail at a unit or subunit scale based on identifying characteristics such as hydraulic conditions and process of formation. Units and subunits are identified using a guidebook of all possible units and subunits within each macro unit  [(Rinaldi et al., 2015)](http://www.reformrivers.eu/system/files/6.2%20Methods%20to%20assess%20hydromorphology%20of%20rivers%20part%20III%20revised_0.pdf). This approach is flow dependent rather than independent, which is advantageous exploring questions relating flow to geomorphic units (GU).  

 ####Topographic Form Classification

GUT includes a new topographic form attribute classification scheme at the Tier 2 level ([Bangen et al, 2017;]({{site.baseurl}}/assets/images/hr/Bangen_AGUPoster_2017.png) Bangen et al., in prep) that segments regions of similar contour signatures as bowls, mounds, planes, troughs and walls (Figure 2).   During development, we discovered that these forms were needed to better segment topography prior to unit designation at the Tier 3 level.  Because the boundaries between these forms are inherently fuzzy, we also output a Tier 2 transitions shapefile which includes bowl transitions and mound transitions.  Boundaries are placed based on user-defined thresholds set in the configure file.  Analysis of transition zones can be conducted by adjusting these dials and comparing output. 

[![shapeContour]({{site.baseurl}}(/assets/images/shapeContour.png)]({{site.baseurl}}/assets/images/hr/shapeContour.png)
Figure 2. Cartoon of Tier 2 forms.


### References:
Bangen SG, Kramer N, Wheaton, JM, and Bouwes N. 2017. The GUTs of the Geomorphic Unit Tool: What is under the hood. EP31D-1901. AGU. New Orleans, LA, 11-15 Dec. 

Bangen SG, Kramer N, Wheaton JM, and Bouwes N. In Preparation. Mapping instream geomorphic units from high resolution topography. 

Belletti, B. et al., 2017. Characterising physical habitats and fluvial hydromorphology: A new system for the survey and classification of river geomorphic units. Geomorphology, 283, pp.143–157.

Rinaldi, M. et al., 2015. The geomorphic units survey and classification system (GUS), Deliverable 6.2, Part 4. In Deliverable 6.2, Final Report on the methods, models, tools to assess the hydromorphology of rivers. Available at: http://www.reformrivers.eu/system/files/6.2%20Methods%20to%20assess%20hydromorphology%20of%20rivers%20part%20IV%20revised.pdf.

Wheaton, J.M. et al., 2015. Geomorphic mapping and taxonomy of fluvial landforms. Geomorphology, 248, pp.273–295.



