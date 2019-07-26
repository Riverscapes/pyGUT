

visit.dir = "C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/VISIT_1029"
layer="Tier2_InChannel_Transition"
group.field = "UnitForm"
gut.run = "GUT_2.1/Run_01"
check = make.unit.fish.metrics(visit.dir, layer = layer, group.field = group.field)


#' Title
#'
#' @param visit.dir 
#'
#' @return
#' @export
#'
#' @examples
make.unit.fish.metrics = function(visit.dir, layer = "Tier2_InChannel_Transition", group.field = NA){
  
  # print visit dir for script progress tracking
  print(visit.dir)
  
  # get visit id from visit directory
  visit.id = as.numeric(unlist(str_split(visit.dir, "VISIT_"))[2])
  
  # # set group field as alias to work with dplyr functions
  # group.alias = !!as.name(group.field)
  # group.alias = get(group.field)
  # var <- c('cyl')
  # mtcars %>% filter(get(var) == 4)
  
  # extent ---------------------------
  # used to clip gut units
  
  # if delft extent shp exists use that otherwise use fuzzy model extent shp
  # if neither exist then extent is set to na
  delft.extent.file = unlist(list.files(path = visit.dir, pattern = "^Delft_Extent.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  fuzzy.extent.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_Chinook_Extent.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  
  if(length(delft.extent.file > 0)){
    extent.shp = st_read(delft.extent.file, quiet = TRUE)
  }else if(length(fuzzy.extent.file > 0)){
    extent.shp = st_read(fuzzy.extent.file, quiet = TRUE)
  }else{
    extent.shp = NA
  }
  
  # gut units ---------------------------

  # read in units shp
  units.files = unlist(list.files(path = visit.dir, pattern = paste("^", layer, ".shp$", sep = ""), full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  units.file = grep(gut.run, units.files, value = TRUE)
  units.shp = check.shp(units.file)
  
  # if gut units don't exist then return tibble with just visit.id
  if(!"sf" %in% class(units.shp)){
    out.metrics = tibble(visit.id = visit.id)
    return(out.metrics)
  }
  
  # clip units to extent shp and calculate new area field (Area.Delft)
  if("sf" %in% class(extent.shp)){
    units.shp = units.shp %>% 
      st_crop(extent.shp) %>%
      mutate(area.delft = st_area(.) %>% as.numeric() %>% round(3))
  }
  
  # create tibble with just group field and extent area to append metrics to
  if("sf" %in% class(extent.shp)){
    tb.metrics = units.shp %>%
      st_drop_geometry() %>%
      dplyr::select(!!as.name(group.field), area.delft) %>%
      group_by(!!as.name(group.field)) %>%
      summarize(area.delft = sum(area.delft)) %>%
      ungroup()
  }else{
    tb.metrics = units.shp %>%
      st_drop_geometry() %>%
      dplyr::select(!!as.name(group.field)) %>%
      mutate(area.delft = NA) %>%
      group_by(!!as.name(group.field)) %>%
      summarize(area.delft = sum(area.delft)) %>%
      ungroup()
  }

  # create reference tibbles with just group field and suitable categories
  tb.units = tb.metrics %>% dplyr::select(!!as.name(group.field))
  tb.cats = tibble(category = c("suitable"))
  tb.units.cats = crossing(tb.units, tb.cats)

  
  # nrei ---------------------------
  
  # read in suitable shp
  nrei.suit.file = unlist(list.files(path = visit.dir, pattern = "^NREI_Suitable_Poly.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  nrei.suit.shp = check.shp(nrei.suit.file)
  
  # # convert from multipolygon to polygon
  # if(!anyNA(nrei.suit.shp)){nrei.suit.shp = nrei.suit.shp %>% st_cast("POLYGON")}

  # intersect suitable shp with clipped gut units (as long as both shps are sf objects) and calculate new area field (Area.Hab)
  if("sf" %in% class(nrei.suit.shp)){
    units.nrei.suit = units.shp %>%
      st_intersection(nrei.suit.shp) 
  }else{
    units.nrei.suit = NA
  }
  
  # read in predicted fish locations shp
  nrei.locs.file = unlist(list.files(path = visit.dir, pattern = "^NREI_FishLocs.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  nrei.locs.shp = check.shp(nrei.locs.file)
  
  # join predicted fish locations shp with units and suitable shp (as long as shps are sf objects)
  nrei.locs.shp = join.shp(nrei.locs.shp, nrei.suit.shp, in.units = units.shp)
  
  # read in nrei all points shp
  nrei.all.file = unlist(list.files(path = visit.dir, pattern = "^NREI_All_Pts.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  nrei.all.shp = check.shp(nrei.all.file)
  
  # join points shp with units and suitable shp (as long as shps are sf objects)
  nrei.all.shp = join.shp(nrei.all.shp, nrei.suit.shp, in.units = units.shp)
  
  # --calculate summary metrics--
  
  # if all points isn't an sf object (i.e., it doesn't exist) assume that nrei model run doesn't exist for visit populate metrics as NA
  # otherwise calculate metrics
  if(!"sf" %in% class(nrei.all.shp)){
    nrei.metrics.wide = tb.metrics %>%
      mutate(model = "nrei", species = "steelhead", lifestage = "juvenile",
             hab.area.suitable = NA, pred.fish = NA, pred.fish.suitable = NA, 
             med = NA, mean = NA, sd = NA, med.suitable = NA, mean.suitable = NA, sd.suitable = NA)
  }else{
    # create tibble to store metrics
    nrei.metrics = tibble()
    
    # area for units and nrei suitable intersections
    nrei.metrics = nrei.metrics %>% 
      bind_rows(., calc.unit.area(units.nrei.suit, by.suit = TRUE) %>% mutate(var = "hab.area"))
    
    # capacity by group field
    nrei.metrics = nrei.metrics %>% 
      bind_rows(., calc.unit.capacity(nrei.locs.shp, by.suit = FALSE) %>% mutate(var = "pred.fish"))
    
    # capacity by group field and suitability category
    nrei.metrics = nrei.metrics %>% 
      bind_rows(., calc.unit.capacity(nrei.locs.shp, by.suit = TRUE) %>% mutate(var = "pred.fish"))
    
    # model values by group field
    nrei.metrics = nrei.metrics %>% 
      bind_rows(., calc.unit.stats(nrei.all.shp, in.field = "nre_Jph", by.suit = FALSE))
    
    # model values by group field and suitability category
    nrei.metrics = nrei.metrics %>% 
      bind_rows(., calc.unit.stats(nrei.all.shp, in.field = "nre_Jph", by.suit = TRUE))
    
    # convert to wide form tibble
    nrei.metrics.wide = nrei.metrics %>%
      unite("variable", c("var", "category"), sep = ".", remove = TRUE) %>%
      mutate(variable = str_replace_all(variable, ".NA", "")) %>%
      spread(variable, value) %>% 
      mutate(model = "nrei", species = "steelhead", lifestage = "juvenile") %>%
      left_join(tb.metrics, by = group.field)
  }

  
  # fuzzy chinook spawner ---------------------------
  
  # read in suitable shp
  ch.suit.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_Suitable_Poly_Chinook.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  ch.suit.shp = check.shp(ch.suit.file)
  
  # intersect suitable shp with clipped gut units (as long as both shps are sf objects) and calculate new area field (Area.Hab)
  if("sf" %in% class(ch.suit.shp)){
    units.ch.suit = units.shp %>%
      st_intersection(ch.suit.shp) 
  }else{
    units.ch.suit = NA
  }
  
  # read in predicted redd locations shp
  ch.redds.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_ReddLocs_Chinook.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  ch.redds.shp = check.shp(ch.redds.file)
  
  # join predicted fish locations shp with units and suitable shp (as long as shps are sf objects)
  ch.redds.shp = join.shp(ch.redds.shp, ch.suit.shp, in.units = units.shp)
  
  # read in fuzzy raster and convert to points
  ch.raster.file = unlist(list.files(path = visit.dir, pattern = "^FuzzyChinookSpawner_DVSC.tif$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(length(ch.raster.file) > 0){
    ch.raster = read_stars(ch.raster.file, quiet = TRUE) %>% st_transform(crs = (st_crs(units.shp)), partial = FALSE)
    ch.all.shp = st_as_sf(ch.raster, as_points = TRUE) %>% st_transform(crs = (st_crs(units.shp)), partial = FALSE) %>%
      rename(ras.value = FuzzyChinookSpawner_DVSC.tif)
  }else{
    ch.all.shp = NA
  }
  
  # join points shp with units and suitable shp (as long as shps are sf objects)
  ch.all.shp = join.shp(ch.all.shp, ch.suit.shp, in.units = units.shp)
  
  # --calculate summary metrics--
  
  # if all points isn't an sf object (i.e., it doesn't exist) assume that fuzzy model run doesn't exist for visit populate metrics as NA
  # otherwise calculate metrics
  if(!"sf" %in% class(ch.all.shp)){
    ch.metrics.wide = tb.metrics %>%
      mutate(model = "fuzzy", species = "chinook", lifestage = "spawner",
             hab.area.suitable = NA, pred.fish = NA, pred.fish.suitable = NA, 
             med = NA, mean = NA, sd = NA, med.suitable = NA, mean.suitable = NA, sd.suitable = NA)
  }else{
    # create tibble to store metrics
    ch.metrics = tibble()
    
    # area for units and chinook suitable intersections
    ch.metrics = ch.metrics %>% 
      bind_rows(., calc.unit.area(units.ch.suit, by.suit = TRUE) %>% mutate(var = "hab.area"))
    
    # capacity by group field
    ch.metrics = ch.metrics %>% 
      bind_rows(., calc.unit.capacity(ch.redds.shp, by.suit = FALSE) %>% mutate(var = "pred.fish"))
    
    # capacity by group field and suitability category
    ch.metrics = ch.metrics %>% 
      bind_rows(., calc.unit.capacity(ch.redds.shp, by.suit = TRUE) %>% mutate(var = "pred.fish"))
    
    # model values by group field
    ch.metrics = ch.metrics %>% 
      bind_rows(., calc.unit.stats(ch.all.shp, in.field = "ras.value", by.suit = FALSE))
    
    # model values by group field and suitability category
    ch.metrics = ch.metrics %>% 
      bind_rows(., calc.unit.stats(ch.all.shp, in.field = "ras.value", by.suit = TRUE))
    
    # convert to wide form tibble
    ch.metrics.wide = ch.metrics %>%
      unite("variable", c("var", "category"), sep = ".", remove = TRUE) %>%
      mutate(variable = str_replace_all(variable, ".NA", "")) %>%
      spread(variable, value) %>% 
      mutate(model = "fuzzy", species = "chinook", lifestage = "spawner") %>%
      left_join(tb.metrics, by = group.field)
  }
  
  # fuzzy steelhead spawner ---------------------------
  
  # read in suitable shp
  st.suit.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_Suitable_Poly_Steelhead.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  st.suit.shp = check.shp(st.suit.file)
  
  # intersect suitable shp with clipped gut units (as long as both shps are sf objects) and calculate new area field (Area.Hab)
  if("sf" %in% class(st.suit.shp)){
    units.st.suit = units.shp %>%
      st_intersection(st.suit.shp) 
  }else{
    units.st.suit = NA
  }
  
  # read in predicted redd locations shp
  st.redds.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_ReddLocs_Steelhead.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  st.redds.shp = check.shp(st.redds.file)
  
  # join predicted fish locations shp with units and suitable shp (as long as shps are sf objects)
  st.redds.shp = join.shp(st.redds.shp, st.suit.shp, in.units = units.shp)
  
  # read in fuzzy raster and convert to points
  st.raster.file = unlist(list.files(path = visit.dir, pattern = "^FuzzySteelheadSpawner_DVSC.tif$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(all(length(st.raster.file) > 0, "sf" %in% class(units.shp))){
    st.raster = read_stars(st.raster.file, quiet = TRUE) %>% st_transform(crs = (st_crs(units.shp)), partial = FALSE)
    st.all.shp = st_as_sf(st.raster, as_points = TRUE) %>% st_transform(crs = (st_crs(units.shp)), partial = FALSE) %>%
      rename(ras.value = FuzzySteelheadSpawner_DVSC.tif)
  }else{
    st.all.shp = NA
  }
  
  # join points shp with units and suitable shp (as long as shps are sf objects)
  st.all.shp = join.shp(st.all.shp, st.suit.shp, in.units = units.shp)
  
  # --calculate summary metrics--
  
  # if all points isn't an sf object (i.e., it doesn't exist) assume that fuzzy model run doesn't exist for visit populate metrics as NA
  # otherwise calculate metrics
  if(!"sf" %in% class(st.all.shp)){
    st.metrics.wide = tb.metrics %>%
      mutate(model = "fuzzy", species = "steelhead", lifestage = "spawner",
             hab.area.suitable = NA, pred.fish = NA, pred.fish.suitable = NA, 
             med = NA, mean = NA, sd = NA, med.suitable = NA, mean.suitable = NA, sd.suitable = NA)
  }else{
    # create tibble to store metrics
    st.metrics = tibble()
    
    # area for units and steelhead suitable intersections
    st.metrics = st.metrics %>% 
      bind_rows(., calc.unit.area(units.st.suit, by.suit = TRUE) %>% mutate(var = "hab.area"))
    
    # capacity by group field
    st.metrics = st.metrics %>% 
      bind_rows(., calc.unit.capacity(st.redds.shp, by.suit = FALSE) %>% mutate(var = "pred.fish"))
    
    # capacity by group field and suitability category
    st.metrics = st.metrics %>% 
      bind_rows(., calc.unit.capacity(st.redds.shp, by.suit = TRUE) %>% mutate(var = "pred.fish"))
    
    # model values by group field
    st.metrics = st.metrics %>% 
      bind_rows(., calc.unit.stats(st.all.shp, in.field = "ras.value", by.suit = FALSE))
    
    # model values by group field and suitability category
    st.metrics = st.metrics %>% 
      bind_rows(., calc.unit.stats(st.all.shp, in.field = "ras.value", by.suit = TRUE))
    
    # convert to wide form tibble
    st.metrics.wide = st.metrics %>%
      unite("variable", c("var", "category"), sep = ".", remove = TRUE) %>%
      mutate(variable = str_replace_all(variable, ".NA", "")) %>%
      spread(variable, value) %>% 
      mutate(model = "fuzzy", species = "steelhead", lifestage = "spawner") %>%
      left_join(tb.metrics, by = group.field)
  }
  
  # fuzzy chinook juvenile ---------------------------
  
  # read in suitable shp
  ch.juv.suit.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_Suitable_Poly_ChinookJuvenile.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  ch.juv.suit.shp = check.shp(ch.juv.suit.file)
  
  # intersect suitable shp with clipped gut units (as long as both shps are sf objects) and calculate new area field (Area.Hab)
  if("sf" %in% class(ch.juv.suit.shp)){
    units.ch.juv.suit = units.shp %>%
      st_intersection(ch.juv.suit.shp) 
  }else{
    units.ch.juv.suit = NA
  }
  
  # read in predicted redd locations shp
  ch.locs.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_JuvenileLocs_Chinook.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  ch.locs.shp = check.shp(ch.locs.file)
  
  # join predicted fish locations shp with units and suitable shp (as long as shps are sf objects)
  ch.locs.shp = join.shp(ch.locs.shp, ch.juv.suit.shp, in.units = units.shp)
  
  # read in fuzzy raster and convert to points
  ch.juv.raster.file = unlist(list.files(path = visit.dir, pattern = "^FuzzyChinookJuvenile_DVS.tif$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(length(ch.juv.raster.file) > 0){
    ch.juv.raster = read_stars(ch.juv.raster.file, quiet = TRUE) %>% st_transform(crs = (st_crs(units.shp)), partial = FALSE)
    ch.juv.all.shp = st_as_sf(ch.juv.raster, as_points = TRUE) %>% st_transform(crs = (st_crs(units.shp)), partial = FALSE) %>%
      rename(ras.value = FuzzyChinookJuvenile_DVS.tif)
  }else{
    ch.juv.all.shp = NA
  }
  
  # join points shp with units and suitable shp (as long as shps are sf objects)
  ch.juv.all.shp = join.shp(ch.juv.all.shp, ch.juv.suit.shp, in.units = units.shp)
  
  # --calculate summary metrics--
  
  # if all points isn't an sf object (i.e., it doesn't exist) assume that fuzzy model run doesn't exist for visit populate metrics as NA
  # otherwise calculate metrics
  if(!"sf" %in% class(ch.juv.all.shp)){
    ch.juv.metrics.wide = tb.metrics %>%
      mutate(model = "fuzzy", species = "chinook", lifestage = "juvenile",
             hab.area.suitable = NA, pred.fish = NA, pred.fish.suitable = NA, 
             med = NA, mean = NA, sd = NA, med.suitable = NA, mean.suitable = NA, sd.suitable = NA)
  }else{
    # create tibble to store metrics
    ch.juv.metrics = tibble()
    
    # area for units and chinook suitable intersections
    ch.juv.metrics = ch.juv.metrics %>% 
      bind_rows(., calc.unit.area(units.ch.juv.suit, by.suit = TRUE) %>% mutate(var = "hab.area"))
    
    # capacity by group field
    ch.juv.metrics = ch.juv.metrics %>% 
      bind_rows(., calc.unit.capacity(ch.locs.shp, by.suit = FALSE) %>% mutate(var = "pred.fish"))
    
    # capacity by group field and suitability category
    ch.juv.metrics = ch.juv.metrics %>% 
      bind_rows(., calc.unit.capacity(ch.locs.shp, by.suit = TRUE) %>% mutate(var = "pred.fish"))
    
    # model values by group field
    ch.juv.metrics = ch.juv.metrics %>% 
      bind_rows(., calc.unit.stats(ch.juv.all.shp, in.field = "ras.value", by.suit = FALSE))
    
    # model values by group field and suitability category
    ch.juv.metrics = ch.juv.metrics %>% 
      bind_rows(., calc.unit.stats(ch.juv.all.shp, in.field = "ras.value", by.suit = TRUE))
    
    # convert to wide form tibble
    ch.juv.metrics.wide = ch.juv.metrics %>%
      unite("variable", c("var", "category"), sep = ".", remove = TRUE) %>%
      mutate(variable = str_replace_all(variable, ".NA", "")) %>%
      spread(variable, value) %>% 
      mutate(model = "fuzzy", species = "chinook", lifestage = "juvenile") %>%
      left_join(tb.metrics, by = group.field)
  }
  
  # join and re-order columns ---------------------------
  
  out.metrics = bind_rows(nrei.metrics.wide, ch.metrics.wide, st.metrics.wide, ch.juv.metrics.wide) %>%
    mutate(visit.id = visit.id,
           pred.fish = replace_na(pred.fish, 0),
           pred.fish.suitable = replace_na(pred.fish.suitable, 0)) %>%
    dplyr::select(visit.id, !!as.name(group.field), model, species, lifestage, area.delft, hab.area.suitable, pred.fish, pred.fish.suitable, med, mean, sd, med.suitable, mean.suitable, sd.suitable)
  
  return(out.metrics)
  
}


#' Check and read in shapefile
#'
#' @param in.shp Input shapefile filepath
#'
#' @return If shapefile exists will return input shapefile otherwise returns NA
#' @export
#'
#' @examples
#' check.shp("C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/VISIT_1029/HSI/reddPlacement/Fuzzy_ReddLocs_Steelhead.shp")
check.shp = function(in.shp){
  if(length(in.shp) > 0){
    out.shp = st_read(in.shp, quiet = TRUE) %>% st_make_valid()
  }else{
    out.shp = NA
  }
  return(out.shp)
}


#' Join shapefile with units and suitability polygon
#'
#' @param in.shp Input shapefile
#' @param in.suit Input suitability polygon shapefile
#' @param in.units Input units polygon shapefile
#'
#' @return If shapefile with units and suitability category appended
#' @export
#'
#' @examples
#' check.shp("C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/VISIT_1029/HSI/reddPlacement/Fuzzy_ReddLocs_Steelhead.shp")
join.shp = function(in.shp, in.suit, in.units = units.shp){
  
  if("sf" %in% class(in.shp)){
    in.shp = in.shp %>%
      st_join(in.units, left = FALSE)}
  
  if(all("sf" %in% class(in.shp), "sf" %in% class(in.suit))){
    in.shp = in.shp %>%
      st_join(in.suit)}
  
  return(in.shp)
}


#' Calculate unit polygon area
#'
#' @param in.shp Input shapefile (sf object)
#' @param by.suit If TRUE area is calculated for group field (e.g., 'UnitForm' field) within suitable polygon.
#' If FALSE area is calculated for group field (e.g., 'UnitForm' field).  Default set to FALSE.
#'
#' @return Returns tibble of areas
#' @export
#'
#' @examples
calc.unit.area = function(in.shp, by.suit = FALSE){
  
  # if shp isn't an sf object or has 0 rows set the output to 0
  if(any(!"sf" %in% class(in.shp), nrow(in.shp) == 0)){
    if(by.suit == TRUE){
      tb = tb.units.cats %>% mutate(value = 0.0)
    }else{
      tb = tb.units %>% mutate(value = 0.0)
    }
    # otherwise calculate shp area
  }else{
    # calculate area and convert to tibble
    shp.tb = in.shp %>%
      mutate(area = st_area(.) %>% as.numeric() %>% round(3)) %>%
      st_drop_geometry()
    # if by.suit is set to TRUE then sum areas by group field and suitability category
    if(by.suit == TRUE){
      shp.tb = shp.tb %>%
        group_by(!!as.name(group.field), layer) %>%
        summarise(value = sum(area)) %>%
        mutate(category = ifelse(layer == 1, "suitable", NA)) %>%
        dplyr::select(-layer)
      tb = tibble(category = c('suitable')) %>% left_join(shp.tb, by = "category") %>%
        mutate(value = replace_na(value, 0))
      # if group.layer is set to FALSE then sum all areas
    }else{
      tb = shp.tb %>%
        group_by(!!as.name(group.field)) %>%
        summarise(value = sum(area))
    }
  }
  
  return(tb)
  
}


#' Calculate unit capacity (raw counts)
#'
#' @param in.shp Input shapefile (sf object)
#' @param by.suit If TRUE capacity is calculated for group field (e.g., 'UnitForm' field) within suitable polygon.
#' If FALSE capacity is calculated for group field (e.g., 'UnitForm' field).  Default set to FALSE.
#' 
#' @return Returns tibble of capacity (counts)
#' @export
#'
#' @examples
calc.unit.capacity = function(in.shp, by.suit = FALSE){

  # if shp isn't an sf object or has 0 rows set the output to 0
  if(any(!"sf" %in% class(in.shp), nrow(in.shp) == 0)){
    if(by.suit == TRUE){
      tb = tb.units.cats %>% mutate(value = 0.0)
    }else{
      tb = tb.units %>% mutate(value = 0.0)
    }
    # if layer (field for suitable and best polygons) isn't in input shp set output value to 0
  }else if(all(by.suit == TRUE, !("layer" %in% names(in.shp)))){
    tb = tb.units.cats %>% mutate(value = 0.0)
    # otherwise calculate capacity as count
  }else{
    # convert shp to tibble
    shp.tb = in.shp %>% st_drop_geometry()
    # if group.layer is set to TRUE then count rows (i.e., input points) by group field and suitability category
    if(by.suit == TRUE){
      shp.tb = shp.tb %>%
        group_by(!!as.name(group.field), layer) %>%
        summarize(value = n()) %>%
        mutate(category = ifelse(layer == 1, "suitable", NA)) %>%
        dplyr::select(-layer)
      tb = tibble(category = c('suitable')) %>% left_join(shp.tb, by = "category") %>%
        mutate(value = replace_na(value, 0)) 
      # if group.layer is set to FALSE then count all rows by group field
    }else{
      tb = shp.tb %>% 
        group_by(!!as.name(group.field)) %>%
        summarize(value = n())
    }
  }
  return(tb)
}

#' Calculate unit model value summary statistics
#'
#' @param in.shp Input shapefile (sf object)
#' @param in.field Name of field (i.e., column) used to calculate summary statistics
#' @param by.suit If TRUE summary stats are calculated for group field (e.g., 'UnitForm' field) within suitable polygon.
#' If FALSE summary stats are calculated for group field (e.g., 'UnitForm' field).  Default set to FALSE.
#' 
#' @return Returns tibble of capacity (counts)
#' @export
#'
#' @examples
calc.unit.stats = function(in.shp, in.field, by.suit = FALSE){
  
  tb.stat = tibble(var = c("med", "mean", "sd"))
  
  # if shp isn't an sf object or has 0 rows set the output to NA
  if(any(!"sf" %in% class(in.shp), nrow(in.shp) == 0)){
    if(by.suit == TRUE){
      tb = tb.units.cats %>% crossing(tb.stat) %>% mutate(value = NA)
    }else{
      tb = tb.units %>% mutate(value = NA)
    }
    # if layer (field for suitable and best polygons) isn't in input shp set output value to NA
  }else if(all(by.suit == TRUE, !("layer" %in% names(in.shp)))){
    tb = tb.units.cats %>% crossing(tb.stat) %>% mutate(value = NA)
    # otherwise calculate capacity as count
  }else{
    # convert shp to tibble
    shp.tb = in.shp %>% st_drop_geometry()
    # if group.layer is set to TRUE then count rows (i.e., input points) by UnitID and suitability category
    if(by.suit == TRUE){
      shp.tb = shp.tb %>%
        filter(!is.na(layer)) %>%
        group_by(!!as.name(group.field), layer) %>%
        summarize(med = median(!!as.name(in.field), na.rm = TRUE) %>% round(3),
                  mean = mean(!!as.name(in.field), na.rm = TRUE) %>% round(3),
                  sd = sd(!!as.name(in.field), na.rm = TRUE) %>% round(3)) %>%
        mutate(category = ifelse(layer == 1, "suitable", NA)) %>%
        dplyr::select(-layer)
      tb = tibble(category = c('suitable')) %>% left_join(shp.tb, by = "category") %>%
        gather(key = "var", value = "value", med, mean, sd) %>%
        mutate(value = replace_na(value, 0))
      # if group.layer is set to FALSE then count all rows by UnitID
    }else{
      tb = shp.tb %>% 
        group_by(!!as.name(group.field)) %>%
        summarize(med = median(!!as.name(in.field), na.rm = TRUE) %>% round(3),
                  mean = mean(!!as.name(in.field), na.rm = TRUE) %>% round(3),
                  sd = sd(!!as.name(in.field), na.rm = TRUE) %>% round(3)) %>%
        gather(key = "var", value = "value", med, mean, sd)
    }
  }
  return(tb)
}
