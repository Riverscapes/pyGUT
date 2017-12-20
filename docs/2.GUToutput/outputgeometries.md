---
title: GUT outputs
---


##Geometries

Currently, GUT outputs several shapefiles and each has unique geometries.

### Tier1_InChannel.shp

A shapefile where each geometry represents a flow unit.  This layer is derived from user supplied bankfull and low flow water extent polygon ([Tier 1  descripton]({{ site.baseurl }}/4.guDescriptions/Tier1)). 

Each geometry is categorized  as:
#### Flow Unit Categories
- **high**
- **emergent**
- **submerged**

### Tier2_InChannel.shp

A shapefile where each geometry represents a form unit derived from topography.. Figure 1 illustrates these form units relate to contour signatures. Full definitions and description for how these are derived: ([Tier 2 descripton]({{ site.baseurl }}/4.guDescriptions/Tier2)) 

[![shapeContour]({{site.baseurl}}(/assets/images/shapeContour.png)](/assets/images/hr/shapeContour.png)
Figure 2. Cartoon of Tier 2 forms.

Each geometry is categorized  as:
#### Unit Form Categories

#####Predominantly convex
- Mound
- Mound Transition
- Saddle
#####Predominantly planar
- Wall
- Plane 
- Trough
#####Predominantly concave
- Bowl Transition
- Bowl

### Tier2_InChannel_discrete.shp
A shapefile where each geometry represents a form unit, but transitions (Mound Transitions and Bowl Transitions) are excluded from the output giving a more discrete look. ([Tier 2 descripton]({{ site.baseurl }}/4.guDescriptions/Tier2)) 

### Tier3_InChannel_GU.shp
A shapefile of major geomorphic units requiring minimal to no user editing to obtain decent maps. These units are created and named by using Tier2_InChannel output as well as derived evidence layers and numeric attributes.  Full definitions used in the algorithms and description of workflows can be viewed here: ([Tier 3  descripton]({{ site.baseurl }}/4.guDescriptions/Tier3)). In the configure file, minimum size thresholds can be set for different sets of units.  

*Units  in italics are under development and are not currently included in the workflows.*

#####Predominantly convex
- Margin Attached Bar
- Mid-Channel Bar
- Riffle
#####Predominantly planar
- Glide-Run
- Rapid 
- Cascade
- Transition
- Bank
- *Step*
#####Predominantly concave
- Pocket Pool
- Pond
- Pool
- Chute

This is an editable output.  The algorithms will take a first guess at where the boundaries for these units are and what they should be named based on limited evidence.  Although the output is reasonable, we expect a user to QaQc the output and edit unit names to match onsite knowledge.  

Generally accepted geomorphic definitions for in-channel geomorphic unts can be found in Brierly and Fryirs (2013), Rinaldi et al. (2015) and Wheaton et al. (2015).  The definitions GUT uses in the algorithms be reviewed here: ([Tier 3  descripton]({{ site.baseurl }}/guDescriptions/Tier3)).  

### Tier3_InChannel_GU_raw.shp
This is the same output as Tier3_InChannel_GU.shp, but it is not editable.  It preserves the original raw output.

### Tier3_InChannel_subGU.shp
This shapefile further categorizes geomorphic units with more specific names. For best results a user should edit the attributes and geometries of the Tier3_InChannel_GU.shp layer prior to running the code to produce the subGU output. This is because it uses the Tier 3 GU output as a starting point before running through some decision trees, so if a mistake was made at the GU level, the tool will not be looking in the correct place to name the subunit ([Tier 3 SubGU descripton]({{ site.baseurl }}/4.guDescriptions/Tier3Sub)).   

Below is  the selection of  Tier3 subGU units that the tool has logic to define  ([Tier 3 SubGU descripton]({{ site.baseurl }}/4.guDescriptions/Tier3Sub)). We recognize that this is not an exhaustive list and we are missing units of geomorphic interest.  Currently the output at this level of detail is still in being developed. You are fully welcome to edit your final maps to suit your own mapping needs. 



*Sub units identified in italics are under development and are not currently included in the workflows.* 

**Sub units in bold depend on user editing of the attributes**

####Types of Banks
Bank, *Cutbank*
####Types of Margin Attached Bars
Bar, Diagonal Bar, Lateral Bar, 
####Types of Mid Channel Bars
Longitudinal Bar, Island Bar, Diagonal Bar, Compound Bar, **Lobate Bar**
####Types of Pools
Pool, Confluence Pool, Meander Pool, **Plunge Pool**
####Types of Ponds
Pond, Backwater Pond, *Beaver Pond*
####Types of Transitions
Transition,*Barface, Bench* 
####Types Chutes
Cut-off Chute, Chute, Shallow Thalweg
####*Types of Steps*  (steps not currently included.)
*Wood-forced Step, Boulder forced step, Step, Waterfall*
####Types of Glide-Runs
Glide-Run,*Glide, Run*
####Units without Sub Units
Rapid, Cascade, Pocket Pool



