---
title: Categorical Attributes
weight: 80
---

Here we provide a summary of categorical attributes for each output geometry. 

Categories in *italics* are currently automated by the GUT algorithms, whereas classes in normal font need to be added manually by the user.  

The categories listed are currently recognized by the GUT algorithms.  However, users could manually edit to change or include additional classes in their final maps or when editing the Tier 3 output prior to running Tier 3 subGU module if desired.  

## Tier 1: Flow Geometry

| Field Name  | Categories                   | Description                              | Adapted from                             |
| ----------- | ---------------------------- | ---------------------------------------- | ---------------------------------------- |
| Valley Unit | *In-Channel, Out-of-Channel* | In-channel versus out of channel  units within the valley bottom. | Wheaton et al. (2017)                    |
| Flow Unit   | *Submerged, Emergent, High*  | This is the geometry class for In-Channel Tier 1 output. | Rinaldi et al. (2015), Belletti  et al. (2017) |

## Tier 2: Topographic Geometry

| Field Name | Classes                                  | Description                              | Adapted from          |
| ---------- | ---------------------------------------- | ---------------------------------------- | --------------------- |
| Form       | *Mound, Mound Transition, Bowl, Bowl Transition, Plane, Wall* | Topographically defined form. This is the geometry class for In-Channel Tier 2 output. | Bangen et al. (2017)  |
| Shape      | *Concavity, Convexity, Planar*           | Topographically defined shape            | Wheaton et al. (2017) |

## Tier 3: Geomorphic Geometry

| Field Name | Classes                                  | Description                              | Adapted from                             |
| ---------- | ---------------------------------------- | ---------------------------------------- | ---------------------------------------- |
| GU         | *Bank, Margin Attached Bar,  Mid-Channel Bar, Pocket Pool, Pool, Pond, Riffle, Glide-Run,  Rapid, Cascade* | Base geomorphic units. This is the geometry class from the Tier 3 GU output. |                                          |
| subGU      | many names….                             | Specific geomorphic units.   User could enter more names than  auto-generated subGUs.  See references for exhaustive lists. This is the geometry class from the Tier 3 subGU output. | Wheaton et al. (2017), Rinaldi  et al. (2015), Friyers and Brierly (2013) |
| ThalwegCh  | *Main, Secondary, Backwater,  Tributary* | Lists which thalweg channels the  unit intersects |                                          |
| OnThalweg  | *Main, Anabranch, Braid, Cut-off,  Split, Return* | Lists which thalweg types the  unit intersects |                                          |
| Position   | *Margin Attached, Margin  Detached, Channel Spanning, Mid-Channel* | Position of unit with respect to  channel margin |                                          |
| Slope      | *Very Low, Low, Moderate, High,  Very High* | Slope                                    |                                          |
| MbendCat   | *Inside, Outside, Lateral*               | Describes whether the unit is on  the outside or inside of bends or along a straighter section of channel. |                                          |
| OrientCat  | *Longitudinal, Transverse,  Diagonal*, Radial, *NA* | Orientation with respect to  centerline  |                                          |
| Morphology | *Elongate*, Lobate, Arcuate,  Round, Oblate | Morphological shape. Categories should be edited and defined by user | Williams (2014),  Wheaton et. al., 2017  |
| ForceType  | None, Structural Element,  Geomorphic Unit, Planform, *NA* | Type of forcing element. Categories should be edited and defined by user | Wheaton et al. (2017)                    |
| ForceElem  | *NA*, Wood, Bank Hardpoint, Engineered  Structure, Boulder, Constriction, Expansion, Meander …. Etc. | Name of forcing element.  Categories should be edited and defined by user | Wheaton et al. (2017)                    |
| ForceHyd   | *Confluence*, Eddy, Plunge,  *Diffluence*, Grade Control, Complex, Shear Zone | Type of forcing hydrology. Categories should be edited and defined by user. | Wheaton et al. (2017)                    |

## Tier 4:  Patch Geometry

*** In development and not incorporated into algorithms at this time.

| Field Name | Classes                                  | Description                              | Adapted from                             |
| ---------- | ---------------------------------------- | ---------------------------------------- | ---------------------------------------- |
| Roughness  | Low, Moderate, High, Very High           | Bed roughness                            | Wheaton et al., (2015)                   |
| Sorting    | Well Sorted, Poorly Sorted,  Moderately Sorted | Characteristic sorting                   |                                          |
| Grain      | Fines, Sands, Gravels, Cobbles,  Boulders, Bedrock | Characteristic or dominant grain  size driving geomorphology and hydraulics |                                          |
| Vegetation | Aquatic, Bare, Pioneer, Riparia,  Forest | Type of vegetation                       | Wheaton et al., (2015), Rinaldi et al., (2015 ) |