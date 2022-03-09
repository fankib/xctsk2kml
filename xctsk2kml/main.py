import argparse

from pykml.factory import KML_ElementMaker as KML
from lxml import etree

from .convert2kml import XctskParser

def main():
	
	# CLI
	parser = argparse.ArgumentParser()
	parser.add_argument('input_file', help='The .xctsk to convert')
	parser.add_argument('output_file', help='The .kml to generate')
	args = parser.parse_args()
	
	# Parse and convert
	parser = XctskParser(args.input_file)
	task = parser.load()
	folder = task.toKML()
	root = KML.kml(folder)
	etree.ElementTree(root).write(args.output_file, pretty_print=True)
	

if __name__ == '__main__':
	main()
