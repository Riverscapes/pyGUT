#This script compiles your data and calls the other scripts.


#######################################################
#Set your Local paths and user defined variables
#######################################################

#set your local working directory:
localdir='E:\\GitHub\\PyGUT'

#folder where all the data is contained
Datapath=paste(localdir,"ExampleData\\VisitData",sep="\\")

#folder where you want your output summary data to go
Metricpath=paste(localdir,"ExampleData\\Metrics",sep="\\")

#folder containing the scripts which run the summaries
Scriptpath=paste(localdir,"SupportingTools\\Rscripts\\OverlaySummary", sep="\\")

#folder where you want any output figures to go
figdir=paste(localdir, "ExampleData\\Figures", sep="\\")

#Some local variables to set
Run="Run_01"  #Specify selection criteria for which GUT run(s) you want to summarize.
layer="Tier3_InChannel_GU" #Specify which GUT output layer you want to summarize 
attribute="GU" #Specify the field name of the GUT field name you are wanting to summarize over
overlaydir="NREI" #the following code is sensitive and needs the GUT directory to be at the same level as the NREI directory.
overlay="predFishLocations.shp" #should be located within the overly directory specified without subfolders
####DONE WITH USER DEFINED VARIABLES#############

#######################
##specify list of visits with overlay files
#########################

#list of directories of all the overly data you want to summarize by geomorphic unit 
#Further lines could be added to remove different run outputs from the list.  The code will summarize over this list, so make sure it is what you want.

Fishrunlist=paste(list.dirs(Datapath)[grep(paste("/",overlaydir,sep=""),list.dirs(Datapath))], overlay, sep="/")

##############################
#Extract ID from path--- READ THIS!!!!
##############################
#IMPORTANT-- all these scripts rely on generating a VISIT_ID field so that you can identify which site visits go with 
#each line in the summary files.  extractIDfrompath.R contains a coustom function, extractvisitfrompath(), that will pull the visit number 
#out of a path, BUT it is dependent on the file naming scheme to have VISIT_##.  If your naming scheme is something different then you will want
#to revise the following script or add a new function so that it will return your unique ID number (an ONLY the number) 
#from a given filepath.  Alternatively you could rename your folders to follow the naming scheme. 
#All scripts source this file on the fly so as long as you have it in the same folder as this script it 
#should be able to find it and source it and you can leave the line below commented out.

source(paste(Scriptpath, "extractIDfrompath.R", sep="/"))

#######################################################################
#Specify/customize universal colors and complete assemblage of geomorphic names
#if you picked a field name OTHER than Unitform or GU, you will need to define the categories and colors yourself
#similarly to what was done below for Unitform (Tier 2 form output) and GU (Tier 3 output) below.
#######################################################################

if(length(grep("Tier2",layer))>0 | attribute=="UnitForm"){

unitcats=c("Saddle", "Bowl","Mound","Plane", "Trough", 
           "Bowl Transition", "Mound Transition")

unitcolors=c(Bowl="royalblue",Mound="darkred",Plane="khaki1",Saddle="orange2",Trough="lightblue",Wall= "grey10",
              `Bowl Transition`="aquamarine", `Mound Transition`="pink")

}

if(length(grep("Tier3",layer))>0 | attribute=="GU"){
unitcats=c("Pocket Pool", "Pool", "Pond", "Margin Attached Bar", "Mid Channel Bar" ,
              "Riffle", "Cascade", "Rapid", "Run-Glide", "Chute", "Transition", "Bank")
unitcolors=c(`Pocket Pool`="light blue", Pool="royalblue", Pond="dark green", `Margin Attached Bar`="darkred", `Mid Channel Bar`="brown2" , 
                        Riffle="orange2", Cascade="pink", Rapid="green", Chute="aquamarine" ,
                        `Glide-Run`="khaki1", Transition="grey90", Bank="grey10")
}

#############################################################
#Create Maps of GUT output
#############################################################
source(paste(Scriptpath, "/makeGUToverlaymaps.R", sep="")) 

#you have to be connected to the internet for this to work due to a package dependency.  Sorry.
for (i in c(1:length(Fishrunlist))){
  print(paste("i=",i, "starting", Fishrunlist[i]))
  makeGUToverlaymaps(Fishrunlist[i],overlaydir=overlaydir, overlayname="predicted Juveniles", layer, figdir, Run, plotthalweg=F, plotthalwegs=F, plotcontour=F)
}
