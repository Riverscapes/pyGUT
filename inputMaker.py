#!/bin/python
import argparse, os
import xml.etree.ElementTree as ET

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input_xml',
                        help = 'Path to input XML',
                        type = str)
    parser.add_argument('output_directory',
                        help = 'Path to the GUT working path (will be wiped!)',
                        type = str)
    parser.add_argument('gdb_path',
                        help = 'Path to the SurveyGDB.',
                        type = str)
    parser.add_argument('site_name',
                        help = 'Name of the site.',
                        type = str)
    args = parser.parse_args()

    # TODO: Add the CSV path stuff for tier 3
    if args.input_xml and args.output_directory and args.gdb_path and args.site_name:
        tree = ET.parse(os.path.join(os.getcwd(), 'xml/inputs_template.xml'))
        root = tree.getroot()
        root.findall('output_directory').text = args.output_directory
        root.findall('gdb_path').text = args.gdb_path
        root.findall('site_name').text = args.site_name
        tree.write(args.input_xml)

if __name__ == '__main__':
    main()