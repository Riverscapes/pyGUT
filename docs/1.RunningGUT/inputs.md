---
title: User Inputs
weight: 1
---

This page describes the user inputs needed to run GUT.  In the future, we plan to develop additional scripts to support generating these inputs (with the exception of the DEM).  In the meantime, these inputs can either be digitized or generated using existing software such as the [River Bahtymetry Toolkit (RBT)](https://essa.com/explore-essa/tools/river-bathymetry-toolkit-rbt/).  


## Digital Elevation Model (DEM) Raster

Since this is a topographic dependent mapping tool, it requires a DEM to run.   

#### Resolution

The resolution of the input DEM is up to the user.  However, if you provide a 10 m resolution DEM do not expect to be able to pull out landforms that are smaller than about 100 m in width (since each pixel is 10 m wide you need at least a few pixels to be able to define a landform).  The tool was developed on DEMs created from total station surveys of wadeable stream reaches (2 to 60 m wide) with 10 cm resolution.  That being said, the tool should work equally well on DEMs of varying resolution derived from data collected using other survey technologies (e.g., LiDAR, SEM). There is an option when you run the tool to specify the minimum unit size so if you input a very high resolution DEM you can produce maps that are more generalized.

#### Smoothing

The DEM should be filtered and smoothed to some extent to avoid anomalous high and low points due to data gaps and errors.  However, if you smooth too much you may start loosing nuances in the topography, resulting in more generalized and larger geomorphic units.  Keep in mind that the quality of the output maps will be directly related to the quality of the DEM input.

#### Detrending

The tool will work equally well on detrended or non-detrended DEMs.  However, detrending may change output classifications, especially for steeper stream segments. 

## Bankfull and Low Flow Water Extent Polygons

The tool relies on the user provide to the bankfull and low flow water extent boundaries as two separate polygon shapefiles. The bankfull extent is used to determine the boundary for the in-channel and out-of-channel and flow unit mapping in Tier 1.  The low flow water extent is also used during the Tier 2 and Tier 3 mapping.

## Bankfull Centerline Polyline(s)

This is an input polyline shapefile that is simply line(s) drawn through the center of the bankfull polygon.  Where multiple channels exist, the centerline should split into two or more lines.  The bankfull centerline(s) are used to determine average bankfull width of the channel, which is in turn used as a scalar for size thresholding during unit delineation.  The bankfull centerline is also used as the reference when calculating the orientation of units.

## Thalweg Polyline(s)

For the in-channel mapping to run successfully, a user must provide a thalweg polyline shapefile.  The thalweg is a line connecting the lowest points along the entire length of the streambed and represents the dominant flowpath of each channel. The thalweg lines(s) input is used to map Tier 2 saddles and Tier 3 riffles.  If the thaweg is not appropriately placed the algorithms may falsely identify or miss saddles and riffles. 

In order to identify saddles not just along the main thalweg, you have the option of supplying an input thalweg layer that includes, not just the main thalweg, but thalwegs associated with secondary flow paths.  These secondary thalweg paths are also used to name sub GUs at the Tier 3 level (e.g., cut-off chutes, diagonal bars, confluence pools, backwater ponds).  For the algorithms to use the multiple thalwegs to full advantage, you should have two fields for each thalweg segment `Channel` and `ThalwegTyp` and each segment should be categorized following the scheme below. The algorithm will run whether or not you have attributed all your thalwegs, it just might not name all the Tier 3 subGUs correctly.  

#### `Channel`
* **Main** - The bankfull channel through which the thalweg that follows the deepest path is within
* **Secondary** - A channel separated from the main channel at bankfull by an island that is not flooded. 
* **Tributary** - A channel confluencing with the secondary or main channel that has an upstream catchement.
* **Backwater** - A channel that is returning to a main or secondary channel from the floodplain.  These channels often reconnect abandoned channels and backwater pools with the hydrology of the main channel. They differ from Tributaries in that the source of their is from the floodplain rather than an upstream drainage network.

#### `ThalwegTyp`
* **Main** - The thalweg within the bankfull channel that follows the deepest path.
* **Anabranch** - The main thalweg of secondary channels.
* **Return**- Thalwegs returning flow from floodplain or backwater areas.
* **Cut-off** - Thalwegs within smaller chute like channels that cut across depostional features.  These typically depart and return from another thalweg and are often on the outside of bends cutting across diagonal and compound bars.
* **Braid** - Thalwegs that cut across bar features and connect two different larger thalwegs. 
* **Split** - Thalwegs that split from another thalweg and then return without cutting through depositional features.  Split flow often forms around boulders, steps and other structural elements in the channel.

See an example of how we classify thalwegs here:
<iframe width="560" height="315" src="https://www.youtube.com/embed/7AXaTnMN_lk" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>

**Important:** When delineating your thalwegs, make sure that they typology is correct.  The line segments should be directional in the direction of downstream and all confluences and diffluences should share a node. Currently the code will not be able to extract saddles/riffles that have a confluence or diffluence on top of them so if you think you have an area that should be called a saddle/riffle, make sure you are not starting or ending any thalweg segment within its bounds. 
