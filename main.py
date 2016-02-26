# Geomorphic Unit Tool Main Model File

# Last updated: 10/14/2015
# Created by: Sara Bangen (sara.bangen@gmail.com)
# -----------------------------------
import sys, os, argparse, time, fns, logger, shutil
import xml.etree.ElementTree as ET

def main():
    #parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('step',
                        help = 'Which step to run: "all" "prep" "tier2" "tier3"',
                        type = str)
    parser.add_argument('input_xml',
                        help = 'Path to the input XML file.',
                        type = str)
    args = parser.parse_args()

    try:
        config = loadConfig(args.input_xml)
        model = fns.interface(config)

        # Set up our init and log xml files
        logger.log('Preparing to Run Gut.....')

        # Start timer
        start = time.time()

        if args.step == "all":
            clean()
            model.EvidenceRasters()
            model.Tier2()
            model.guMerge()
            model.Tier3()

        if args.step == "prep":
            clean()
            model.EvidenceRasters()

        if args.step == "tier2":
            cleanFile("gut.shp")
            cleanDir("tier2")
            cleanDir("tier3")
            model.Tier2()
            model.guMerge()

        if args.step == "tier3":
            cleanDir("tier3")
            model.Tier3()

        logger.log('Model run completed.')
        logger.log('It took', time.time() - start, 'seconds.')

    except:
        print 'Unxexpected error: {0}'.format(sys.exc_info()[0])
        raise
        sys.exit(0)        

# -----------------------------------------------------------------------
# Utility Methods
#
# -----------------------------------------------------------------------

# Clean everything up
def clean():
    cleanFile("gut.shp")
    cleanDir("logs")
    cleanDir("prep")
    cleanDir("tier2")
    cleanDir("tier3")

# Clean up a file
def cleanFile(rootPath, relFilePath):
    filePath = os.path.join(rootPath, relFilePath)
    if os.path.isfile(filePath):
        os.remove(filePath)

# Clean up a folder
def cleanDir(rootPath, relDirPath):
    dirPath = os.path.join(rootPath, relDirPath)
    if os.path.isdir(dirPath):
        shutil.rmtree(dirPath)

def loadConfig(xmlFile):
    config = {}
    tree = ET.parse(xmlFile)
    root = tree.getroot()
    inputs = root.getchildren()
    for input in inputs:
        config[input.tag] = input.text
    return config

if __name__ == '__main__':
    main()





