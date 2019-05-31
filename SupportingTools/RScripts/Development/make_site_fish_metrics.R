# todo: check with Natalie - thalweg length (m) is sum of all lengths - is this waht she wanted?
#       also - should main thalweg be [Channel == "Main" & ThalwegTyp == "Main"] -- she only had the latter
# if(nrei.pred.fish <= 1){
#   nrei.suit.area.m2 = 0.0
#   nrei.best.area.m2 = 0.0
# }

visit.dir = "C:/etal/Shared/Projects/USA/GUTUpscale/wrk_Data/VISIT_1029"

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
    bind_rows(., calc.area(nrei.ext.shp, group.layer = FALSE) %>% mutate(category = "reach", layer = "nrei", var = "area", species = "steelhead", lifestage = "juvenile"))
  
  # read in suitable shp
  nrei.suit.file = unlist(list.files(path = visit.dir, pattern = "^NREI_Suitable_Poly.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  nrei.suit.shp = check.shp(nrei.suit.file)
  
  # calculate area by suitable category (1 = suitable, 2 = best)
  tb.meas = tb.meas %>% 
    bind_rows(., calc.area(nrei.suit.shp, group.layer = TRUE) %>% mutate(layer = "nrei", var = "area", species = "steelhead", lifestage = "juvenile"))

  # read in predicted fish locations shp
  nrei.locs.file = unlist(list.files(path = visit.dir, pattern = "^NREI_FishLocs.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  nrei.locs.shp = check.shp(nrei.locs.file)
  
  # join with suitable polygon (as long as both shps aren't na)
  if(all(!is.na(nrei.suit.shp), !is.na(nrei.locs.shp))){nrei.locs.shp = nrei.locs.shp %>% st_join(nrei.suit.shp)}
  
  # remove duplicate points created in join (sorting layer by descending so 2 = best is selected over 1 = suitable)
  nrei.locs.shp = nrei.locs.shp %>%
    arrange(idx, desc(layer)) %>%
    distinct(idx, .keep_all = TRUE)
  
  # calculate fish capacity by suitable category (1 = suitable, 2 = best)
  tb.meas = tb.meas %>% 
    bind_rows(., calc.capacity(nrei.locs.shp, group.layer = TRUE) %>% mutate(layer = "nrei", var = "pred.fish", species = "steelhead", lifestage = "juvenile"))
  
  # calculate fish capacity for entire reach
  tb.meas = tb.meas %>% 
    bind_rows(., calc.capacity(nrei.locs.shp, group.layer = FALSE) %>% mutate(category = "reach", layer = "nrei", var = "pred.fish", species = "steelhead", lifestage = "juvenile"))
  
  # fuzzy chinook spawner ---------------------------
  
  # read in extent shp
  ch.ext.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_Chinook_Extent.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  ch.ext.shp = check.shp(ch.ext.file)
  
  # calculate extent area
  tb.meas = tb.meas %>% 
    bind_rows(., calc.area(ch.ext.shp, group.layer = FALSE) %>% mutate(category = "reach", layer = "fuzzy", var = "area", species = "chinook", lifestage = "spawner"))
  
  # read in suitable shp
  ch.suit.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_Suitable_Poly_Chinook.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  ch.suit.shp = check.shp(ch.suit.file)
  
  # calculate area by suitable category (1 = suitable, 2 = best)
  tb.meas = tb.meas %>% 
    bind_rows(., calc.area(ch.suit.shp, group.layer = TRUE) %>% mutate(layer = "fuzzy", var = "area", species = "chinook", lifestage = "spawner"))
  
  # read in predicted redd locations shp
  ch.redds.files = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_ReddLocs_Chinook.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  ch.redds.file = grep("reddPlacement", ch.redds.files, value = TRUE)
  ch.redds.shp = check.shp(ch.redds.file)
  
  # if point id (idx) field doesn't exist, create it
  if(!"idx" %in% names(ch.redds.shp)){ch.redds.shp = ch.redds.shp %>% mutate(idx = row_number())}
  
  # join with suitable polygon (as long as both shps aren't na)
  if(all(!is.na(ch.suit.shp), !is.na(ch.redds.shp))){ch.redds.shp = ch.redds.shp %>% st_join(ch.suit.shp)}
  
  # remove duplicate points created in join (sorting layer by descending so 2 = best is selected over 1 = suitable)
  ch.redds.shp = ch.redds.shp %>%
    arrange(idx, desc(layer)) %>%
    distinct(idx, .keep_all = TRUE)
  
  # calculate redd capacity by suitable category (1 = suitable, 2 = best)
  tb.meas = tb.meas %>% 
    bind_rows(., calc.capacity(ch.redds.shp, group.layer = TRUE) %>% mutate(layer = "fuzzy", var = "pred.fish", species = "chinook", lifestage = "spawner"))
  
  # calculate redd capacity for entire reach
  tb.meas = tb.meas %>% 
    bind_rows(., calc.capacity(ch.redds.shp, group.layer = FALSE) %>% mutate(category = "reach", layer = "fuzzy", var = "pred.fish", species = "chinook", lifestage = "spawner"))
  
  # fuzzy steelhead spawner ---------------------------
  
  # read in extent shp
  st.ext.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_Steelhead_Extent.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  st.ext.shp = check.shp(st.ext.file)
  
  # calculate extent area
  tb.meas = tb.meas %>% 
    bind_rows(., calc.area(st.ext.shp, group.layer = FALSE) %>% mutate(category = "reach", layer = "fuzzy", var = "area", species = "steelhead", lifestage = "spawner"))
  
  # read in suitable shp
  st.suit.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_Suitable_Poly_Steelhead.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  st.suit.shp = check.shp(st.suit.file)
  
  # calculate area by suitable category (1 = suitable, 2 = best)
  tb.meas = tb.meas %>% 
    bind_rows(., calc.area(st.suit.shp, group.layer = TRUE) %>% mutate(layer = "fuzzy", var = "area", species = "steelhead", lifestage = "spawner"))
  
  # read in predicted redd locations shp
  st.redds.files = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_ReddLocs_Steelhead.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  st.redds.file = grep("reddPlacement", st.redds.files, value = TRUE)
  st.redds.shp = check.shp(st.redds.file)
  
  # if point id (idx) field doesn't exist, create it
  if(!"idx" %in% names(st.redds.shp)){st.redds.shp = st.redds.shp %>% mutate(idx = row_number())}
  
  # join with suitable polygon (as long as both shps aren't na)
  if(all(!is.na(st.suit.shp), !is.na(st.redds.shp))){st.redds.shp = st.redds.shp %>% st_join(st.suit.shp)}
  
  # remove duplicate points created in join (sorting layer by descending so 2 = best is selected over 1 = suitable)
  st.redds.shp = st.redds.shp %>%
    arrange(idx, desc(layer)) %>%
    distinct(idx, .keep_all = TRUE)
  
  # calculate redd capacity by suitable category (1 = suitable, 2 = best)
  tb.meas = tb.meas %>% 
    bind_rows(., calc.capacity(st.redds.shp, group.layer = TRUE) %>% mutate(layer = "fuzzy", var = "pred.fish", species = "steelhead", lifestage = "spawner"))
  
  # calculate redd capacity for entire reach
  tb.meas = tb.meas %>% 
    bind_rows(., calc.capacity(st.redds.shp, group.layer = FALSE) %>% mutate(category = "reach", layer = "fuzzy", var = "pred.fish", species = "steelhead", lifestage = "spawner"))
  
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
    out.shp = st_read(in.shp, quiet = TRUE) %>% st_make_valid()
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
#' @param group.layer If TRUE area is calculated for each 'layer' field otherwise area is calculated for entire polygon.  Default is set to FALSE.
#'
#' @return Returns tibble of areas
#' @export
#'
#' @examples
calc.area = function(in.shp, group.layer = FALSE){
  
  # if input shape isn't a sf object, then set output to NA
  if(!"sf" %in% class(in.shp)){
    if(group.layer == TRUE){
      tb = tibble(value = NA, category = "suitable")
    }else{
      tb = tibble(value = NA)
    }
  # if shp has 0 rows set the output value to 0
  }else if(nrow(in.shp) == 0){
    if(group.layer == TRUE){
      tb = tibble(value = 0, category = "suitable")
    }else{
      tb = tibble(value = 0)
    }
  # otherwise calculate shp area
  }else{
    # calculate area and convert to tibble
    shp.tb = in.shp %>%
      mutate(area = st_area(.) %>% as.numeric() %>% round(3)) %>%
      st_drop_geometry()
    # if group.layer is set to TRUE then sum areas by suitability category
    if(group.layer == TRUE){
      shp.tb = shp.tb %>%
        group_by(layer) %>%
        summarise(value = sum(area)) %>%
        mutate(value = ifelse(layer == 1, sum(value), value),
               category = ifelse(layer == 1, "suitable", ifelse(layer == 2, "best", NA))) %>%
        dplyr::select(-layer)
      tb = tibble(category = c('suitable', 'best')) %>% left_join(shp.tb, by = "category") %>%
        mutate(value = replace_na(value, 0))
    # if group.layer is set to FALSE then sum all areas
    }else{
      tb = shp.tb %>%
        summarise(value = sum(area))
    }
  }
  
  return(tb)
  
}



#' Calculate capacity (raw counts)
#'
#' @param in.shp Input shapefile (sf object)
#' @param group.layer If TRUE capacity is calculated for each 'layer' field (joined from suitable polygon) otherwise capacity using all points.  Default is set to FALSE.
#'
#' @return Returns tibble of capacity (counts)
#' @export
#'
#' @examples
calc.capacity = function(in.shp, group.layer = FALSE){
  
  # if input shape isn't a sf object, then set output to NA
  if(!"sf" %in% class(in.shp)){
    if(group.layer == TRUE){
      tb = tibble(value = NA, category = "suitable")
    }else{
      tb = tibble(value = NA)
    }
  # if shp has 0 rows set the output value to 0
  }else if(nrow(in.shp) == 0){
    if(group.layer == TRUE){
      tb = tibble(value = 0, category = "suitable")
    }else{
      tb = tibble(value = 0)
    }
  # otherwise calculate capacity as count
  }else{
    # convert shp to tibble
    shp.tb = in.shp %>% st_drop_geometry()
    # if group.layer is set to TRUE then count rows (i.e., input points) by suitability category
    if(group.layer == TRUE){
      shp.tb = shp.tb %>%
        group_by(layer) %>%
        summarize(value = n()) %>%
        mutate(value = ifelse(layer == 1, sum(value), value),
               category = ifelse(layer == 1, "suitable", ifelse(layer == 2, "best", NA))) %>%
        dplyr::select(-layer)
      tb = tibble(category = c('suitable', 'best')) %>% left_join(shp.tb, by = "category") %>%
        mutate(value = replace_na(value, 0))
    # if group.layer is set to FALSE then count all rows
    }else{
      tb = shp.tb %>% summarize(value = n())
    }
  }
  return(tb)
}
