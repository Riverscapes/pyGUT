---
title: User Inputs
---

[![GUTLogo]({{site.baseurl}}/assets/images/GUTLogo.png)]({{site.baseurl}}/assets/images/Large/GUTLogo.png)

This describes user inputs needed to run GUT.  


## Digital Elevation Model (DEM) Raster

Since this is a topographic dependent mapping tool, it requires a DEM to run.   

### Resolution

The resolution of the input DEM should match the resolution of the units that you wish to extract.  For example, if you provide a 10m resolution DEM, do not expect to be able to pull out landforms that are smaller than about 100 m in width since each pixel is 10m wide and you need at least a few pixels to be able to define a landform.   The tool was developed on DEMs created from total station surveys of channel reaches with about 10 cm resolution but should work equally well on DEMs created in a variety of ways (from LiDAR, SEM, etc.). There is an option when you run the tool to specify the minimum unit size so if you feed it a DEM with very high resolution you can produce maps that are more generalized.

### Smoothing

The DEM should be filtered and smoothed to some extent to avoid anomalous high and low points due to data gaps and errors.  However, if you smooth too much you may start loosing nuances in the topography, resulting in more generalized and larger geomorphic units.  Keep in mind that the quality of the output maps will be directly related to the quality of the DEM input.

### Detrending

The tool will work equally well on detrended or non-detrended input DEMs.  However, detrending may change output classifications, especially for steeper stream segments.  A Detrended DEM is provided as an output Evidence Layer (see here for more details)

## Bankfull and Low Flow Water Extent Polygons

The tool relies on the user deciding where the bankfull and low flow water extent boundaries are.  The extents need to be provided in two separate shapefiles. The Bankfull is used to determine the boundaries for the in-channel versus out of channel mapping shemes and are combined to create Tier 1 output.  The low flow water extent is used during the Tier 3 mapping to help split units.  These boundaries can be created by hand digitizing polygons or based on bankfull flooded extents generated from hydraulic model results.

## Bankfull Centerline

This is an input line layer that is simply line(s) drawn through the center of the bankfull polygon.  Where multiple channels exist, the centerline splits into two or more lines.  The bankfull centerlines are used to determine average bankfull width of the channel, which is in turn used as a scalar for size thresholding during unit delimination.  The bankfull centerline is also used as the reference base when calculating the orientation of units.

## Thalweg Lines

For the In-Channel mapping to run successfully, a user must provide a thalweg, a line connecting the lowest points of successive cross-sections along the course of a valley or river. The thalweg line is used to pull out Tier 2 saddle forms and riffles.  If the thaweg is not appropriately placed, then the algorithms may falsly identify or miss saddles and riffles.  See here for an explanation of how saddles are extracted.

In order for a user to be able to identify saddles not along the main thalweg, you have the option of supplying an input thalweg layer that includes, not just the main thalweg, but thalwegs associated with secondary flow paths.  These secondary thalweg paths are used to identify riffles not along the main flow, and sub Geomorphic Units at the Tier 3 level such as cut-off chutes, diagonal bars, confluence pools, backwater ponds, etc.  For the algorithms to use the multiple thalwegs to full advantage, you should have two fields for each thalweg segment **'Channel'** and **'ThalwegTyp'** and each segment should be categorized following the scheme below. However, the algorithm will run whether or not you have attributed all your thalwegs, it just might not pull out all the Tier 3 subGU units.

#### Channel
* **Main** - The bankfull channel through which the thalweg that follows the deepest path is within
* **Secondary** - A channel separated from the main channel at bankfull by an island that is not flooded. 
* **Tributary** - A channel confluencing with the secondary or main channel that has an upstream catchement.
* **Backwater**- A channel that is returning to a main or secondary channel from the floodplain.  These channels often reconnect abandoned channels and backwater pools with the hydrology of the main channel. They differ from Tributaries in that the source of their is from the floodplain rather than an upstream drainage network.

#### ThalwegTyp

* **Main**- The thalweg within the bankful channel that follows the deepest path.
* **Anabranch**- The main thalweg of secondary channels.
* **Return**- Thalwegs returning flow from floodplain or backwater areas.
* **Cut-off**- Thalwegs within smaller chute like channels that cut across depostional features.  These typically depart and return from another thalweg and are often on the outside of bends cutting across diagonal and compound bars.
* **Braid**- Thalwegs that cut across bar features and connect two different larger thalwegs. 
* **Split**- Thalwegs that split from another thalweg and then return without cutting through depositional features.  Split flow often forms around boulders, steps and other structural elements in the channel.