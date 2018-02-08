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
Scriptpath=paste(localdir,"SupportingTools\\Rscripts\\GU_summary", sep="\\")

#folder where you want any output figures to go
figdir=paste(localdir, "ExampleData\\Figures", sep="\\")

#Some local variables to set
Run="Run_01"  #Specify selection criteria for which GUT run(s) you want to summarize.
layer="Tier2_InChannel_Transition" #Specify which GUT output layer you want to summarize 
attribute="UnitForm" #Specify the field name of the GUT field name you are wanting to summarize over

####DONE WITH USER DEFINED VARIABLES#############

#######################
#Make GUT run summary list
#########################

#list of directories of all the GUT runs you want to summarize by searching for a specific run or runs. 
#Further lines could be added to remove different run outputs from the list.  The code will summarize over this list, so make sure it is what you want.


GUTrunlist=list.dirs(Datapath)[grep(Run,list.dirs(Datapath))] 

#check to see if your list contains all the GUT runs you want to summarize
GUTrunlist


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

#source(paste(Scriptpath, "extractIDfrompath.R", sep="/"))

#######################################################################
#Specify/customize universal colors and complete assemblage of geomorphic names
#if you picked a field name OTHER than Unitform or GU, you will need to define the categories and colors yourself
#similarly to what was done below for Unitform (Tier 2 form output) and GU (Tier 3 output) below.
#######################################################################

if(length(grep("Tier2",layer))>0 | attribute=="Unitform"){

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
source(paste(Scriptpath, "/makeGUTmaps.R", sep="")) 

#you have to be connected to the internet for this to work due to a package dependency.  Sorry.
for (i in c(1:length(GUTrunlist))){
  print(paste("i=",i, "starting", GUTrunlist[i]))
  makeGUTmaps(GUTrunlist[i], layer, figdir, Run, plotthalweg=T, plotthalwegs=T, plotcontour=T)
}

#################################################################
#GU Metrics
#Summarizes Geomorphic Units
#see makesiteGUTunitmetrics.R for details, this just loops these scripts over all your runs
#################################################################

source(paste(Scriptpath, "/makeGUmetrics.R", sep=""))

for (i in c(1:length(GUTrunlist))){
  print(paste("i=",i, "starting", GUTrunlist[i]))
  v=makeGUmetrics(GUTrunlist[i], layer, attribute=attribute, unitcats=unitcats)
  if (i==1){metrics=v} else {metrics=rbind(metrics,v)} 
} 

#cleans up data a little bit before export
metrics2=as.data.frame(metrics)
if((length(grep("exist", metrics2$Unit))>0)==T){metrics2[-grep("exist", metrics2$Unit),]} #cleans out lines printing that they didn't exist
if(length(which(metrics2$n==1))>0){
  metrics2[which(metrics2$n==1),]$sdArea=0 #sets sd to zero for items with only one value
  metrics2[which(metrics2$n==1),]$sdPerim=0 #sets sd to zero for items with only one value
}
metrics2
write.csv(metrics2, paste(Metricpath, "\\GUmetrics_", Run, "_", layer, ".csv" ,sep=""), row.names=F)


##########################################################################################################
#Site Metrics.  
#Summarizes site complexity.
#see makesiteGUTmetrics.R and intersectpts.R for details, this just loops these scripts over all your runs
#########################################################################################################
source(paste(Scriptpath, "/makesitemetrics.R", sep=""))
source(paste(Scriptpath, "/intersectpts.R", sep="")) 

#you have to be connected to the internet for this to work due to a package dependency.  Sorry.
for (i in c(1:length(GUTrunlist))){
  #for (i in runlist){
  print(paste("i=",i, "starting", GUTrunlist[i]))
  v=makesitemetrics(GUTrunlist[i], layer)
  if (i==1){metrics=v} else {metrics=rbind(metrics,v)} 
} 

#cleans up table a tad before saving
rownames(metrics)=seq(1,length(GUTrunlist))
metrics1=as.data.frame(metrics)
metrics1
write.csv(metrics1, paste(Metricpath, "\\sitemetrics_", Run, "_", layer, ".csv" ,sep=""), row.names=F)
