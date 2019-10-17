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

  # read in tier 2 form polygons
  t2.files = unlist(list.files(path = visit.dir, pattern = "^Tier2_InChannel.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  t2.file = grep(gut.run, t2.files, value = TRUE)
  if(length(t2.file) > 0){forms = st_read(t2.file, quiet = TRUE, stringsAsFactors = FALSE)}  
  
  # read in tier 3 gu polygons
  t3.files = unlist(list.files(path = visit.dir, pattern = "^Tier3_InChannel_GU.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  t3.file = grep(gut.run, t3.files, value = TRUE)
  if(length(t3.file) > 0){gus = st_read(t3.file, quiet = TRUE, stringsAsFactors = FALSE)}  
  
  # read in nrei fish points (juvenile steelhead) and nrei modeled extent
  nrei.locs.file = unlist(list.files(path = visit.dir, pattern = "^NREI_FishLocs.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(length(nrei.locs.file) > 0){nrei.fish = st_read(nrei.locs.file, quiet = TRUE, stringsAsFactors = FALSE)}else{nrei.fish = NA}
  
  nrei.extent.file = unlist(list.files(path = visit.dir, pattern = "^Delft_Extent.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(length(nrei.extent.file) > 0){nrei.extent = st_read(nrei.extent.file, quiet = TRUE, stringsAsFactors = FALSE)}else{nrei.extent = NA}
  
  # read in steelhead redd points and fuzzy modeled extent
  st.redd.locs.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_ReddLocs_Steelhead.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(length(st.redd.locs.file) > 0){st.redds = st_read(st.redd.locs.file, quiet = TRUE, stringsAsFactors = FALSE)}else{st.redds = NA}
  
  st.extent.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_Steelhead_Extent.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(length(st.extent.file) > 0){st.extent = st_read(st.extent.file, quiet = TRUE, stringsAsFactors = FALSE)}else{st.extent = NA}
  
  # read in chinook redd points and fuzzy modeled extent
  ch.redd.locs.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_ReddLocs_Chinook.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(length(ch.redd.locs.file) > 0){ch.redds = st_read(ch.redd.locs.file, quiet = TRUE, stringsAsFactors = FALSE)}else{ch.redds = NA}
  
  ch.extent.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_Chinook_Extent.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(length(ch.extent.file) > 0){ch.extent = st_read(ch.extent.file, quiet = TRUE, stringsAsFactors = FALSE)}else{ch.extent = NA}
  
  # read in chinook juvenile fish points and fuzzy modeled extent
  ch.juv.locs.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_JuvenileLocs_Chinook.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(length(ch.juv.locs.file) > 0){ch.juv = st_read(ch.juv.locs.file, quiet = TRUE, stringsAsFactors = FALSE)}else{ch.juv = NA}
  
  ch.juv.extent.file = unlist(list.files(path = visit.dir, pattern = "^Fuzzy_Chinook_Juvenile_Extent.shp$", full.names = TRUE, recursive = TRUE, include.dirs = FALSE))
  if(length(ch.juv.extent.file) > 0){ch.juv.extent = st_read(ch.juv.extent.file, quiet = TRUE, stringsAsFactors = FALSE)}else{ch.juv.extent = NA}
  
  
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
    
    # -- tier 2 forms plot
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
      theme_void() +
      ggtitle('Tier 2 Unit Form')
    
    # -- nrei steelhead juvenile predicted fish locations plot
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
        theme_void() +
        ggtitle('NREI Predicted Steelhead Juvenile Locations') 
    }else{
      map.forms.nrei = map.forms + 
        ggtitle('NREI Predicted Steelhead Juvenile Locations') 
    }
    
    # arrange and save plot output
    forms.title = paste("Visit", as.character(visit.id), "Tier 2 Unit Form", sep = " ")
    out.name = paste("Visit_", as.character(visit.id), "_Tier2_Steelhead_Juvenile_Map.png", sep = "")
    ggarrange(map.forms, map.forms.nrei, ncol = plot.ncol, nrow = plot.nrow, align = plot.align, common.legend = FALSE, legend = "right") %>% 
      ggexport(filename = file.path(fig.path, out.name), width = 6000, height = 6000, res = 500)
    
    # map.forms.out = ggarrange(map.forms, map.forms.nrei, ncol = plot.ncol, nrow = plot.nrow, align = plot.align) %>% 
    #   annotate_figure(fig.lab = forms.title, fig.lab.face = "bold")
    
    # -- fuzzy steelhead predicted redd locations plot
    if(all("sf" %in% class(st.redds), "sf" %in% class(st.extent))){
      map.forms.st.redds = ggplot() +
        geom_sf(data = contours, aes(color = "A"), show.legend = "line") +
        geom_sf(data = forms, aes(fill = forms$UnitForm), color = NA, alpha = 0.5) +
        geom_sf(data = st.redds, aes(colour = "B"), shape = 1, show.legend = "point") +
        geom_sf(data = st.extent, aes(colour = "C", fill = NA), linetype = 2, show.legend = "line") +
        scale_fill_manual(name = "Unit Form", values = form.fill,
                          guide = guide_legend(override.aes = list(linetype = "blank", shape = NA))) +
        scale_colour_manual(values = c("A" = "darkgrey", "B" = "magenta4", "C" = "magenta4"),
                            labels = c("Contours", "Fuzzy Predicted Redds", "Fuzzy Extent"),
                            name = NULL,
                            guide = guide_legend(override.aes = list(linetype = c("solid", "blank", "dashed"), shape = c(NA, 1, NA)))) +
        annotation_scale(location = "bl", width_hint = 0.5, bar_cols = c("grey37", "white"), line_col = "grey37", text_col = "grey37") +
        theme_void() +
        ggtitle('Fuzzy Predicted Steelhead Redd Locations') 
    }else{
      map.forms.st.redds = map.forms + 
        ggtitle('Fuzzy Predicted Steelhead Redd Locations') 
    }
    
    # arrange and save plot output
    out.name = paste("Visit_", as.character(visit.id), "_Tier2_Steelhead_Redd_Map.png", sep = "")
    ggarrange(map.forms, map.forms.st.redds, ncol = plot.ncol, nrow = plot.nrow, align = plot.align, common.legend = FALSE, legend = "right") %>% 
      ggexport(filename = file.path(fig.path, out.name), width = 6000, height = 6000, res = 500)
    
    # -- fuzzy chinook predicted juvenile locations plot
    if(all("sf" %in% class(ch.juv), "sf" %in% class(ch.juv.extent))){
      map.forms.ch.juv = ggplot() +
        geom_sf(data = contours, aes(color = "A"), show.legend = "line") +
        geom_sf(data = forms, aes(fill = forms$UnitForm), color = NA, alpha = 0.5) +
        geom_sf(data = ch.juv, aes(colour = "B"), shape = 1, show.legend = "point") +
        geom_sf(data = ch.juv.extent, aes(colour = "C", fill = NA), linetype = 2, show.legend = "line") +
        scale_fill_manual(name = "Unit Form", values = form.fill,
                          guide = guide_legend(override.aes = list(linetype = "blank", shape = NA))) +
        scale_colour_manual(values = c("A" = "darkgrey", "B" = "magenta4", "C" = "magenta4"),
                            labels = c("Contours", "Fuzzy Predicted Fish", "Fuzzy Extent"),
                            name = NULL,
                            guide = guide_legend(override.aes = list(linetype = c("solid", "blank", "dashed"), shape = c(NA, 1, NA)))) +
        annotation_scale(location = "bl", width_hint = 0.5, bar_cols = c("grey37", "white"), line_col = "grey37", text_col = "grey37") +
        theme_void() +
        ggtitle('Fuzzy Predicted Chinook Juvenile Locations') 
    }else{
      map.forms.ch.juv = map.forms + 
        ggtitle('Fuzzy Predicted Chinook Juvenile Locations')  
    }
    
    # arrange and save plot output
    out.name = paste("Visit_", as.character(visit.id), "_Tier2_Chinook_Juvenile_Map.png", sep = "")
    ggarrange(map.forms, map.forms.ch.juv, ncol = plot.ncol, nrow = plot.nrow, align = plot.align, common.legend = FALSE, legend = "right") %>% 
      ggexport(filename = file.path(fig.path, out.name), width = 6000, height = 6000, res = 500)
    
    
    # -- fuzzy chinook predicted redd locations plot
    if(all("sf" %in% class(ch.redds), "sf" %in% class(ch.extent))){
      map.forms.ch.redds = ggplot() +
        geom_sf(data = contours, aes(color = "A"), show.legend = "line") +
        geom_sf(data = forms, aes(fill = forms$UnitForm), color = NA, alpha = 0.5) +
        geom_sf(data = ch.redds, aes(colour = "B"), shape = 1, show.legend = "point") +
        geom_sf(data = ch.extent, aes(colour = "C", fill = NA), linetype = 2, show.legend = "line") +
        scale_fill_manual(name = "Unit Form", values = form.fill,
                          guide = guide_legend(override.aes = list(linetype = "blank", shape = NA))) +
        scale_colour_manual(values = c("A" = "darkgrey", "B" = "magenta4", "C" = "magenta4"),
                            labels = c("Contours", "Fuzzy Predicted Redds", "Fuzzy Extent"),
                            name = NULL,
                            guide = guide_legend(override.aes = list(linetype = c("solid", "blank", "dashed"), shape = c(NA, 1, NA)))) +
        annotation_scale(location = "bl", width_hint = 0.5, bar_cols = c("grey37", "white"), line_col = "grey37", text_col = "grey37") +
        theme_void() +
        ggtitle('Fuzzy Predicted Chinook Redd Locations') 
    }else{
      map.forms.ch.redds = map.forms + 
        ggtitle('Fuzzy Predicted Chinook Redd Locations') 
    }
    
    # arrange and save plot output
    out.name = paste("Visit_", as.character(visit.id), "_Tier2_Chinook_Redd_Map.png", sep = "")
    ggarrange(map.forms, map.forms.ch.redds, ncol = plot.ncol, nrow = plot.nrow, align = plot.align, common.legend = FALSE, legend = "right") %>% 
      ggexport(filename = file.path(fig.path, out.name), width = 6000, height = 6000, res = 500)
    
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
      theme_void() +
      ggtitle('Tier 3 Geomorphic Unit')
    
    # -- nrei steelhead juvenile predicted fish locations plot
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
        theme_void() +
        ggtitle('NREI Predicted Steelhead Juvenile Locations') 
    }else{
      map.gus.nrei = map.gus +
        ggtitle('NREI Predicted Steelhead Juvenile Locations') 
    }
    
    # arrange and save plot output
    gu.title = paste("Visit", as.character(visit.id), "Tier 3 GU", sep = " ")
    out.name = paste("Visit_", as.character(visit.id), "_Tier3_Steelhead_Juvenile_Map.png", sep = "")
    ggarrange(map.gus, map.gus.nrei, ncol = plot.ncol, nrow = plot.nrow, align = plot.align) %>% 
      ggexport(filename = file.path(fig.path, out.name), width = 6000, height = 6000, res = 500)
    
    # -- fuzzy steelhead predicted redd locations plot
    if(all("sf" %in% class(st.redds), "sf" %in% class(st.extent))){
      map.gus.st.redds = ggplot() +
        geom_sf(data = contours, aes(color = "A"), show.legend = "line") +
        geom_sf(data = gus, aes(fill = gus$GU), color = NA, alpha = 0.5) +
        geom_sf(data = st.redds, aes(colour = "B"), shape = 1, show.legend = "point") +
        geom_sf(data = st.extent, aes(colour = "C", fill = NA), linetype = 2, show.legend = "line") +
        scale_fill_manual(name = "GU", values = gu.fill,
                          guide = guide_legend(override.aes = list(linetype = "blank", shape = NA))) +
        scale_colour_manual(values = c("A" = "darkgrey", "B" = "magenta4", "C" = "magenta4"),
                            labels = c("Contours", "Fuzzy Predicted Redds", "Fuzzy Extent"),
                            name = NULL,
                            guide = guide_legend(override.aes = list(linetype = c("solid", "blank", "dashed"), shape = c(NA, 1, NA)))) +
        annotation_scale(location = "bl", width_hint = 0.5, bar_cols = c("grey37", "white"), line_col = "grey37", text_col = "grey37") +
        theme_void() +
        ggtitle('Fuzzy Predicted Steelhead Redd Locations') 
    }else{
      map.gus.st.redds = map.gus +
        ggtitle('Fuzzy Predicted Steelhead Redd Locations') 
    }
    
    # arrange and save plot output
    out.name = paste("Visit_", as.character(visit.id), "_Tier3_Steelhead_Redd_Map.png", sep = "")
    ggarrange(map.gus, map.gus.st.redds, ncol = plot.ncol, nrow = plot.nrow, align = plot.align) %>% 
      ggexport(filename = file.path(fig.path, out.name), width = 6000, height = 6000, res = 500)
    
    # -- fuzzy chinook predicted juvenile locations plot
    if(all("sf" %in% class(ch.juv), "sf" %in% class(ch.juv.extent))){
      map.gus.ch.juv = ggplot() +
        geom_sf(data = contours, aes(color = "A"), show.legend = "line") +
        geom_sf(data = gus, aes(fill = gus$GU), color = NA, alpha = 0.5) +
        geom_sf(data = ch.juv, aes(colour = "B"), shape = 1, show.legend = "point") +
        geom_sf(data = ch.juv.extent, aes(colour = "C", fill = NA), linetype = 2, show.legend = "line") +
        scale_fill_manual(name = "GU", values = gu.fill,
                          guide = guide_legend(override.aes = list(linetype = "blank", shape = NA))) +
        scale_colour_manual(values = c("A" = "darkgrey", "B" = "magenta4", "C" = "magenta4"),
                            labels = c("Contours", "Fuzzy Predicted Fish", "Fuzzy Extent"),
                            name = NULL,
                            guide = guide_legend(override.aes = list(linetype = c("solid", "blank", "dashed"), shape = c(NA, 1, NA)))) +
        annotation_scale(location = "bl", width_hint = 0.5, bar_cols = c("grey37", "white"), line_col = "grey37", text_col = "grey37") +
        theme_void() +
        ggtitle('Fuzzy Predicted Chinook Juvenile Locations')  
    }else{
      map.gus.ch.juv = map.gus +
        ggtitle('Fuzzy Predicted Chinook Juvenile Locations')  
    }
    
    # arrange and save plot output
    out.name = paste("Visit_", as.character(visit.id), "_Tier3_Chinook_Juvenile_Map.png", sep = "")
    ggarrange(map.gus, map.gus.ch.juv, ncol = plot.ncol, nrow = plot.nrow, align = plot.align) %>% 
      ggexport(filename = file.path(fig.path, out.name), width = 6000, height = 6000, res = 500)
    
    # -- fuzzy chinook predicted redd locations plot
    if(all("sf" %in% class(ch.redds), "sf" %in% class(ch.extent))){
      map.gus.ch.redds = ggplot() +
        geom_sf(data = contours, aes(color = "A"), show.legend = "line") +
        geom_sf(data = gus, aes(fill = gus$GU), color = NA, alpha = 0.5) +
        geom_sf(data = ch.redds, aes(colour = "B"), shape = 1, show.legend = "point") +
        geom_sf(data = ch.extent, aes(colour = "C", fill = NA), linetype = 2, show.legend = "line") +
        scale_fill_manual(name = "GU", values = gu.fill,
                          guide = guide_legend(override.aes = list(linetype = "blank", shape = NA))) +
        scale_colour_manual(values = c("A" = "darkgrey", "B" = "magenta4", "C" = "magenta4"),
                            labels = c("Contours", "Fuzzy Predicted Redds", "Fuzzy Extent"),
                            name = NULL,
                            guide = guide_legend(override.aes = list(linetype = c("solid", "blank", "dashed"), shape = c(NA, 1, NA)))) +
        annotation_scale(location = "bl", width_hint = 0.5, bar_cols = c("grey37", "white"), line_col = "grey37", text_col = "grey37") +
        theme_void() +
        ggtitle('Fuzzy Predicted Chinook Redd Locations') 
    }else{
      map.gus.ch.redds = map.gus +
        ggtitle('Fuzzy Predicted Chinook Redd Locations')  
    }
    
    # arrange and save plot output
    out.name = paste("Visit_", as.character(visit.id), "_Tier3_Chinook_Redd_Map.png", sep = "")
    ggarrange(map.gus, map.gus.ch.redds, ncol = plot.ncol, nrow = plot.nrow, align = plot.align) %>% 
      ggexport(filename = file.path(fig.path, out.name), width = 6000, height = 6000, res = 500)
  }
  
}