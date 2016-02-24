# Geomorphic Unit Tool Main Model File

# Last updated: 10/14/2015
# Created by: Sara Bangen (sara.bangen@gmail.com)

# -----------------------------------

import sys, argparse, time, fns
def main():
    #parse command line options
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('output_directory',
                            help = 'directory to store the results of program.',
                            type = str)
        parser.add_argument('gdb_path',
                            help = 'path to the survey gdb.',
                            type = str)
        parser.add_argument('site_name',
                            help = 'site name, this will be used to name the final output.',
                            type = str)
        parser.add_argument('--champ_grain_size_results',
                            help = 'champ grain size distribution results csv',
                            type = str)
        parser.add_argument('--champ_substrate',
                            help = 'champ substrate csv',
                            type = str)
        parser.add_argument('--champ_lw',
                            help = 'champ lw csv',
                            type = str)
        args = parser.parse_args()
        print 'Preparing to Run Gut.....'



        # Start timer
        start = time.time()

        # Call model functions from functions file

##        #TODO: fns needs to be created as a class
##        fns.setConfig(config)
##        fns.EvidenceRasters(config.inDEM, config.inDet, config.bfPoints,
##                               config.bfPolyShp, config.wePolyShp, config.intBFW,
##                               config.intWW, config.fwRelief)
##
##        fns.Tier2()
##
##        fns.guMerge()
##
##        fns.Tier3()

        # End timer
        # Print model run time.
        print "GDB and Site Name: " + args.gdb_path, args.site_name
        model = fns.interface(args.output_directory, args.gdb_path, args.site_name, args.champ_grain_size_results, args.champ_substrate, args.champ_lw)
        model.EvidenceRasters(model.inDEM.path,
                            model.inDet.path,
                            model.bfPoints.path,
                            model.bfPolyShp.path,
                            model.wePolyShp.path,
                            model.intBFW,
                            model.intWW,
                            model.fwRelief)

        #TODO: right now these are hard coded but eventually should be added as arguments to argsparse
        low_slope = 10
        up_slope = 15
        low_cm_slope = 15
        up_cm_slope = 25
        low_hadbf = 1.0
        up_hadbf = 1.2
        low_relief = 0.8
        up_relief = 1.0
        low_bf_distance = 0.1 * model.intBFW
        up_bf_distance = 0.2 * model.intBFW
        fw_relief = 0.5 * model.intBFW 
        
        model.Tier2(low_slope,
                    up_slope,
                    low_cm_slope,
                    up_cm_slope,
                    low_hadbf,
                    up_hadbf,
                    low_relief,
                    up_relief,
                    low_bf_distance,
                    up_bf_distance)
        
        model.guMerge()
        print "Grain Size Results: " + args.champ_grain_size_results
        if args.champ_grain_size_results != None and args.champ_substrate != None and args.champ_lw != None:
            model.Tier3()
                            
        print 'Model run completed.'
        print 'It took', time.time()-start, 'seconds.'

    except:
        print 'Unxexpected error: {0}'.format(sys.exc_info()[0])
        raise
        sys.exit(0)        

if __name__ == '__main__':
    main()





