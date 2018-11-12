---
title: Supporting Tools
---
We provide several scripts that you can use to help prepare, manage and use GUT data.  These have been developed by users.  If you have any improvements or your own scripts that could be of use to the community to share please contact us and we can link to them here.

#R Tools

##GU_Summary Toolkit
The GU_Summary Tool Package will summarize your GUT output geometry quickly for multiple runs. A video Tutorial is here: https://youtu.be/lSQjCs54Fjc.  The toolkit can produce:

-[*makeGUTmaps.R*](https://github.com/Riverscapes/pyGUT/blob/master/SupportingTools/Rscripts/GU_Summary/makeGUTmaps.R) creates simples maps of the geometry and can batch run for large numbers of GUT output.  [video tutorial](https://youtu.be/S1eeWStImko)(https://github.com/Riverscapes/pyGUT/blob/master/SupportingTools/Rscripts/GU_Summary/makeGUTmaps.R) 
 
<iframe width="560" height="315" src="https://www.youtube.com/embed/S1eeWStImko" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

-[*makeGUmetrics.R*](https://github.com/Riverscapes/pyGUT/blob/master/SupportingTools/Rscripts/GU_Summary/makeGUmetrics.R) Creates a summary of your GU categories by site visit

-[*makesitemetrics.R*](https://github.com/Riverscapes/pyGUT/blob/master/SupportingTools/Rscripts/GU_Summary/makesitemetrics.R) Creates a summary of some site complexity attributes   

-[*Compiler_ReadMe.R*](https://github.com/Riverscapes/pyGUT/blob/master/SupportingTools/Rscripts/GU_Summary/Compiler_ReadMe.R) Calls the other scripts and provides examples for batch processing of many GUT run.

The toolkit can be downloaded from GitHub. https://github.com/Riverscapes/pyGUT/tree/master/SupportingTools/Rscripts/GU_Summary

Example data can be downloaded from GitHub. https://github.com/Riverscapes/pyGUT/blob/master/ExampleData.zip



#ArcPy Tools

*SmoothPolygon.py*:  will smooth your output polygon edges
 	
*polygonMetrics.py*: Computes different metrics for output geometries

*mappingtool.py*: Imports and symbolized GUT output into existing ArcMap.  This will need to be updated to reflect the most current version of GUT output.  It probably won't work at first.

*CHAMP_gdbExport.py*: Extracts the necessary GUT import files from batch CHaMP geodatabase and puts them into a GUT inputs folder with the correct names, etc.  This script is old and hasn't been updated in a while.  It will need to be updated  to work correctly.

