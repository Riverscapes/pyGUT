#This script Makes map of GUT output whith fish pts plotted on top"
# data = visit.summary %>% slice(1)
# visit.dir = visit.summary %>% slice(1) %>% dplyr::select(visit.dir) %>% as.character()
# run.dir = "GUT_2.1/Run_01"
# layer = "Tier2_InChannel_Transition"


make.gut.maps = function(data, gut.run, fig.path){
  
  # get visit id from visit directory
  visit.dir = data %>% dplyr::select(visit.dir) %>% as.character()
  visit.id = as.numeric(unlist(str_split(data$visit.dir, "VISIT_"))[2])
  
  # set gut form and gu colors
  form.fill = c('Bowl' = '#004DA8', 'Bowl Transition' = '#00A9E6', 'Trough' = '#73DFFF', 'Plane' = '#E6E600', 
    'Mound Transition' = '#FF7F7F', 'Saddle' = '#E69800', 'Mound' = '#A80000', 'Wall' = '#000000')
  
  gu.fill = c('Bank' = '#000000', 'Pool' = '#004DA8', 'Pond' = '#0070FF', 'Pocket Pool' = '#73B2FF', 'Chute' = '#73FFDF', 
             'Rapid' = '#66CDAB', 'Cascade' = '#448970', 'Glide-Run' = '#E6E600', 'Riffle' = '#E69800', 'Step' = '#D7B09E', 
             'Mid Channel Bar' = '#895A44', 'Margin Attached Bar' = '#A80000', 'Transition' = '#CCCCCC')
  
  # read in contour polylines
  contours.file = unlist(list.files(path = visit.dir, pattern = "DEM_Contours.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(length(contours.file) > 0){contours = st_read(contours.file, quiet = TRUE, stringsAsFactors = FALSE)}
  
  # read in thalweg polylines
  thalwegs.file = unlist(list.files(path = visit.dir, pattern = "^Thalwegs.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  thalweg.file = unlist(list.files(path = visit.dir, pattern = "^Thalweg.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(length(thalwegs.file) > 0){
    thalwegs = st_read(thalwegs.file, quiet = TRUE, stringsAsFactors = FALSE)
  }else{
    thalwegs = st_read(thalweg.file, quiet = TRUE, stringsAsFactors = FALSE)
  }

  # read in tier 2 form polygons !! todo: change to include run
  t2.files = unlist(list.files(path = visit.dir, pattern = "^Tier2_InChannel_Transition.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))[1]
  t2.file = grep(gut.run, t2.files, value = TRUE)
  if(length(t2.file) > 0){forms = st_read(t2.file, quiet = TRUE, stringsAsFactors = FALSE)}  
  
  # read in tier 3 gu polygons !! todo: change to include run
  t3.files = unlist(list.files(path = visit.dir, pattern = "^Tier3_InChannel_GU.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))[1]
  t3.file = grep(gut.run, t3.files, value = TRUE)
  if(length(t3.file) > 0){gus = st_read(t3.file, quiet = TRUE, stringsAsFactors = FALSE)}  
  
  # read in nrei fish points
  nrei.locs.file = unlist(list.files(path = visit.dir, pattern = "^NREI_FishLocs.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(length(nrei.locs.file) > 0){nrei.fish = st_read(nrei.locs.file, quiet = TRUE, stringsAsFactors = FALSE)}
  
  # read in nrei extent (todo: check is okay to read in delft extent since have on hand)
  nrei.extent.file = unlist(list.files(path = visit.dir, pattern = "^Delft_Extent.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(length(nrei.extent.file) > 0){nrei.extent = st_read(nrei.extent.file, quiet = TRUE, stringsAsFactors = FALSE)}
  
  # # check if nrei points and extent exist
  # if(exists("nrei.extent") & exists("nrei.fish"))
  
  # plot tier 2 form maps
  if("sf" %in% class(forms)){
    
    # determine plotting orientation
    xy.ratio = (as.numeric(st_bbox(forms)$xmax) - as.numeric(st_bbox(forms)$xmin)) / (as.numeric(st_bbox(forms)$ymax) - as.numeric(st_bbox(forms)$ymin))
    if(xy.ratio < 1){
      plot.ncol = 2
      plot.nrow = 1
      plot.align = "v"
    }else{
      plot.ncol = 1
      plot.nrow = 2
      plot.align = "h"
    }
    
    map.forms = ggplot() +
      geom_sf(data = contours, aes(color = "A"), show.legend = "line") +
      geom_sf(data = forms, aes(fill = forms$UnitForm), color = NA, alpha = 0.5) +
      geom_sf(data = thalwegs, aes(colour = "B"), linetype = 2, size = 0.6, show.legend = "line") +
      scale_fill_manual(name = "Unit Form", values = form.fill,
                        guide = guide_legend(override.aes = list(linetype = "blank", shape = NA))) +
      scale_colour_manual(values = c("A" = "darkgrey", "B" = "blue"),
                          labels = c("Contours", "Thalweg"),
                          name = NULL,
                          guide = guide_legend(override.aes = list(linetype = c("solid", "dashed"), shape = c(NA, NA)))) +
      # xlab("Longitude") + ylab("Latitude") +
      # annotation_scale(width_hint = 0.5) +
      # theme_light()
      # annotation_north_arrow(location = "bl", style = north_arrow_fancy_orienteering) +
      annotation_scale(location = "bl", width_hint = 0.5, bar_cols = c("grey37", "white"), line_col = "grey37", text_col = "grey37") +
      theme_void()
    
    if(all("sf" %in% class(nrei.fish), "sf" %in% class(nrei.extent))){
      map.forms.nrei = ggplot() +
        geom_sf(data = contours, aes(color = "A"), show.legend = "line") +
        geom_sf(data = forms, aes(fill = forms$UnitForm), color = NA, alpha = 0.5) +
        geom_sf(data = nrei.fish, aes(colour = "B"), shape = 1, show.legend = "point") +
        geom_sf(data = nrei.extent, aes(colour = "C", fill = NA), linetype = 2, show.legend = "line") +
        scale_fill_manual(name = "Unit Form", values = form.fill,
                          guide = guide_legend(override.aes = list(linetype = "blank", shape = NA))) +
        scale_colour_manual(values = c("A" = "darkgrey", "B" = "magenta4", "C" = "magenta4"),
                            labels = c("Contours", "NREI Predicted Fish", "NREI Extent"),
                            name = NULL,
                            guide = guide_legend(override.aes = list(linetype = c("solid", "blank", "dashed"), shape = c(NA, 1, NA)))) +
        annotation_scale(location = "bl", width_hint = 0.5, bar_cols = c("grey37", "white"), line_col = "grey37", text_col = "grey37") +
        theme_void()
    }else{
      map.forms.nrei = map.forms
    }
    
    # arrange and save plot output
    forms.title = paste("Visit", as.character(visit.id), "Tier 2 Unit Form", sep = " ")
    out.name = paste("Visit_", as.character(visit.id), "_Tier2_UnitForm_Map.png", sep = "")
    ggarrange(map.forms, map.forms.nrei, ncol = plot.ncol, nrow = plot.nrow, align = plot.align) %>% 
      ggexport(filename = file.path(fig.path, out.name), width = 6000, height = 6000, res = 500)
    
    # map.forms.out = ggarrange(map.forms, map.forms.nrei, ncol = plot.ncol, nrow = plot.nrow, align = plot.align) %>% 
    #   annotate_figure(fig.lab = forms.title, fig.lab.face = "bold")
  }
  

  if("sf" %in% class(gus)){
    
    # determine plotting orientation
    xy.ratio = (as.numeric(st_bbox(gus)$xmax) - as.numeric(st_bbox(gus)$xmin)) / (as.numeric(st_bbox(gus)$ymax) - as.numeric(st_bbox(gus)$ymin))
    if(xy.ratio < 1){
      plot.ncol = 2
      plot.nrow = 1
      plot.align = "v"
    }else{
      plot.ncol = 1
      plot.nrow = 2
      plot.align = "h"
    }
    
    # plot tier 3 maps GU maps
    map.gus = ggplot() +
      geom_sf(data = contours, aes(color = "A"), show.legend = "line") +
      geom_sf(data = gus, aes(fill = gus$GU), color = NA, alpha = 0.5) +
      geom_sf(data = thalwegs, aes(colour = "B"), linetype = 2, size = 0.6, show.legend = "line") +
      scale_fill_manual(name = "GU", values = gu.fill,
                        guide = guide_legend(override.aes = list(linetype = "blank", shape = NA))) +
      scale_colour_manual(values = c("A" = "darkgrey", "B" = "blue"),
                          labels = c("Contours", "Thalweg"),
                          name = NULL,
                          guide = guide_legend(override.aes = list(linetype = c("solid", "dashed"), shape = c(NA, NA)))) +
      annotation_scale(location = "bl", width_hint = 0.5, bar_cols = c("grey37", "white"), line_col = "grey37", text_col = "grey37") +
      theme_void()
    
    if(all("sf" %in% class(nrei.fish), "sf" %in% class(nrei.extent))){
      map.gus.nrei = ggplot() +
        geom_sf(data = contours, aes(color = "A"), show.legend = "line") +
        geom_sf(data = gus, aes(fill = gus$GU), color = NA, alpha = 0.5) +
        geom_sf(data = nrei.fish, aes(colour = "B"), shape = 1, show.legend = "point") +
        geom_sf(data = nrei.extent, aes(colour = "C", fill = NA), linetype = 2, show.legend = "line") +
        scale_fill_manual(name = "GU", values = gu.fill,
                          guide = guide_legend(override.aes = list(linetype = "blank", shape = NA))) +
        scale_colour_manual(values = c("A" = "darkgrey", "B" = "magenta4", "C" = "magenta4"),
                            labels = c("Contours", "NREI Predicted Fish", "NREI Extent"),
                            name = NULL,
                            guide = guide_legend(override.aes = list(linetype = c("solid", "blank", "dashed"), shape = c(NA, 1, NA)))) +
        annotation_scale(location = "bl", width_hint = 0.5, bar_cols = c("grey37", "white"), line_col = "grey37", text_col = "grey37") +
        theme_void()
    }else{
      map.gus.nrei = map.gus
    }
    
    # arrange and save plot output
    gu.title = paste("Visit", as.character(visit.id), "Tier 3 GU", sep = " ")
    out.name = paste("Visit_", as.character(visit.id), "_Tier3_GU_Map.png", sep = "")
    ggarrange(map.gus, map.gus.nrei, ncol = plot.ncol, nrow = plot.nrow, align = plot.align) %>% 
      ggexport(filename = file.path(fig.path, out.name), width = 6000, height = 6000, res = 500)
  }
  
}