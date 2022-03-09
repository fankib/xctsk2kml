import numpy as np
import json

from pykml.factory import KML_ElementMaker as KML
from pykml.factory import ATOM_ElementMaker as ATOM
from pykml.factory import GX_ElementMaker as GX
from lxml import etree

from .wgs84_ch1903 import WGStoCHx, WGStoCHy, CHtoWGSlng, CHtoWGSlat

##########################################################################
# Script to convert XC Track - Task files to KML to view in Google Earth #
##########################################################################
# Author:  bembem                                                        #
# License: MIT                                                           #
##########################################################################

### WGS84-CH1903 conversion (we use the (x, y) rather the (y, x) convention!) ###

def toCh1903(lon, lat):
	return (WGStoCHy(lat, lon), WGStoCHx(lat, lon))

def toWgs84(x, y):
	return (CHtoWGSlng(x, y), CHtoWGSlat(x, y))

### KML extensions ###

class MyKML:
	
	@staticmethod
	def Cylinder(name, center_lon, center_lat, radius, altitude, styleUrl=None, steps=None):
		if not steps:
			steps = int(radius*0.5)
		
		# Quickfix: transform to ch1903, work there in meters and transform back:
		center_x, center_y = toCh1903(center_lon, center_lat)
		xs = [center_x + (np.cos(2*np.pi*i/steps)*radius) for i in range(steps)]
		xs += [xs[0]] # close loop
		ys = [center_y + np.sin(2*np.pi*i/steps)*radius for i in range(steps)]
		ys += [ys[0]] # close loop
		coords = [toWgs84(x, y) for x,y in zip(xs, ys)]
		coords = [f'{lon},{lat},{altitude}' for lon,lat in coords]		
		
		return KML.Placemark(
			KML.name(name),
			KML.styleUrl(styleUrl),
			KML.Polygon(
				KML.extrude(1),
				KML.altitudeMode('absolute'),
				KML.outerBoundaryIs(
					KML.LinearRing(
						KML.coordinates('\n'.join(coords))
						)
					)
				)			
			)
	
	@staticmethod
	def HalfCylinder(name, center_lon, center_lat, direction_lon, direction_lat, radius, altitude, styleUrl=None, steps=None):
		if not steps:
			steps = int(radius*0.25)
		
		# magic
		#wp_x, wp_y = self.buoys[-2].waypoint.coordinates.ch1903()
		#c_x, c_y = self.buoys[-1].waypoint.coordinates.ch1903()
		#n_x = wp_x-c_x
		#n_y = wp_y-c_y
		
		center_x, center_y = toCh1903(center_lon, center_lat)
		
		# compute half line
		wp_x, wp_y = toCh1903(direction_lon, direction_lat)
		n_x = wp_x-center_x
		n_y = wp_y-center_y
		norm = np.linalg.norm((n_x, n_y))
		n = (-n_y/norm, n_x/norm)
		theta = np.arccos(n[0])
		if n[1] < 0.0:
			theta *= -1 # arccos ambiguity fix:
		l_x = n[0]*radius
		l_y = n[1]*radius		
		s = int(steps*2/np.pi) # other steps for lines
		xs = [(center_x-l_x) + 2*l_x*i/s for i in range(s)]
		ys = [(center_y-l_y) + 2*l_y*i/s for i in range(s)]		
		coords_line = [toWgs84(x, y) for x,y in zip(xs, ys)]
		coords_str = [f'{lon},{lat},{altitude}' for lon,lat in coords_line]
		
		# create half cylinder
		xs = [center_x + (np.cos(np.pi*i/steps+theta)*radius) for i in range(steps)]
		ys = [center_y + np.sin(np.pi*i/steps+theta)*radius for i in range(steps)]
		coords = [toWgs84(x, y) for x,y in zip(xs, ys)]
		coords.append(coords_line[0]) # close loop
		coords_str += [f'{lon},{lat},{altitude}' for lon,lat in coords]		
		
		#hc = self.buoys[-1].toHalfCylinder(theta)
		#line_g1 = MyKML.Line('line_g1', c_x+n[0]*r, c_y+n[1]*r, -n[0]*r*2, -n[1]*r*2, 2000)
		
		return KML.Placemark(
			KML.name(name),
			KML.styleUrl(styleUrl),
			KML.Polygon(
				KML.extrude(1),
				KML.altitudeMode('absolute'),
				KML.outerBoundaryIs(
					KML.LinearRing(
						KML.coordinates('\n'.join(coords_str))
						)
					)
				)			
			)
			
	@staticmethod
	def Line(name, center_x, center_y, n_x, n_y, altitude, steps=100):
		
		xs = [center_x + n_x*i/steps for i in range(steps)]
		ys = [center_y + n_y*i/steps for i in range(steps)]
		
		coords = [toWgs84(x, y) for x,y in zip(xs, ys)]
		coords = [f'{lon},{lat},{altitude}' for lon,lat in coords]		
		
		return KML.Placemark(
			KML.name(name),
			KML.styleUrl('#buoy_default'),
			KML.Polygon(
				KML.extrude(1),
				KML.altitudeMode('absolute'),
				KML.outerBoundaryIs(
					KML.LinearRing(
						KML.coordinates('\n'.join(coords))
						)
					)
				)			
			)
		
	@staticmethod
	def style_buoy_default():
		return MyKML.create_buoy_style('8000aa55', 'default')
	
	@staticmethod
	def style_buoy_take_off():
		return MyKML.create_buoy_style('8055a4ff', 'TAKEOFF')

	@staticmethod
	def style_buoy_sss():
		return MyKML.create_buoy_style('8065faff', 'SSS')
	
	@staticmethod
	def style_buoy_ess():
		return MyKML.create_buoy_style('8065faff', 'ESS')
	
	@staticmethod
	def style_buoy_goal():
		return MyKML.create_buoy_style('8055a4ff', 'GOAL')
	
	@staticmethod
	def create_buoy_style(color_code, type):
		return KML.Style(
			KML.LineStyle(
				KML.color(color_code),
				KML.width(0.1)
				),
			KML.PolyStyle(
				KML.color(color_code),
				KML.fill(0)
				),
			id=f'buoy_{type}'
			)
		
	
	@staticmethod
	def style_waypoint():
		return KML.Style(
			KML.IconStyle(
				KML.scale(1.1),
				KML.Icon(
					KML.href('http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png')
					),
				KML.hotSpot(x='32', y='1', xunits='pixels', yunits='pixels')
			),
			id='waypoint'
			)

### DATA MODEL ###

class Coordinates:
	
	def __init__(self, longitude=7.0, latitude=46.0):
		self.longitude = longitude
		self.latitude = latitude
	
	def ch1903(self):
		return toCh1903(self.longitude, self.latitude)
	
	def toKML(self):
		return KML.coordinates(f'{self.longitude},{self.latitude}')
		

class Waypoint:
	
	def __init__(self):
		self.name = None
		self.description = None
		self.altSmoothed = None
		self.coordintes = None
	
	def cylinder(self, radius, altitude_offset, styleUrl):
		return MyKML.Cylinder(f'{self.name}-{self.description}', self.coordinates.longitude, self.coordinates.latitude, radius, 0+altitude_offset, styleUrl)

	def halfCylinder(self, direction_wp, radius, altitude_offset, styleUrl):
		return MyKML.HalfCylinder(f'{self.name}-{self.description}', self.coordinates.longitude, self.coordinates.latitude, direction_wp.coordinates.longitude, direction_wp.coordinates.latitude, radius, 0+altitude_offset, styleUrl)
		
	
	def toKML(self):
		return KML.Placemark(
			KML.name(f'{self.description} ({self.name})'),
			KML.styleUrl('#waypoint'),
			KML.Point(
				self.coordinates.toKML()
				)
			)	
		

class Buoy:
	
	def __init__(self):
		self.waypoint = None
		self.radius = None
		self.type = 'default'
	
	def toKML(self, altitude):
		return self.waypoint.cylinder(self.radius, altitude, f'#buoy_{self.type}')
	
	def toHalfCylinder(self, direction_buoy, altitude):
		return self.waypoint.halfCylinder(direction_buoy.waypoint, self.radius, altitude, f'#buoy_{self.type}')

class Task:
	
	def __init__(self):
		self.version = None
		self.taskType = None
		self.earthModel = None
		self.waypoints = []
		self.buoys = []
		self.goal_type = None
		self.altitude = None
	
	def toKML(self):
		# collect styles
		styles = [MyKML.style_waypoint(),
				MyKML.style_buoy_default(),
				MyKML.style_buoy_take_off(),
				MyKML.style_buoy_sss(),
				MyKML.style_buoy_ess(),
				MyKML.style_buoy_goal()			  
				]
		
		# collect waypoints 
		wps = [wp.toKML() for wp in self.waypoints]
		wps.append(KML.name('Waypoints'))
		
		# create goal (special buoy)
		goal = self.buoys[-1].toKML(self.altitude)
		if self.goal_type == 'LINE':
			goal = self.buoys[-1].toHalfCylinder(self.buoys[-2], self.altitude)
		
		# collect buoys
		buoys = [b.toKML(self.altitude) for b in self.buoys[:-1]]
		buoys.append(goal)
		buoys.append(KML.name('Turnpoints'))
		
		return KML.Folder(*styles, KML.Folder(*wps), KML.Folder(*buoys))
		
		
		
### XCTSK Parser ###

class XctskParser:
	
	def __init__(self, path):
		self.path = path
		self.task = Task()
		self.waypoints = []
	
	def load(self):
		with open(self.path) as f:
			doc = json.load(f)
			self.load_task(doc)
		return self.task
	
	def load_task(self, doc):
		self.task.version = doc['version']
		self.task.taskType = doc['taskType']
		if 'earthModel' in doc:
			self.task.earthModel = doc['earthModel']
		self.task.goal_type = doc['goal']['type']
		
		for node in doc['turnpoints']:
			self.load_turnpoint(node)
		
		# fix 0 altitudes
		alts = [wp.altSmoothed for wp in self.waypoints]
		for wp in self.waypoints:
			if wp.altSmoothed == 0:
				wp.altSmoothed = np.mean(alts)
		self.task.altitude = np.mean(alts)+1000
		
		self.task.waypoints = self.waypoints
		self.task.buoys[-1].type = 'GOAL' # goal fix

	
	def load_turnpoint(self, doc):
		waypoint = self.get_or_create_waypoint(doc['waypoint'])
		buoy = Buoy()
		buoy.waypoint = waypoint
		buoy.radius = doc['radius']
		if 'type' in doc:
			buoy.type = doc['type']
		self.task.buoys.append(buoy)
		
	
	def get_or_create_waypoint(self, doc):
		for wp in self.waypoints:
			if doc['name'] == wp.name:
				return wp
		wp = Waypoint()
		wp.name = doc['name']
		wp.description = doc['description']
		wp.altSmoothed = int(doc['altSmoothed'])
		wp.coordinates = Coordinates(doc['lon'], doc['lat'])
		self.waypoints.append(wp)
		return wp
				
		
		


### other stuff ###

if __name__ == '__main__':
	
	named_object = KML.name('Hello World')

	pm1 = KML.Placemark(
		KML.name('Hello World'),
		KML.Point(
			KML.coordinates('7.819915771484375,46.70069122314453,')
			)
		)

	pm2 = KML.Placemark(
		KML.name('A second placemark!'),
		KML.Point(
			KML.coordinates('7.823744773864746,46.68098449707031')
			)
		)


		
	# end styles

	#cylinder = MyKML.Cylinder('sss', 7.823744773864746, 46.68098449707031, 1500, 2000, styleUrl='#buoy_default')
		
	#folder = KML.Folder(MyKML.style_buoy_default(), pm1, pm2, cylinder)

	# Integration test:
	parser = XctskParser('tasks/interlaken-battle.xctsk')
	task = parser.load()
	folder = task.toKML()
	root = KML.kml(folder)

	# convert to string:
	print(etree.tostring(root, pretty_print=True).decode())




