#Extracts visit from CHaMP filepath. visit folder must be of the form "VISIT_#"

extractvisitfrompath=function(path){
  split_path <- function(path) {
    if (dirname(path) %in% c(".", path)) return(basename(path))
    return(c(basename(path), split_path(dirname(path))))
  }
  visit=split_path(path)[grep("VISIT", split_path(path))]
  visit2=round(as.numeric(strsplit(visit,"_")[[1]][2]),0)
  
  return(visit2)
}