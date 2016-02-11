import xml.etree.ElementTree as Et
import config, os, fnmatch
from shutil import copyfile

# A few globals
workdir = ""
inputs = ""


def prep(argv):
    global workdir, inputs
    print 'Loading XML File'
    print 'Choosing Work Folder: ' + workdir

    workdir = os.path.join(os.path.dirname(argv[1]), 'workdir')
    if not os.path.exists(workdir):
        os.makedirs(workdir)
    tree = Et.parse(argv[1])
    inputs = tree.getroot().find('inputs')

    config.workspace = workdir
    config.siteName = inputs.find('SiteName').text.strip();

    # Now put all the files in the right place.
    copyFromXMLPath("DEM", config.inDEM)
    copyFromXMLPath("DetrendedDEM", config.inDet)
    config.intBFW = float(inputs.find('BankfullWidth').text.strip())
    config.intWW = float(inputs.find('WettedWidth').text.strip())
    copyFromXMLPath("WettedDepth", config.inWaterD)
    copyFromXMLPath("BankfullPoints", config.bfPoints)
    copyFromXMLPath("BankfullPolygon", config.bfPolyShp)
    copyFromXMLPath("BankfullCrossSections", config.bfXS)
    copyFromXMLPath("WettedPolygon", config.wePolyShp)
    copyFromXMLPath("ChannelUnits", config.champUnits)
    return config


def copyFromXMLPath(xmlname, filename):
    global workdir, inputs
    srcraw = inputs.find(xmlname).text.strip()

    srcbasename = os.path.splitext(os.path.basename(srcraw))[0]
    dstbasename = os.path.splitext(filename)[0]

    for fname in os.listdir(os.path.dirname(srcraw)):
        if fnmatch.fnmatch(fname, srcbasename + '.*'):
            ext = os.path.splitext(fname)[1].split(".")[1]
            midext = os.path.splitext(fname)[0].split('.')[1:]
            newnamearr = [dstbasename]
            for extpart in midext:
                newnamearr.append(extpart)
            newnamearr.append(ext)
            newfilename = ".".join(newnamearr)

            print "copying: " + fname + " to: " + newfilename
            src = os.path.join(os.path.dirname(srcraw), fname)
            dst = os.path.join(workdir, newfilename)
            copyfile(src, dst)


# <?xml version="1.0"?>
# <gut_prep>
#   <date>11 Feb 2016</date>
#   <inputs>
#     <SiteName>
#     </SiteName>
#     <DEM>C:\Users\Matt\AppData\Roaming\CHaMPTopo\TempWorkspace\DEM2.tif</DEM>
#     <DetrendedDEM>C:\Users\Matt\AppData\Roaming\CHaMPTopo\TempWorkspace\Detrended2.tif</DetrendedDEM>
#     <WettedDepth>C:\Users\Matt\AppData\Roaming\CHaMPTopo\TempWorkspace\Water_Depth.tif</WettedDepth>
#     <BankfullWidth>6.74632</BankfullWidth>
#     <WettedWidth>5.434275</WettedWidth>
#     <BankfullPoints>C:\Users\Matt\AppData\Roaming\CHaMPTopo\TempWorkspace\topopts.shp</BankfullPoints>
#     <BankfullPolygon>C:\Users\Matt\AppData\Roaming\CHaMPTopo\TempWorkspace\BFPolygon.shp</BankfullPolygon>
#     <BankfullCrossSections>C:\Users\Matt\AppData\Roaming\CHaMPTopo\TempWorkspace\BFCrossSections.shp</BankfullCrossSections>
#     <WettedPolygon>C:\Users\Matt\AppData\Roaming\CHaMPTopo\TempWorkspace\WECrossSections.shp</WettedPolygon>
#     <ChannelUnits>C:\Users\Matt\AppData\Roaming\CHaMPTopo\TempWorkspace\ChannelUnits.shp</ChannelUnits>
#   </inputs>
# </gut_prep>