---
title: Supporting Tools
---
We provide several scripts that you can use to help prepare, manage and use GUT data.  These have been developed by users.  If you have any improvements or your own scripts that could be of use to the community to share please contact us and we can link to them here.

# R Tools

## GU_Summary Toolkit
The GU_Summary Tool Package will summarize your GUT output geometry quickly for one or multiple runs. [Video Tutorial](https://youtu.be/lSQjCs54Fjc.). [The toolkit](https://github.com/Riverscapes/pyGUT/tree/master/SupportingTools/Rscripts/GU_Summary) can be downloaded from GitHub with [Example data](https://github.com/Riverscapes/pyGUT/blob/master/ExampleData.zip).

### The Toolkit consists of:

- [*makeGUTmaps.R*](https://github.com/Riverscapes/pyGUT/blob/master/SupportingTools/Rscripts/GU_Summary/makeGUTmaps.R) creates simples maps of the geometry. [video tutorial](https://youtu.be/S1eeWStImko). 
 
<iframe width="560" height="315" src="https://www.youtube.com/embed/S1eeWStImko" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

- [*makeGUmetrics.R*](https://github.com/Riverscapes/pyGUT/blob/master/SupportingTools/Rscripts/GU_Summary/makeGUmetrics.R) Creates a summary of your GU categories by site visit.

- [*makesitemetrics.R*](https://github.com/Riverscapes/pyGUT/blob/master/SupportingTools/Rscripts/GU_Summary/makesitemetrics.R) Creates a summary of some site complexity attributes   

- [*Compiler_ReadMe.R*](https://github.com/Riverscapes/pyGUT/blob/master/SupportingTools/Rscripts/GU_Summary/Compiler_ReadMe.R) Calls the other scripts and provides examples for batch processing of many GUT runs.


# ArcPy Tools

- [*SmoothPolygon.py*](https://github.com/Riverscapes/pyGUT/blob/master/SupportingTools/ArcPytools/SmoothPolygon.py):  smooths your output polygon edges
 	
- [*polygonMetrics.py*](https://github.com/Riverscapes/pyGUT/blob/master/SupportingTools/ArcPytools/polygonMetrics.py): Computes different metrics for output geometries

- [*mappingtool2.0_NK.py*](https://github.com/Riverscapes/pyGUT/blob/master/SupportingTools/ArcPytools/mappingtool2.0_NK.py) and [*mappingtool1.0_NK.py](https://github.com/Riverscapes/pyGUT/blob/master/SupportingTools/ArcPytools/mappingtool1.0_NK.py): Two vesions of a script for two previous verions of GUT that imports and symbolizes GUT output into an existing ArcMap.  This will need to be updated to reflect the most current version of GUT output.  It probably won't work at first.

- [*CHAMP_gdbExport_SB.py*](https://github.com/Riverscapes/pyGUT/blob/master/SupportingTools/ArcPytools/CHaMP_gdbExport_SB.py) and [*CHAMP_gdbExport_NK.py*](https://github.com/Riverscapes/pyGUT/blob/master/SupportingTools/ArcPytools/CHaMP_gdbExport_NK.py): Extracts the necessary GUT import files from batch CHaMP geodatabase and puts them into a GUT inputs folder with the correct names, etc.  This script is old and hasn't been updated in a while.  It will need to be updated to work correctly. We provide two versions that are slightly different.

