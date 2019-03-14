#' Calculates site-level GUT metrics
#'
#' @param data 
#'
#' @return
#BFArea: Bankfull Area in sq meters
#WEArea: Wetted Area in sq meters
#mainThalwegL:  Length in meters of the main Thalweg.
#ThalwegsL: Sum of all Lengths from multiple thalwegs, including the main and any secondary ones
#ThalwegsR: ThalwegsL/mainThalwegL 
#' @export
#'
#' @examples
calc.site.gut.metrics = function(visit.dir, run.dir, layer){
  
  # get visit id from visit directory
  visit.id = as.numeric(unlist(str_split(visit.dir, "VISIT_"))[2])
  
  # bankfull area
  bf.file = unlist(list.files(path = visit.dir, pattern = "^Bankfull.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(file.exists(bf.file)){
    bf.area.m2 = as.numeric(st_area(st_read(bf.file, quiet = TRUE)))
  }else{
    bf.area.m2 = NA
  }
  
  # wetted area
  we.file = unlist(list.files(path = visit.dir, pattern = "^WaterExtent.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(file.exists(we.file)){
    wet.area.m2 = as.numeric(st_area(st_read(we.file, quiet = TRUE)))
  }else{
    wet.area.m2 = NA
  }
  
  # thalweg length
  # todo: check with Natalie - thalweg length (m) is sum of all lengths - is this waht she wanted?
  #       also - should main thalweg be [Channel == "Main" & ThalwegTyp == "Main"] -- she only had the latter
  thalwegs.file = unlist(list.files(path = visit.dir, pattern = "^Thalwegs.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  thalweg.file = unlist(list.files(path = visit.dir, pattern = "^Thalweg.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  
  # if multiple thalwegs shp exists and has 'ThalwegTyp' field, set thalweg.shp to that, otherwise use single thalweg shp
  if(file.exists(thalwegs.file) & "ThalwegTyp" %in% names(st_read(thalwegs.file, quiet = TRUE))){
    thalweg = st_read(thalwegs.file, quiet = TRUE)
    main.thalweg = thalweg %>% dplyr::filter(ThalwegTyp == "Main")
    main.thalweg.length.m = main.thalweg %>% st_length(.) %>% sum() %>% as.numeric() %>% round(3) 
    thalweg.length.m = thalweg %>% st_length(.) %>% sum() %>% as.numeric() %>% round(3) 
    thalweg.length.ratio = round(main.thalweg.length.m / thalweg.length.m, 3)
  }else if(file.exists(thalweg.file)){
    thalweg = st_read(thalweg.file, quiet = TRUE)
    main.thalweg = thalweg
    main.thalweg.length.m = thalweg %>% st_length(.) %>% as.numeric() %>% round(3)
    thalweg.length.m = main.thalweg.length.m
    thalweg.length.ratio = round(main.thalweg.length.m / thalweg.length.m, 3)
  }else{
    main.thalweg.length.m = NA
    thalweg.length.m = NA
    thalweg.length.ratio = NA
  }
  
  # read in gut layer
  unit.files = unlist(list.files(path = visit.dir, pattern = paste("^", layer, ".shp$", sep = ""), full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  unit.file = grep(run.dir, unit.files, value = TRUE)
  
  # calculate unit edge length to area ratio
  if(file.exists(unit.file)){
    units = st_read(unit.file, quiet = TRUE) 
    n.units = units %>% nrow()
    area = units %>% st_area(.) %>% sum() %>% as.numeric()
    # commented out but saving -- approach preserves attributes
    # edges = st_cast(forms, "LINESTRING") %>% st_difference(.)
    edges = st_cast(units, "MULTILINESTRING") %>% st_union() %>% st_line_merge(.) %>% st_cast(., "LINESTRING") %>% st_sf(.)
    edge.length = edges %>% st_length(.) %>% sum() %>% as.numeric()
    edge.length.area.ratio = round(edge.length / area, 3)
   }else{
    n.units = NA
    edge.length.area.ratio = NA
  }
  
  # calculate edge density (for main thalweg and all thalwegs)
  if(exists("main.thalweg") & exists("units")){
    int.edge.main = st_intersection(main.thalweg, edges) %>% st_union(.) %>% st_cast(., "POINT") %>% st_sf(.) %>% nrow()
    edge.dens.main.thalweg = round(int.edge.main / main.thalweg.length.m, 3)
  }else{
    edge.dens.main.thalweg = NA
  }
  

  if(exists("thalweg") & exists("units")){
    int.edge.thalwegs = st_intersection(thalweg, edges) %>% st_union(.) %>% st_cast(., "POINT") %>% st_sf(.) %>% nrow()
    edge.dens.thalwegs = round(int.edge.thalwegs / thalweg.length.m, 3)
  }else{
    edge.dens.thalwegs = NA
  }

  # average number of unit and cross-section intersections
  # subset to every 10th cross-sections
  
  xs.file = unlist(list.files(path = visit.dir, pattern = "^BankfullXS.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(file.exists(xs.file) & exists("units")){
    xs = st_read(xs.file, quiet = TRUE) %>% filter(IsValid == 1)
    xs.sub = xs %>% filter(row_number() %% 10 == 1)
    int.edge.xs = st_intersection(xs.sub, edges) %>% st_union(.) %>% st_cast(., "POINT") %>% st_sf(.) %>% nrow()
    xs.length = xs.sub %>% st_length(.) %>% sum() %>% as.numeric()
    edge.dens.xs = round(int.edge.xs / xs.length, 3)
  }else{
    edge.dens.xs = NA
  }
  
  # create tb of calculated metrics
  metrics = tibble(layer, visit.id, bf.area.m2, wet.area.m2, main.thalweg.length.m, thalweg.length.m, thalweg.length.ratio, 
                   edge.length.area.ratio, edge.dens.main.thalweg, edge.dens.thalwegs, edge.dens.xs)

  return(metrics)
}
   
