# visit.dir = "C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/VISIT_1027"
# check = calc.site.fish.metrics(visit.dir)

#' Calculate site-level fish metrics
#'
#' @param visit.dir Full filepath to visit folder
#'
#' @return A tibble with following summary:
#' deflt extent area
#' main thalweg length (clipped to delft shapefile extent)
#' total thalweg(s) length (clipped to deflt shapefile extent)
#' nrei suitable area
#' nrei best area
#' nrei fish capacity entire reach
#' nrei fish capacity best area
#' fuzzy chinook spawner area
#' fuzzy chinook spawner best area
#' fuzzy chinook spawner redd capacity entire reach
#' fuzzy chinook spawner redd capacity best area
#' fuzzy steelhead spawner area
#' fuzzy steelhead spawner best area
#' fuzzy steelhead spawner redd capacity entire reach
#' fuzzy steelhead spawner redd capacity best area
#' @export
#'
#' @examples
calc.site.fish.metrics = function(visit.dir){
  
  # print visit dir for script progress tracking
  print(visit.dir)
  
  # get visit id from visit directory
  visit.id = as.numeric(unlist(str_split(visit.dir, "VISIT_"))[2])
  
  # create tibble to append metrics to
  tb.meas = tibble()
  
  # extent ---------------------------
  # used to clip thalweg
  
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
  
  # thalwegs (clipped to model extent) ---------------------------

  # if multiple thalwegs shp exists and has 'ThalwegTyp' field use that otherwise use single thalweg shp
  # if neither exist and/or extent doesn't exist then thalweg is set to na
  thalwegs.file = unlist(list.files(path = visit.dir, pattern = "^Thalwegs.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  thalweg.file = unlist(list.files(path = visit.dir, pattern = "^Thalweg.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  
  if(all(length(thalwegs.file) > 0 & !is.na(extent.shp) & "ThalwegTyp" %in% names(st_read(thalwegs.file, quiet = TRUE)))){
    thalweg.shp = st_read(thalwegs.file, quiet = TRUE) %>% st_crop(extent.shp)
    thalweg.main.shp = thalweg.shp %>% dplyr::filter(ThalwegTyp == "Main")
  }else if(length(thalweg.file) > 0 & !is.na(extent.shp)){
    thalweg.shp = st_read(thalweg.file, quiet = TRUE) %>% st_crop(extent.shp)
    thalweg.main.shp = thalweg.shp
  }else{
    thalweg.shp = NA
    thalweg.main.shp = NA
  }
  
  # calculate length of all thalwegs
  tb.meas = tb.meas %>% bind_rows(., calc.length(thalweg.shp) %>% mutate(layer = "thalweg", var = "length", category = "reach"))
  
  # calculate length of main thalwegs
  tb.meas = tb.meas %>% bind_rows(., calc.length(thalweg.main.shp) %>% mutate(layer = "thalweg", var = "length", category = "main"))
  
  # nrei ---------------------------
  
  # read in extent shp
  nrei.ext.file = unlist(list.files(path = visit.dir, pattern = "^Delft_Extent.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  nrei.ext.shp = check.shp(nrei.ext.file)
  
  # calculate extent area
  tb.meas = tb.meas %>% 
    bind_rows(., calc.area(nrei.ext.shp, nrei.ext.shp) %>% mutate(category = "reach", layer = "nrei", var = "area", species = "steelhead", lifestage = "juvenile"))
  
  # read in suitable shp
  nrei.suit.file = unlist(list.files(path = visit.dir, pattern = "^NREI_Suitable_Poly.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  nrei.suit.shp = check.shp(nrei.suit.file)
  
  # calculate area for suitable polygon
  tb.meas = tb.meas %>% 
    bind_rows(., calc.area(nrei.suit.shp, nrei.ext.shp) %>% mutate(category = "suitable", layer = "nrei", var = "area", species = "steelhead", lifestage = "juvenile"))

  # read in predicted fish locations shp
  nrei.locs.file = unlist(list.files(path = visit.dir, pattern = "^NREI_FishLocs.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  nrei.locs.shp = check.shp(nrei.locs.file)
  
  # join with suitable polygon (as long as both shps aren't na)
  nrei.locs.suit = join.shp(nrei.locs.shp, nrei.suit.shp)
  
  # calculate fish capacity for suitable polygon
  tb.meas = tb.meas %>% 
    bind_rows(., calc.capacity(nrei.locs.suit, nrei.ext.shp) %>% mutate(category = "suitable", layer = "nrei", var = "pred.fish", species = "steelhead", lifestage = "juvenile"))
  
  # calculate fish capacity for entire reach
  tb.meas = tb.meas %>% 
    bind_rows(., calc.capacity(nrei.locs.shp, nrei.ext.shp) %>% mutate(category = "reach", layer = "nrei", var = "pred.fish", species = "steelhead", lifestage = "juvenile"))
  
  # read in nrei all points shp
  nrei.all.file = unlist(list.files(path = visit.dir, pattern = "^NREI_All_Pts.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  nrei.all.shp = check.shp(nrei.all.file)
  
  # join points shp with suitable shp (as long as shps are sf objects)
  nrei.all.suit = join.shp(nrei.all.shp, nrei.suit.shp)
  
  # model stat values for entire reach
  tb.meas = tb.meas %>% 
    bind_rows(., calc.unit.stats(nrei.all.shp, in.field = "nre_Jph") %>% mutate(category = "reach", layer = "nrei", species = "steelhead", lifestage = "juvenile"))
  
  # model stat values by suitable
  tb.meas = tb.meas %>% 
    bind_rows(., calc.unit.stats(nrei.all.suit, in.field = "nre_Jph") %>% mutate(category = "suitable", layer = "nrei", species = "steelhead", lifestage = "juvenile"))
  
  # fuzzy chinook spawner ---------------------------
  
  # read in extent shp
  ch.ext.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_Chinook_Extent.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  ch.ext.shp = check.shp(ch.ext.file)
  
  # calculate extent area
  tb.meas = tb.meas %>% 
    bind_rows(., calc.area(ch.ext.shp, ch.ext.shp) %>% mutate(category = "reach", layer = "fuzzy", var = "area", species = "chinook", lifestage = "spawner"))
  
  # read in suitable shp
  ch.suit.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_Suitable_Poly_Chinook.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  ch.suit.shp = check.shp(ch.suit.file)
  
  # calculate area for suitable polygon
  tb.meas = tb.meas %>% 
    bind_rows(., calc.area(ch.suit.shp, ch.ext.shp) %>% mutate(category = "suitable", layer = "fuzzy", var = "area", species = "chinook", lifestage = "spawner"))
  
  # read in predicted redd locations shp
  ch.redds.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_ReddLocs_Chinook.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  ch.redds.shp = check.shp(ch.redds.file)
  
  # join with suitable polygon (as long as both shps aren't na)
  ch.redds.suit = join.shp(ch.redds.shp, ch.suit.shp)
  
  # calculate redd capacity for suitable polygon
  tb.meas = tb.meas %>% 
    bind_rows(., calc.capacity(ch.redds.suit, ch.ext.shp) %>% mutate(category = "suitable", layer = "fuzzy", var = "pred.fish", species = "chinook", lifestage = "spawner"))
  
  # calculate redd capacity for entire reach
  tb.meas = tb.meas %>% 
    bind_rows(., calc.capacity(ch.redds.shp, ch.ext.shp) %>% mutate(category = "reach", layer = "fuzzy", var = "pred.fish", species = "chinook", lifestage = "spawner"))
  
  # read in fuzzy raster, join with suitability shape and return data frames
  ch.raster.file = unlist(list.files(path = visit.dir, pattern = "^FuzzyChinookSpawner_DVSC.tif$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(length(ch.raster.file) > 0){
    ch.raster = raster(ch.raster.file)
    ch.all.df = as.data.frame(ch.raster) %>% rename(ras.value = FuzzyChinookSpawner_DVSC) %>% filter(!is.na(ras.value))
    if("sf" %in% class(ch.suit.shp)){
      ch.suit.df = raster::extract(x = ch.raster, y = ch.suit.shp, df = TRUE) %>%
        rename(ras.value = FuzzyChinookSpawner_DVSC) 
    }else{
      ch.suit.df = NA
    }
  }else{
    ch.raster = NA
    ch.all.df = NA
    ch.suit.df = NA
  }
  
  # model stat values for entire reach
  tb.meas = tb.meas %>% 
    bind_rows(., calc.unit.stats(ch.all.df, in.field = "ras.value") %>% mutate(category = "reach", layer = "fuzzy", species = "chinook", lifestage = "spawner"))
  
  # model stat values by suitable
  tb.meas = tb.meas %>% 
    bind_rows(., calc.unit.stats(ch.suit.df, in.field = "ras.value") %>% mutate(category = "suitable", layer = "fuzzy", species = "chinook", lifestage = "spawner"))
  
  
  # fuzzy steelhead spawner ---------------------------
  
  # read in extent shp
  st.ext.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_Steelhead_Extent.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  st.ext.shp = check.shp(st.ext.file)
  
  # calculate extent area
  tb.meas = tb.meas %>% 
    bind_rows(., calc.area(st.ext.shp, st.ext.shp) %>% mutate(category = "reach", layer = "fuzzy", var = "area", species = "steelhead", lifestage = "spawner"))
  
  # read in suitable shp
  st.suit.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_Suitable_Poly_Steelhead.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  st.suit.shp = check.shp(st.suit.file)
  
  # calculate area for suitable polygon
  tb.meas = tb.meas %>% 
    bind_rows(., calc.area(st.suit.shp, st.ext.shp) %>% mutate(category = "suitable", layer = "fuzzy", var = "area", species = "steelhead", lifestage = "spawner"))
  
  # read in predicted redd locations shp
  st.redds.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_ReddLocs_Steelhead.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  st.redds.shp = check.shp(st.redds.file)
  
  
  # join with suitable polygon (as long as both shps aren't na)
  st.redds.suit = join.shp(st.redds.shp, st.suit.shp)
  
  # calculate redd capacity for suitable polygon
  tb.meas = tb.meas %>% 
    bind_rows(., calc.capacity(st.redds.suit, st.ext.shp) %>% mutate(category = "suitable", layer = "fuzzy", var = "pred.fish", species = "steelhead", lifestage = "spawner"))
  
  # calculate redd capacity for entire reach
  tb.meas = tb.meas %>% 
    bind_rows(., calc.capacity(st.redds.shp, st.ext.shp) %>% mutate(category = "reach", layer = "fuzzy", var = "pred.fish", species = "steelhead", lifestage = "spawner"))
  
  # read in fuzzy raster, join with suitability shape and return data frames
  st.raster.file = unlist(list.files(path = visit.dir, pattern = "^FuzzySteelheadSpawner_DVSC.tif$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(length(st.raster.file) > 0){
    st.raster = raster(st.raster.file)
    st.all.df = as.data.frame(st.raster) %>% rename(ras.value = FuzzySteelheadSpawner_DVSC) %>% filter(!is.na(ras.value))
    if("sf" %in% class(st.suit.shp)){
      st.suit.df = raster::extract(x = st.raster, y = st.suit.shp, df = TRUE) %>%
        rename(ras.value = FuzzySteelheadSpawner_DVSC) 
    }else{
      st.suit.df = NA
    }
  }else{
    st.raster = NA
    st.all.df = NA
    st.suit.df = NA
  }
  
  # model stat values for entire reach
  tb.meas = tb.meas %>% 
    bind_rows(., calc.unit.stats(st.all.df, in.field = "ras.value") %>% mutate(category = "reach", layer = "fuzzy", species = "steelhead", lifestage = "spawner"))
  
  # model stat values by suitable
  tb.meas = tb.meas %>% 
    bind_rows(., calc.unit.stats(st.suit.df, in.field = "ras.value") %>% mutate(category = "suitable", layer = "fuzzy", species = "steelhead", lifestage = "spawner"))
  
  # fuzzy chinook juvenile ---------------------------
  
  # read in extent shp
  ch.juv.ext.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_Chinook_Juvenile_Extent.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  ch.juv.ext.shp = check.shp(ch.juv.ext.file)
  
  # calculate extent area
  tb.meas = tb.meas %>% 
    bind_rows(., calc.area(ch.juv.ext.shp, ch.juv.ext.shp) %>% mutate(category = "reach", layer = "fuzzy", var = "area", species = "chinook", lifestage = "juvenile"))
  
  # read in suitable shp
  ch.juv.suit.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_Suitable_Poly_ChinookJuvenile.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  ch.juv.suit.shp = check.shp(ch.juv.suit.file)
  
  # calculate area for suitable polygon
  tb.meas = tb.meas %>% 
    bind_rows(., calc.area(ch.juv.suit.shp, ch.juv.ext.shp) %>% mutate(category = "suitable", layer = "fuzzy", var = "area", species = "chinook", lifestage = "juvenile"))
  
  # read in predicted fish locations shp
  ch.locs.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_JuvenileLocs_Chinook.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  ch.locs.shp = check.shp(ch.locs.file)
  
  # join with suitable polygon (as long as both shps aren't na)
  ch.locs.suit = join.shp(ch.locs.shp, ch.juv.suit.shp)
  
  # calculate redd capacity for suitable polygon
  tb.meas = tb.meas %>% 
    bind_rows(., calc.capacity(ch.locs.suit, ch.juv.ext.shp) %>% mutate(category = "suitable", layer = "fuzzy", var = "pred.fish", species = "chinook", lifestage = "juvenile"))
  
  # calculate redd capacity for entire reach
  tb.meas = tb.meas %>% 
    bind_rows(., calc.capacity(ch.locs.shp, ch.juv.ext.shp) %>% mutate(category = "reach", layer = "fuzzy", var = "pred.fish", species = "chinook", lifestage = "juvenile"))
  
  # read in fuzzy raster, join with suitability shape and return data frames
  ch.juv.raster.file = unlist(list.files(path = visit.dir, pattern = "^FuzzyChinookJuvenile_DVS.tif$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(length(ch.juv.raster.file) > 0){
    ch.juv.raster = raster(ch.juv.raster.file)
    ch.juv.all.df = as.data.frame(ch.juv.raster) %>% rename(ras.value = FuzzyChinookJuvenile_DVS) %>% filter(!is.na(ras.value))
    if("sf" %in% class(ch.juv.suit.shp)){
      ch.juv.suit.df = raster::extract(x = ch.juv.raster, y = ch.juv.suit.shp, df = TRUE) %>%
        rename(ras.value = FuzzyChinookJuvenile_DVS) 
    }else{
      ch.juv.suit.df = NA
    }
  }else{
    ch.juv.raster = NA
    ch.juv.all.df = NA
    ch.juv.suit.df = NA
  }
  
  # model stat values for entire reach
  tb.meas = tb.meas %>% 
    bind_rows(., calc.unit.stats(ch.juv.all.df, in.field = "ras.value") %>% mutate(category = "reach", layer = "fuzzy", species = "chinook", lifestage = "juvenile"))
  
  # model stat values by suitable
  tb.meas = tb.meas %>% 
    bind_rows(., calc.unit.stats(ch.juv.suit.df, in.field = "ras.value") %>% mutate(category = "suitable", layer = "fuzzy", species = "chinook", lifestage = "juvenile"))
  
  
  # clean-up and save output ---------------------------
  
  # add visit id and re-order columns
  tb.meas = tb.meas %>% mutate(visit.id = visit.id) %>% dplyr::select(visit.id, layer, var, category, value, species, lifestage)
  
  # export calculated metrics
  return(tb.meas)
  
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
    out.shp = st_read(in.shp, quiet = TRUE) 
    # if(!st_is_valid(out.shp)){out.shp = out.shp %>% st_make_valid(.)}
  }else{
    out.shp = NA
  }
  return(out.shp)
}


#' Calculate polyline length
#'
#' @param in.shp Input shapefile (sf object)
#'
#' @return Returns tibble of summed lengths
#' @export
#'
#' @examples
calc.length = function(in.shp){
  
  # if input shape isn't a sf object, then set output to NA
  if(!"sf" %in% class(in.shp)){
    tb = tibble(value = NA)
  # if shp has 0 rows set the output value to 0
  }else if(nrow(in.shp) == 0){
    tb = tibble(value = 0)
  # otherwise calculate and sum lengths
  }else{
    value = as.numeric(st_length(in.shp)) %>% sum() %>% as.numeric() %>% round(3)
    tb = tibble(value)
  }
  return(tb)
}


#' Calculate polygon area
#'
#' @param in.shp Input shapefile (sf object)
#' 
#' @return Returns tibble of areas
#' @export
#'
#' @examples
calc.area = function(in.shp, extent.shp){
  
  # if input shape isn't a sf object, then set output to NA
  if(all(!"sf" %in% class(in.shp), !"sf" %in% class(extent.shp))){
    tb = tibble(value = NA)
  }else if(!"sf" %in% class(in.shp)){
    tb = tibble(value = 0) 
  # if shp has 0 rows set the output value to 0
  }else if(nrow(in.shp) == 0){
    tb = tibble(value = 0)
  # otherwise calculate shp area
  }else{
    # calculate area and convert to tibble
    shp.tb = in.shp %>%
      mutate(area = st_area(.) %>% as.numeric() %>% round(3)) %>%
      st_drop_geometry()
    tb = shp.tb %>%
      summarise(value = sum(area))
  }
  return(tb)
}


#' Calculate capacity (raw counts)
#'
#' @param in.shp Input shapefile (sf object)
#' 
#' @return Returns tibble of capacity (counts)
#' @export
#'
#' @examples
calc.capacity = function(in.shp, extent.shp){
  
  # if input shape isn't a sf object, then set output to NA
  if(all(!"sf" %in% class(in.shp), !"sf" %in% class(extent.shp))){
    tb = tibble(value = NA)
  }else if(!"sf" %in% class(in.shp)){
    tb = tibble(value = 0) 
    # if shp has 0 rows set the output value to 0
  }else if(nrow(in.shp) == 0){
      tb = tibble(value = 0)
  # otherwise calculate capacity as count
  }else{
    # convert shp to tibble
    shp.tb = in.shp %>% st_drop_geometry()
    # count all rows
    tb = shp.tb %>% summarize(value = n())
  }
  return(tb)
}

#' Join shapefile with suitability polygon
#'
#' @param in.shp Input shapefile
#' @param in.suit Input suitability polygon shapefile
#'
#' @return Input shapefile with suitability category appended
#' @export
#'
#' @examples
join.shp = function(in.shp, in.suit){
  
  if(all("sf" %in% class(in.shp), "sf" %in% class(in.suit))){
    out.shp = in.shp %>%
      st_join(in.suit) %>%
      dplyr::filter(layer > 0)
  }else{
    out.shp = NA
  }
  
  return(out.shp)
}


#' Calculate unit model value summary statistics
#'
#' @param in.shp Input shapefile (sf object)
#' @param in.field Name of field (i.e., column) used to calculate summary statistics
#' 
#' @return Returns tibble of mean, median, sd values
#' @export
#'
#' @examples
calc.unit.stats = function(in.shp, in.field){
  
  tb.stat = tibble(var = c("med", "mean", "sd"))
  
  # if shp isn't an sf object or has 0 rows set the output to NA
  if(all(!"sf" %in% class(in.shp), !"data.frame" %in% class(in.shp))){
    tb = tb.stat %>% mutate(value = NA)
  }else if(nrow(in.shp) == 0){
    tb = tb.stat %>% mutate(value = NA)
  }else if(all("data.frame" %in% class(in.shp), !"sf" %in% class(in.shp))){
    tb = in.shp %>% 
      summarize(med = median(!!as.name(in.field), na.rm = TRUE) %>% round(3),
                mean = mean(!!as.name(in.field), na.rm = TRUE) %>% round(3),
                sd = sd(!!as.name(in.field), na.rm = TRUE) %>% round(3)) %>%
      gather(key = "var", value = "value", med, mean, sd)
  }else{
    # convert shp to tibble
    shp.tb = in.shp %>% st_drop_geometry()

    tb = shp.tb %>% 
      summarize(med = median(!!as.name(in.field), na.rm = TRUE) %>% round(3),
                mean = mean(!!as.name(in.field), na.rm = TRUE) %>% round(3),
                sd = sd(!!as.name(in.field), na.rm = TRUE) %>% round(3)) %>%
      gather(key = "var", value = "value", med, mean, sd)
  }
  return(tb)
}
