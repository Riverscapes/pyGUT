# Philip Bailey
# 11 May 2020
# Script to build riverscapes project.rs.xml for series of Asotin GUT projects 
import os
import sqlite3
import argparse
from loghelper import Logger
import xml_builder
import datetime
import uuid

XMLBuilder = xml_builder.XMLBuilder

namespaceSchemaURL = ''
modelVersion = '2.1'


class RSLayer:
    def __init__(self, name, id, tag, rel_path):
        if name is None:
            raise Exception('Name is required')
        if id is None:
            raise Exception('id is required')
        if rel_path is None:
            raise Exception('rel_path is required')
        self.name = name
        self.id = id
        self.tag = tag
        self.rel_path = rel_path


input_files = {
    'BCenterline.shp': ('Bankfull Centerline', 'BFCL'),
    'BExtent.shp': ('Bankfull Extent', 'BFEX'),
    'WExtent.shp': ('Wetted Extent', 'WEEX'),
    'Thalweg.shp': ('Thalweg', 'TH'),
    'WCenterline.shp': ('Wetted Centerline', 'WCL'),
    'Channel_Units_Field.shp': ('Channel Units (Field)', 'CU'),
    'WCrossSections.shp': ('Wetted Cross Sections', 'WXS'),
    'BIslands.shp': ('Bankfull Islands', 'BFI'),
    'WIslands.shp': ('Wetted Islands', 'WI'),
    'Channel_Units.shp': ('Channel Units', 'CU'),
    'BCrossSections.shp': ('Bankfull Cross Sections', 'BFXS'),
    'DEM.tif': ('DEM', 'DEM'),
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
    'Tier1_InChannel.shp': ('Tier 1', 'Tier1'),
    'Tier2_InChannel.shp': ('Tier 2', 'Tier2'),
    'Tier2_InChannel_Discrete.shp': (' Tier 2 - Discrete', 'Tier2'),
    'Tier3_InChannel_GU.shp': ('Tier 3 In Channel Geomorphic Units', 'Tier3'),
    'Tier3_InChannel_GU_raw.shp': ('Tier 3 In Channel Geomorphic Units Raw', 'Tier3'),
    'Tier3_InChannel_subGU.shp': ('Tier 3 In Channel Sub Geomorphic Units', 'Tier3')
}

def build_gut_riverscapes_projects(dbPath, gut_data):

    log = Logger('GUT')


    conn = sqlite3.connect(dbPath)
    conn.row_factory = dict_factory
    
    # Load all the CHaMP sites for Asotin
    champ_sites = get_asotin_sites(conn)
    log.info('{} CHaMP Sites loaded from database'.format(len(champ_sites)))

    # Load all the GUT folders into a dictionary
    gut_sites = {os.path.join(gut_data, x): {'MetaData': {}} for x in os.listdir(gut_data) if os.path.isdir(os.path.join(gut_data, x)) is True}
    log.info('{} GUT site folders located on disk'.format(len(gut_sites)))
    
    # Match GUT folders to CHaMP sites
    for folder, data in gut_sites.items():
        abbr = os.path.basename(folder).replace(' ', '').replace('-', '')
        data['MetaData']['ModelVersion'] = modelVersion
        data['MetaData']['dateCreated'] = datetime.datetime.now().isoformat()

        for champ, champ_data in champ_sites.items():
            if abbr in champ:
                for key, val in champ_data.items():
                    data['MetaData'][key] = val
        
        if len(data) == 1:
            log.warning('No CHaMP site found for folder {}'.format(folder))

        build_project(folder, data)
        write_project(folder, data) # TODO change this to folder


    log.info('Process completed successfully.')


def build_project(folder, site_data):

    log = Logger('Realization')
    log.info('Building GUT project for {}'.format(folder))

    site_data['Realizations'] = {x: {'Inputs': {}, 'EvidenceLayers': {}, "Analyses": {}} for x in os.listdir(folder)}
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

            if not os.path.isfile(os.path.join(run_folder, 'configSettings.txt')):
                log.warning('Skipping output folder withput configSettings.txt file {}'.format(folder))
                continue

            real_data['Analyses'][run] = {}

            build_datasets('Outputs', run_folder, real_data['Analyses'][run], output_files)
            real_data['Analyses'][run]['Configuration Settings'] = RSLayer('Configuration Settings', 'ID', 'File', os.path.join(run_folder, 'configSettings.txt'))
          

def build_datasets(folder_type, folder, input_data, lookup):

    log = Logger(folder_type)
    log.info('Building GUT project for {}'.format(folder))

    for file in os.listdir(folder):
        tag = 'ID'
        if file.endswith('.shp'):
            file_name = os.path.basename(file)


            if file_name in lookup:
                if lookup[file_name] is str:
                    file_name = lookup[file]
                else:
                    file_name = lookup[file][0]
                    tag = lookup[file][1]
            else:
                log.warning('Missing ShapeFile type {}. Using file name as input name'.format(file_name))

            input_data[file_name] = RSLayer(file_name, tag, 'Vector', os.path.join(folder, file))

        elif file.endswith('.tif'):
            file_name = os.path.basename(file)
            if file in lookup:
                if lookup[file] is str:
                    file_name = lookup[file]
                else:
                    file_name = lookup[file][0]
                    tag = lookup[file][1]      
            else:
                log.warning('Missing raster file type {}. Using file name as input name'.format(file_name))

            input_data[file_name] = RSLayer(file_name, tag, 'Raster', os.path.join(folder, file))


def write_project(folder, data):

    xml_path = os.path.join(folder, 'project.rs.xml')
    if os.path.isfile(xml_path):
        os.remove(xml_path)

    xmlb = XMLBuilder(xml_path, 'Project', [
            ('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance'),
            ('xsi:noNamespaceSchemaLocation',
             namespaceSchemaURL)])

    xmlb.add_sub_element(xmlb.root, 'Name', 'GUT for Site {}'.format(data['MetaData']['SiteName']))
    xmlb.add_sub_element(xmlb.root, 'ProjectType', 'GUT')

    add_project_meta(xmlb, data['MetaData'])

    for real_name, real_data in data['Realizations'].items():

        reals_element = xmlb.find('Realizations')
        if not reals_element:
            reals_element = xmlb.add_sub_element(xmlb.root, "Realizations")


        realization_id = getUniqueTypeID(reals_element, 'GUT', 'RZ')

        real_element = xmlb.add_sub_element(reals_element, 'GUT', tags=[
            ('dateCreated', datetime.datetime.now().isoformat()),
            ('guid', str(uuid.uuid1())),
            ('id', realization_id)])

        xmlb.add_sub_element(real_element, "Name", real_name)


        for data_grouping in ['Inputs', 'EvidenceLayers']:
            element = xmlb.add_sub_element(real_element, data_grouping)
            for input_data in real_data[data_grouping].values():
                add_dataset(xmlb, element, xml_path, input_data, input_data.tag)

        analyses_element = xmlb.add_sub_element(real_element, 'Analyses')
        for analysis_name, analysis_data in real_data['Analyses'].items():
            analysis_element = xmlb.add_sub_element(analyses_element, 'Analysis')
            xmlb.add_sub_element(analysis_element, 'Name', analysis_name)

            for rsoutput in analysis_data.values():
                add_dataset(xmlb, analysis_element, xml_path, rsoutput, rsoutput.tag)
           

  

    xmlb.write()
    return xml_path


def add_project_meta(xmlBuilder, valdict):
    metadata_element = xmlBuilder.find('MetaData')
    for mkey, mval in valdict.items():
        if not metadata_element:
            metadata_element = xmlBuilder.add_sub_element(xmlBuilder.root, "MetaData")

        xmlBuilder.add_sub_element(metadata_element, "Meta", mval, [("name", mkey)])
    xmlBuilder.write()

def getUniqueTypeID(nodParent, xml_tag, IDRoot):

    i = 1
    for nodChild in nodParent.findall(xml_tag):
        if nodChild.attrib['id'][:len(IDRoot)] == IDRoot:
            i += 1

    return '{}{}'.format(IDRoot, i if i > 0 else '')

def add_dataset(xmlb, parent_node, xml_path, rs_lyr, default_tag):

    xml_tag = rs_lyr.tag if rs_lyr.tag is not None else default_tag
    id = getUniqueTypeID(parent_node, xml_tag, rs_lyr.id)

    nod_dataset = xmlb.add_sub_element(parent_node, xml_tag, tags=[('guid', str(uuid.uuid1())), ('id', id)])
    xmlb.add_sub_element(nod_dataset, 'Name', rs_lyr.name)
    xmlb.add_sub_element(nod_dataset, 'Path', os.path.relpath(rs_lyr.rel_path, os.path.dirname(xml_path)))


def get_asotin_sites(conn):

    curs = conn.cursor()
    curs.execute('SELECT S.*, W.WatershedName AS WatershedName FROM CHaMP_Sites S INNER JOIN CHaMP_Watersheds W ON S.WatershedID = W.WatershedID WHERE W.WatershedID = 17')
    return {
        row['SiteName'].replace(' ', '').replace('-', '') : {
            'SiteName' : row['SiteName'],
            'StreamName': row['StreamName'],
            'HUC8': row['HUC4'],
            'Watershed': row['WatershedName']
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
