#################################################################################################################
## CHaMP Grain Size Distribution Calculation - GUI
## James Hensleigh - Hensleigh.ride@gmail.com
##
## The purpose of this script is to take in a either a CHAMP CHANNELUNIT*.csv or a CHAMP PEBBLE_CHAMP*.csv file and 
## calculate the grain size distribution for the file. Specifically the D16, D50, and D84.
##
## For a CHANNELUNIT file the grain size distribution is calculated for each line in the file.
## For a PEBBLE_CHAMP file the grain size distribution is calculated for the entire file.
#################################################################################################################

import os, math, numpy, sys, glob, csv
import argparse
upperBoundsCHANNEL = [0.06, 2, 16, 64, 256, 4000] # If different bins are used this needs to be changed


def Di(x1, x2, y1, y2, i):
    '''Calculates the Dx for a given grain size distribution'''
    try:
        return math.pow(10,((math.log(x2, 10) - math.log(x1, 10)) * ((i - float(y1))/(y2 - y1)) + math.log(x1, 10)))
    except:
        print sys.exc_info()

# "Watershed","SiteID","SampleDate","VisitID","MeasureNbr","Crew","VisitPhase","VisitStatus","StreamName","Panel","ChannelUnitID","ChannelUnitNumber",
# "Bedrock","BouldersGT256","Cobbles65_255","CoarseGravel17_64","FineGravel3_16","Sand006_2","FinesLT006",
# "SumSubstrateCover"
def processChannelFileAndWrite(grainFile, outfile):

    # Raw Data Import into an array
    infile = open(grainFile, 'r')  # CSV file
    table = []
    for row in csv.reader(infile):
        table.append(row)
    infile.close()

    with open(outfile, 'w') as outFile:

        # Write the header
        outFile.write(",".join(table[0]) + ",D16,D50,D84,D90\n")

        # The bins are listed in sequential order so we need to find the first one and then we're good
        startIndex = table[0].index("BouldersGT256")
        endIndex = table[0].index("FinesLT006") + 1
        if (endIndex - startIndex != len(upperBoundsCHANNEL)):
            raise "Warning. Wrong number of bins/columns in CSV file"

        for rowi in range(len(table)):
            # Skip the header. We've already dealt with it.
            if rowi == 0:
                continue
                
            row = table[rowi]

            if 'D16' in locals():
                del D16

            if 'D50' in locals():
                del D50

            if 'D84' in locals():
                del D84

            if 'D90' in locals():
                del D90

            # Createa a partial line with all the old columns
            relationalColumns = ",".join(table[rowi]) + ","

            # Find the beginning of the bins
            sub = [int(i) for i in table[rowi][startIndex:endIndex]]
            sub.reverse()
            cumSum = list(numpy.cumsum(sub))

            if cumSum[-2] == 0:
                    D16 = 4000
                    D50 = 4000
                    D84 = 4000
                    D90 = 4000
                    outFile.write(relationalColumns + str(D16) + ',' + str(D50) + ',' + str(D84) + ',' + str(D90) + '\n')
                    continue

            cumSumNoBedrock = [int(i/float(cumSum[-2])*100) for i in cumSum[:-1]]
            ct = 0
            for i in cumSumNoBedrock:
                if ct + 1 > len(cumSumNoBedrock):
                    break

                if 'D90' in locals():
                    outFile.write(relationalColumns + str(D16) + ',' + str(D50) + ',' + str(D84) + ',' + str(D90) + '\n')
                    break

                elif ct == 0 and i >= 90:
                    D16 = 0.06
                    D50 = 0.06
                    D84 = 0.06
                    D90 = 0.06
                    outFile.write(relationalColumns + str(D16) + ',' + str(D50) + ',' + str(D84) + ',' + str(D90) + '\n')
                    break

                elif ct == 0 and i >= 84:
                    D16 = 0.06
                    D50 = 0.06
                    D84 = 0.06

                    if 90 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1):
                        D90 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct + 1], cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1], 90)
                        outFile.write(relationalColumns + str(D16) + ',' + str(D50) + ',' + str(D84) + ',' + str(D90) + '\n')
                        break

                    else:
                        ct += 1
                        continue

                elif ct == 0 and i >= 50:
                    D16 = 0.06
                    D50 = 0.06

                    if 84 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1) and 90 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1):
                        D84 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct + 1], cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1], 84)
                        D90 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct + 1], cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1], 90)
                        outFile.write(relationalColumns + str(D16) + ',' + str(D50) + ',' + str(D84) + ',' + str(D90) + '\n')
                        break

                    elif 84 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1):
                            D84 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct + 1], cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1], 84)
                            ct += 1
                            continue
                    else:
                        ct += 1
                        continue

                elif ct == 0 and i >= 16:
                    D16 = 0.06

                    if 50 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1) and 84 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1) and 90 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1):
                        D50 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct + 1], cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1], 50)
                        D84 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct + 1], cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1], 84)
                        D90 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct + 1], cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1], 90)
                        outFile.write(relationalColumns + str(D16) + ',' + str(D50) + ',' + str(D84) + ',' + str(D90) + '\n')
                        break

                    elif 50 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1) and 84 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1):
                        D50 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct + 1], cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1], 50)
                        D84 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct + 1], cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1], 84)
                        ct += 1
                        continue

                    elif 50 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1):
                        D50 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct + 1], cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1], 50)
                        ct += 1
                        continue

                    else:
                        ct += 1
                        continue

                if i < 16 and cumSumNoBedrock[ct + 1] < 16:
                    ct += 1
                    continue

                elif 16 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1) and 50 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1) and 84 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1) and 90 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1):

                    D16 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 16)
                    D50 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 50)
                    D84 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 84)
                    D90 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 90)
                    outFile.write(relationalColumns + str(D16) + ',' + str(D50) + ',' + str(D84) + ',' + str(D90) + '\n')
                    break


                elif 90 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1) and 'D16' in locals() and 'D50' in locals() and 'D84' in locals():


                    D90 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 90)
                    outFile.write(relationalColumns + str(D16) + ',' + str(D50) + ',' + str(D84) + ',' + str(D90) + '\n')
                    break

                elif 84 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1) and 90 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1) and 'D16' in locals() and 'D50' in locals():
                    D84 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 84)
                    D90 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 90)
                    outFile.write(relationalColumns + str(D16) + ',' + str(D50) + ',' + str(D84) + ',' + str(D90) + '\n')
                    break


                elif 50 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1) and 84 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1) and 90 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1) and 'D16' in locals():

                    D50 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 50)
                    D84 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 84)
                    D90 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 90)
                    outFile.write(relationalColumns + str(D16) + ',' + str(D50) + ',' + str(D84) + ',' + str(D90) + '\n')
                    break


                elif 16 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1) and 50 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1) and 84 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1):

                    D16 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 16)
                    D50 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 50)
                    D84 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 84)
                    ct += 1
                    continue

                elif 16 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1):

                    D16 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 16)

                    if 50 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1):
                        D50 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 50)
                        ct += 1
                        continue

                    else:
                        ct += 1
                        continue

                elif 50 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1) and 'D16' in locals():

                    D50 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 50)

                    if 84 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1):
                        D84 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 84)
                        ct += 1
                        continue

                    else:
                        ct += 1
                        continue


                elif 84 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1):

                    D84 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 84)

                    if 90 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1]):
                        D90 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 90)
                        outFile.write(relationalColumns + str(D16) + ',' + str(D50) + ',' + str(D84) + ',' + str(D90) + '\n')
                        break

                    else:
                        ct += 1
                        continue

                elif 90 in range(cumSumNoBedrock[ct], cumSumNoBedrock[ct + 1] + 1):

                    D90 = Di(upperBoundsCHANNEL[ct], upperBoundsCHANNEL[ct+1], cumSumNoBedrock[ct], cumSumNoBedrock[ct+1], 90)
                    ct += 1
                    outFile.write(relationalColumns + str(D16) + ',' + str(D50) + ',' + str(D84) + ',' + str(D90) + '\n')
                    break

                else:
                    ct += 1



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_csv',
                        help = 'Path to input CSV',
                        type = str)
    parser.add_argument('output_csv',
                        help = 'Path to output CSV',
                        type = str)
    args = parser.parse_args()

    # TODO: Add the CSV path stuff for tier 3
    if args.input_csv:
        processChannelFileAndWrite(args.input_csv, args.output_csv)
if __name__ == '__main__':
    main()