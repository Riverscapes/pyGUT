#Natalie Kramer (n.kramer.anderson@gmail.com)
#updated Oct 29, 2017

#This script will take any GUT outuput and with the output layer and attribute specified summarize basic
#geometries by the attribute.

#Outputs (grouped by attribute class)
#units will depend on input spatial class, gut is in UTM so...
#medArea=median of Area of all polygons (m2)
#medPerim=median of Perimeter of all Polygons (m) 
#avgArea= average area of all polygons  (m2)
#avgPerim=average Perimeter of all polygons (m)
#sdArea=st dev of Area '(m2)
#sdPerim= st dev of Perimeters (m)
#totArea= sum of all areas (m2)
#totPerim= sum of all perimeters (m)
#n= total count of polygons (#)
#PercArea = totArea/sum(totArea)*100 (%)- percent of reach covered by each unity type
#PerimbyArea =avgPerim/avgArea

# visit.dir = visit.summary %>% slice(1) %>% dplyr::select(visit.dir) %>% as.character()
# layer = "Tier3_InChannel_GU"
# run.dir = "GUT_2.1/Run_01"

#' Title
#'
#' @param visit.dir 
#' @param run.dir 
#' @param gut.layer 
#'
#' @return
#' @export
#'
#' @examples
make.gut.unit.metrics = function(visit.dir, run.dir, gut.layer){
  
  print(visit.dir)
  
  # get visit id from visit directory
  visit.id = as.numeric(unlist(str_split(visit.dir, "VISIT_"))[2])
  
  # create tibble
  tb.metrics = tibble()
  
  # get path to gut layer
  unit.files = unlist(list.files(path = visit.dir, pattern = paste("^", gut.layer, ".shp$", sep = ""), full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  unit.file = grep(run.dir, unit.files, value = TRUE)
  
  # read in gut layer if it exists
  if(length(unit.file) > 0){
    
    # calculate area and perimeter
    units.gut = st_read(unit.file, quiet = TRUE) %>%
      mutate(area = st_area(.) %>% as.numeric() %>% round(3),
             perim = st_perimeter(.) %>% as.numeric())
    
    # calculate total area of all units
    total.area = units.gut %>% st_area(.) %>% sum() %>% as.numeric()
    
    # get column names
    units.cols = colnames(units.gut)
    
    # calculate "UnitShape" area and perimeter stats (if column exists in layer)
    if("UnitShape" %in% units.cols){
      
      units.gut = units.gut %>% filter(!is.na(UnitShape))
      
      shape.count = units.gut %>% st_drop_geometry() %>%
        group_by(UnitShape) %>%
        summarise(n = n()) 
      
      shape.metrics = units.gut %>% st_drop_geometry() %>% 
        dplyr::select(UnitShape, area, perim) %>%
        gather(key = variable, value = value, area:perim) %>%
        group_by(UnitShape, variable) %>%
        summarize(med = median(value, na.rm = TRUE),
                  mean = mean(value, na.rm = TRUE),
                  sd = sd(value, na.rm = TRUE),
                  sum = sum(value, na.rm = TRUE)) %>%
        gather(key = stat, value = value, med:sum) %>%
        mutate(value = round(value, 3)) %>%
        unite("variable.stat", c("variable", "stat"), sep = ".", remove = TRUE) %>%
        spread(variable.stat, value) %>%
        mutate(area.ratio = round((area.sum / total.area) , 3),
               perim.area.ratio = round((perim.mean / area.mean), 3),
               gut.layer = "UnitShape") %>%
        left_join(shape.count, by = "UnitShape") %>%
        rename(unit.type = UnitShape) %>%
        dplyr::select(gut.layer, unit.type, n, everything()) %>%
        ungroup() %>%
        mutate(unit.type = as.character(unit.type))
      
      tb.metrics = tb.metrics %>% bind_rows(shape.metrics)
    }
    
    # calculate "UnitForm" area and perimeter stats (if column exists in layer)
    if("UnitForm" %in% units.cols){
      
      units.gut = units.gut %>% filter(!is.na(UnitForm))
      
      form.count = units.gut %>% st_drop_geometry() %>%
        group_by(UnitForm) %>%
        summarise(n = n()) 
      
      form.metrics = units.gut %>% st_drop_geometry() %>% 
        dplyr::select(UnitForm, area, perim) %>%
        gather(key = variable, value = value, area:perim) %>%
        group_by(UnitForm, variable) %>%
        summarize(med = median(value, na.rm = TRUE),
                  mean = mean(value, na.rm = TRUE),
                  sd = sd(value, na.rm = TRUE),
                  sum = sum(value, na.rm = TRUE)) %>%
        gather(key = stat, value = value, med:sum) %>%
        mutate(value = round(value, 3)) %>%
        unite("variable.stat", c("variable", "stat"), sep = ".", remove = TRUE) %>%
        spread(variable.stat, value) %>%
        mutate(area.ratio = round((area.sum / total.area) , 3),
               perim.area.ratio = round((perim.mean / area.mean), 3),
               gut.layer = "UnitForm") %>%
        left_join(form.count, by = "UnitForm") %>%
        rename(unit.type = UnitForm) %>%
        dplyr::select(gut.layer, unit.type, n, everything()) %>%
        ungroup() %>%
        mutate(unit.type = as.character(unit.type)) 
      
      tb.metrics = tb.metrics %>% bind_rows(form.metrics)
    }

    # calculate "GU" area and perimeter stats (if column exists in layer)
    if("GU" %in% units.cols){
      
      units.gut = units.gut %>% filter(!is.na(GU))
      
      gu.count = units.gut %>% st_drop_geometry() %>%
        group_by(GU) %>%
        summarise(n = n()) 
      
      gu.metrics = units.gut %>% st_drop_geometry() %>% 
        dplyr::select(GU, area, perim) %>%
        gather(key = variable, value = value, area:perim) %>%
        group_by(GU, variable) %>%
        summarize(med = median(value, na.rm = TRUE),
                  mean = mean(value, na.rm = TRUE),
                  sd = sd(value, na.rm = TRUE),
                  sum = sum(value, na.rm = TRUE)) %>%
        gather(key = stat, value = value, med:sum) %>%
        mutate(value = round(value, 3)) %>%
        unite("variable.stat", c("variable", "stat"), sep = ".", remove = TRUE) %>%
        spread(variable.stat, value) %>%
        mutate(area.ratio = round((area.sum / total.area) , 3),
               perim.area.ratio = round((perim.mean / area.mean), 3),
               gut.layer = "GU") %>%
        left_join(gu.count, by = "GU") %>%
        rename(unit.type = GU) %>%
        dplyr::select(gut.layer, unit.type, n, everything()) %>%
        ungroup() %>%
        mutate(unit.type = as.character(unit.type)) 
      
      tb.metrics = tb.metrics %>% bind_rows(gu.metrics)
    }
      
  }else{
    print(paste(gut.layer, ": shapefile doesn't exist", sep = ""))
  }
  
  tb.metrics = tb.metrics %>% mutate(visit.id = visit.id) %>% dplyr::select(visit.id, everything())
  
  return(tb.metrics) 
  
}
