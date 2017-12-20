---
title: GUT outputs
---
GUT outputs each unique geometry as a polygon shapefile.  These shapefiles contain categorical attribute and numeric attribute fields (columns)  to describe each unique polygon (row).  In addition to the output shapefiles the code will generate numerous evidence shapefiles (lines, points and polygons) and rasters that could be handy.  

1. [the output geometries]({{ site.baseurl }}/2.GUToutput/outputgeometries)
2. [categorical attributes]({{ site.baseurl }}/2.GUToutput/categoricalattributes)
3. [numeric attributes]({{ site.baseurl }}/2.GUToutput/numericattributes)
4. [evidence layers]({{ site.baseurl }}/2.GUToutput/evidencelayers)


The most important element of the  [GUT_Framework]({{site.baseurl}}/assets/images/hr/GUT_Framework.png)  is the conceptualization of each tier as having [geometries]({{site.baseurl}}/docs/2.GUToutput/outputgeometries) in accordance to a theme: tier 1 has flow related geometries, tier 2 has topographic related geometries, tier 3 has geomorphic related geometries.  For each geometry, previous tier geometry, [categorical]({{site.baseurl}}/docs/2.GUToutput/categoricalattributes) and   [numeric]({{site.baseurl}}/docs/2.GUToutput/numericattributes) attributes, and [evidence layers]({{site.baseurl}}/docs/GUToutput/evidencelayers) created from user supplied [inputs]({{site.baseurl}}/docs/1.RunningGUT/inputs) are utilized by the [tool's algorithms]({{site.baseurl}}/docs/4.guDescriptions/index.md) to derive unit names. 

It is important to note that tier outputs are used as evidence to derive subsequent tier outputs but that higher order tier geometries are not not necessarily nested within lower tier geometries. The modularization of the Tier output so that it doesn’t follow a strict hierarchy allows for flexible analysis and customization to suit a broad range of questions and many scales.  The geometries and associated attributes from any tier can be intersected with any other tier, making a wide variety of  [applications]({{site.baseurl}}/docs/Applications/index.md) possible.  For example, an analysis could be conducted using the intersection between banks (geomorphic name from Tier 3) and submergence (flow attribute from Tier 1).  

