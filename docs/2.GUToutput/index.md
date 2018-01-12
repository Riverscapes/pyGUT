---
title: GUT Output
---
GUT outputs each unique geometry (e.g., Tier 1, Tier 2) as a polygon shapefile and writes them to an 'Output' folder.  These shapefiles contain categorical and numeric attribute fields (columns)  to describe each unique polygon (row).  In addition, GUT produces numerous intermediary shapefiles and rasters that are used in the model algorithms.   Several of these intermediary layers are written to a 'EvidenceLayers' folder as we find them useful for understanding the output and running subsequent analyses.

An important element of the GUT framework is the conceptualization of each tier as having **geometries** in accordance to a theme: 

- Tier 1 has **flow** related geometries
- Tier 2 has **topographic** related geometries
- Tier 3 has **geomorphic** related geometries.  

The **evidence layers** created from the user supplied inputs, the previous tier **geometry** (after Tier 1), along with the unit's **categorical and numeric attributes** are used in the GUT algorithms to derive unit names for each polygon.  

It is important to note that while tier outputs are used as evidence to derive subsequent tier outputs, the higher order tier geometries (e.g., Tier 3) are not not necessarily nested within lower tier geometries (e.g., Tier 2). The modularization of the tier output so that it doesn’t follow a strict hierarchy allows for flexible analysis and customization to suit a broad range of questions and many scales.  The geometries and associated attributes from any tier can be intersected with any other tier, allowing for a wide variety of  analyses.  For example, an analysis could be conducted using the intersection between banks (classified at Tier 3) and submergence (Tier 1 flow attribute).  

