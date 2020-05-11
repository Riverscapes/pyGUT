# Philip Bailey
# 11 May 2020
# Script to build riverscapes project.rs.xml for series of Asotin GUT projects 
import os
import sqlite3
import argparse
from loghelper import Logger

input_files = {
    'BCenterline.shp': 'Bankfull Centerline',
    'BExtent.shp': 'Bankfull Extent',
    'WExtent.shp': 'Wetted Extent',
    'Thalweg.shp': 'Thalweg',
    'WCenterline.shp': 'Wetted Centerline',
    'Channel_Units_Field.shp': 'Channel Units (Field)',
    'WCrossSections.shp': 'Wetted Cross Sections',
    'BIslands.shp': 'Bankfull Islands',
    'WIslands.shp': 'Wetted Islands',
    'Channel_Units.shp': 'Channel Units',
    'BCrossSections.shp': 'Bankfull Cross Sections',
    'DEM.tif': 'DEM'
}

intermediate_files = {
    'bedSlopeSD_Cat.shp': 'Bed Slope Standard Deviation Category Shapefile',
    'bfCh.tif': 'Bankfull Channel Raster',
    'bfSlope.tif': 'Bankfull Surface Slope Raster',
    'bfSlope_Smooth.tif': 'Smoothed Bankfull Surface Slope Raster',
    'bfSlope_Smooth_Cat.shp': 'Smoothed Bankfull Surface Slope Cateogry Polygon',
    'channelEdge.shp': 'Channel Edge Polygon',
    'channelNodes.shp': 'Channel Nodes Points',
    'chMargin.tif': 'Channel Margin Raster',
    'channelNodes_Thalwegs.shp': 'Contour Node Points',
    'channelPolygons_Thalwegs.shp': 'Contour Polygons',
    'DEM_Contours.shp': 'DEM Contour Lines',
    'DEM_mean.tif': 'Smoothed DEM Raster',
    'bedSlopeSD.tif': 'Bed Slope Standard Deviation Raster',
    'inCh_DEM.tif': 'Smoothed In-Channel DEM Raster',
    'mBendIndex.tif': 'Meander Bend Index',
    'resDepth.tif': 'Residual Pool Depth Raster',
    'resTopo.tif': 'Residual Topography Raster',
    'slope_inCh_DEM.tif': 'In-Channel DEM Slope Raster'
}

output_files = {
    'Tier1_InChannel.shp': 'Tier 1',
    'Tier2_InChannel.shp': 'Tier 2',
    'Tier2_InChannel_Discrete.shp': ' Tier 2 - Discrete',
    'Tier3_InChannel_GU.shp': 'Tier 3 In Channel Geomorphic Units',
    'Tier3_InChannel_GU_raw.shp': 'Tier 3 In Channel Geomorphic Units Raw',
    'Tier3_InChannel_subGU.shp': 'Tier 3 In Channel Sub Geomorphic Units'

}

def build_gut_riverscapes_projects(dbPath, gut_data):

    log = Logger('GUT')


    conn = sqlite3.connect(dbPath)
    conn.row_factory = dict_factory
    
    # Load all the CHaMP sites for Asotin
    champ_sites = get_asotin_sites(conn)
    log.info('{} CHaMP Sites loaded from database'.format(len(champ_sites)))

    # Load all the GUT folders into a dictionary
    gut_sites = {os.path.join(gut_data, x): {'SiteName': x} for x in os.listdir(gut_data) if os.path.isdir(os.path.join(gut_data, x)) is True}
    log.info('{} GUT site folders located on disk'.format(len(gut_sites)))
    
    # Match GUT folders to CHaMP sites
    for folder, data in gut_sites.items():
        abbr = os.path.basename(folder).replace(' ', '').replace('-', '')
        for champ, champ_data in champ_sites.items():
            if abbr in champ:
                for key, val in champ_data.items():
                    data[key] = val
        
        if len(data) == 1:
            log.warning('No CHaMP site found for folder {}'.format(folder))

        build_project(folder, data)




    log.info('Process completed successfully.')


def build_project(folder, site_data):

    log = Logger('Realization')
    log.info('Building GUT project for {}'.format(folder))

    site_data['Realizations'] = {x: {'Inputs': {}, 'EvidenceLayers': {}, "Outputs": {}} for x in os.listdir(folder)}
    log.info('{} realizations identified'.format(len(site_data['Realizations'])))

    for realization, real_data in site_data['Realizations'].items():

        if not realization.isnumeric():
            log.warning('Skipping non-numeric realization folder {}'.format(os.path.join(folder, realization)))
            continue

        build_datasets('Inputs', os.path.join(folder, realization, 'Inputs'), real_data['Inputs'], input_files)
        build_datasets('Intermediates', os.path.join(folder, realization, 'EvidenceLayers'), real_data['EvidenceLayers'], intermediate_files)

        real_parent = os.path.join(folder, realization, 'Output', 'GUT_2.1')
        for run in os.listdir(real_parent):
            run_folder  = os.path.join(real_parent, run)

            if not os.path.isfile(os.path.join(folder, 'configSettings.txt')):
                log.warning('Skipping output folder withput configSettings.txt file {}'.format(folder))
                continue

            build_datasets('Outputs', run_folder, real_data['Outputs'], output_files)
          

def build_datasets(folder_type, folder, input_data, lookup):

    log = Logger(folder_type)
    log.info('Building GUT project for {}'.format(folder))

    for file in os.listdir(folder):
        if file.endswith('.shp'):
            file_name = os.path.basename(file)
            if file_name in lookup:
                file_name = lookup[file_name]
            else:
                log.warning('Missing ShapeFile type {}. Using file name as input name'.format(file_name))

            input_data[file_name]: ('Vector', os.path.join(folder, file))

        elif file.endswith('.tif'):
            file_name = os.path.basename(file)
            if file_name in lookup:
                file_name = lookup[file_name]
            else:
                log.warning('Missing raster file type {}. Using file name as input name'.format(file_name))

            input_data[file_name]: ('Raster', os.path.join(folder, file))





 


def get_asotin_sites(conn):

    curs = conn.cursor()
    curs.execute('SELECT * FROM CHaMP_Sites WHERE WatershedID = 17')
    return {
        row['SiteName'].replace(' ', '').replace('-', '') : {
            'SiteName' : row['SiteName'],
            'StreamName': row['StreamName'],
            'HUC8': row['HUC4']
        }

    for row in curs.fetchall()}



def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dbpath', help='Path to CHaMP Workbench SQLite database', type=str)
    parser.add_argument('gut_data', help='Path to top level folder containing GUT projects', type=str)
    parser.add_argument('--verbose', help='verbose logging')
    args = parser.parse_args()

    log = Logger('GUT')
    log.setup(logPath=os.path.join(args.gut_data, "build_gut_riverscapes_projects.log"), verbose=args.verbose)
    log.info('DB Path: {}'.format(args.dbpath))
    log.info('GUT Data: {}'.format(args.gut_data))
  
    build_gut_riverscapes_projects(args.dbpath, args.gut_data)


if __name__ == '__main__':
    main()
