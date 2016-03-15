# Geomorphic Unit Tool Main Model File

# Last updated: 10/14/2015
# Created by: Sara Bangen (sara.bangen@gmail.com)
# -----------------------------------
import sys, os, argparse, time, fns, gutlog, shutil, fnmatch
import xml.etree.ElementTree as ET

def main():
    #parse command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('step',
                        help = 'Which step to run: "all" "evidence" "tier2" "tier3"',
                        type = str)
    parser.add_argument('input_xml',
                        help = 'Path to the input XML file.',
                        type = str)
    parser.add_argument('--verbose',
                        help = 'A little more logging.',
                        type = str)
    args = parser.parse_args()

    try:
        config = loadConfig(args.input_xml)
        outDir = config['output_directory']

        # Set up our init and log xml files
        print('Preparing to Run Gut operation: {0}.....'.format(args.step))

        # Start timer
        start = time.time()

        if args.step == "all":
            clean(outDir)
            model = fns.interface(config)
            model.EvidenceRasters()
            model.Tier2()
            model.Tier3()

        if args.step == "evidence":
            clean(outDir)
            model = fns.interface(config)
            model.EvidenceRasters()

        if args.step == "tier2":
            cleanFilePattern(outDir, "gut.*")
            cleanFile(outDir, "logs/tier2.xml")
            cleanFile(outDir, "logs/tier3.xml")
            cleanDir(outDir, "tier2")
            cleanDir(outDir, "tier3")
            model = fns.interface(config)
            model.Tier2()

        if args.step == "tier3":
            cleanDir(outDir, "tier3")
            cleanFile(outDir, "logs/tier3.xml")
            model = fns.interface(config)
            model.Tier3()

        print "GUT Operation: {0} Completed in {1} seconds.".format(args.step, int(time.time() - start))

    except:
        print 'Unxexpected error: {0}'.format(sys.exc_info()[0])
        raise
        sys.exit(0)        

# -----------------------------------------------------------------------
# Utility Methods
#
# -----------------------------------------------------------------------

# Clean everything up
def clean(rootPath):
    cleanFilePattern(rootPath, "gut.*")
    cleanDir(rootPath, "logs")
    cleanDir(rootPath, "inputs")
    cleanDir(rootPath, "evidence")
    cleanDir(rootPath, "tier2")
    cleanDir(rootPath, "tier3")

# Clean up a file
def cleanFile(rootPath, relFilePath):
    filePath = os.path.join(rootPath, relFilePath)
    if os.path.isfile(filePath):
        try:
            os.remove(filePath)
        except:
            print "ERROR Removing File: {0}".format(filePath)

def cleanFilePattern(rootPath, Pattern):
    for file in os.listdir(rootPath):
        if fnmatch.fnmatch(file, Pattern):
            try:
                os.remove(file)
            except:
                print "ERROR Removing File: {0}".format(file)

# Clean up a folder
def cleanDir(rootPath, relDirPath):
    dirPath = os.path.join(rootPath, relDirPath)
    if os.path.isdir(dirPath):
        shutil.rmtree(dirPath)

def loadConfig(xmlFile):
    config = {}
    tree = ET.parse(xmlFile)
    root = tree.getroot()
    meta = root.find('metadata')
    # Just put the whole meta into the config object
    config['metadata'] = meta
    inputs = root.find('inputs')
    for input in inputs:
        config[input.tag] = input.text
    return config

if __name__ == '__main__':
    main()





