#!/usr/bin/env python

"""
	WADdle Plot v0.8 - DOOM wadfile map plotter.
"""
from struct import unpack
import planar
import turtle
import sys
import argparse

#Python 3 madness...
from planar.line import LineSegment
from turtle import *


__author__ = 'InZane84'
__email__ = 'InZaneGamer84@protonmail.com'

class LumpInfo:
	def __init__(self ,offset, size):
		"""Entry in the WAD's directory. Table starts at
		"""
		self.offset = offset # Start of the Lump Info Entries (Directory)
		self.size = size


class Level:
	def __init__(self ,verts_x, verts_y, lines, sides):
		"""DOOM level object"""
		self.verts_x = verts_x
		self.verts_y = verts_y
		self.lines = lines
		self.sides = sides
		self.vertex_vectors = self.to_vec2()
		
	def __repr__(self):
		"""Print information about the built level"""
		return self.return_info()
	
	def return_info(self):
		"""This instance's loaded level info"""
		level_name = '[Level: ' + str(self.map) + ' is loaded]\n'
		vertices = str(len(self.vertex_vectors)) + ' vertices\n'
		linedefs = str(len(self.lines)) + ' linedefs\n'
		sidedefs = str(len(self.sides)) + ' sidedefs'
		return level_name + vertices + linedefs + sidedefs

	def to_vec2(self):
		"""Parses vertexes into Vector2D's"""
		vecs = []
		vecs_x = []
		vecs_y = []
		vertex_vectors = []
		
		i = 0
		x = 0
		y = 0
		
		while i < len(self.verts_x and self.verts_y) /4:
			vecs.append(planar.Vec2(self.verts_x[x], self.verts_y[y]))
			vertex_vectors.append(vecs[0])
			vecs_x.append(vecs[0].x)
			vecs_y.append(vecs[0].y)
			vecs.remove(vecs[0])
			i += 1
			x += 1
			y += 1
		return vertex_vectors


class LineDefs:
	def __init__(self, offset, size, wadfile):
		"""LINEDEFS"""
		self.offset = offset
		self.size = size
		self.lines = []
		self.wadfile = wadfile
	
	def get_lines(self):
		"""Load LINEDEFS"""
		i = 0
		self.wadfile.seek(self.offset)
		
		while i < self.size/14:
			line_packed = self.wadfile.read(14)
			line = unpack('<hhhhhhh', line_packed)
			linedefs = {}
			linedefs['start_point'] = line[0]
			linedefs['end_point'] = line[1]
			linedefs['flags'] = line[2]
			linedefs['type'] = line[3]
			linedefs['tag'] = line[4]
			linedefs['frontside_num'] = line[5]
			linedefs['backside_num'] = line[6]
			linedefs['number'] = i
			self.lines.append(linedefs)
			i += 1
		return self.lines


class SideDefs:
	def __init__(self, offset, size, wadfile):
		"""SIDEDEFS"""
		self.offset = offset
		self.size = size
		self.sides = []
		self.wadfile = wadfile
	
	def get_sides(self):
		"""Load SIDEDEFS"""
		i = 0
		self.wadfile.seek(self.offset)
		
		while i < self.size/30:
			side_packed = self.wadfile.read(30)
			side = unpack('<hh8s8s8sh', side_packed)
			side_dict = dict()
			side_dict['x'] = side[0]
			side_dict['y'] = side[1]
			side_dict['UPPER'] = side[2].strip(b"\x00")
			side_dict['LOWER'] = side[3].strip(b"\x00")
			side_dict['MIDDLE'] = side[4].strip(b"\x00")
			# decode...
			#side_dict["UPPER"] = side_dict["UPPER"].decode(encoding="utf-8")
			#side_dict["LOWER"] = side_dict["LOWER"].decode("utf")
			#side_dict["MIDDLE"] = side_dict["MIDDLE"].decode("utf")

			side_dict['SECTOR'] = side[5]
			self.sides.append(side_dict)
			i += 1
		return self.sides


class Vertexes:
	def __init__(self, offset, size, wadfile):
		"""VERTEXES"""
		self.offset = offset
		self.size = size
		self.verts_x = []
		self.verts_y = []
		self.wadfile = wadfile
		
	def get_verts(self):
		"""Load VERTEXES"""
		i = 0
		self.wadfile.seek(self.offset)
		
		while i < self.size:
			vertex_packed = self.wadfile.read(4)
			vertex = unpack('<hh', vertex_packed)
			self.verts_x.append(vertex[0])
			self.verts_y.append(vertex[1])
			i += 1
		return self.verts_x, self.verts_y 


class Wad:
	def __init__(self, wadfile):
		"""DOOM wadfile"""
		self.wadfile = wadfile
		self.infotable = {}
		self.header = {}
		self.maptable = {}
		
		# load wadfile header
		packed = self.wadfile.read(12)
		unpacked = unpack('<4sll', packed)
		self.header['ID'], self.header['diroffset'] = unpacked[0], unpacked[2]
		self.header['numlumps'] = unpacked[1]
		
	def get_lump_info(self, lump):
		"""
		Returns a single Lump Info Entry from the directory.
		Currently doesn't return Map Info Entries such as VERTEXES,
		SIDEDEFS, e.t.c.
		
		It will but they will be for the very first map ONLY...
		
		Argument: str
		Returns: dict
		"""
		if self.wadfile.tell() != self.header['diroffset']:
			self.wadfile.seek(self.header['diroffset'])
					
		lumpentry_num = 0
		info = {}
		
		while lumpentry_num < self.header['numlumps']:
			info_packed = self.wadfile.read(16)
			info_unpacked = unpack("<ll8s", info_packed)
			info['lumpofs'] = info_unpacked[0]
			info['lumpsize'] = info_unpacked[1]
			info['lumpname'] = info_unpacked[2].strip(b'\x00')
			# decode...
			info['lumpname'] = info['lumpname'].decode("utf")
			lumpentry_num += 1
			if info['lumpname'] == lump:
				return info
				
		if info['lumpname'] != bytes("lump", "utf8"):
			print('Wadfile contains no such lump: ' + str(lump))

	def load_level_info(self, level):
		"Loads the info entries of the level data"""
		MAPLUMPS = ['LINEDEFS', 'SIDEDEFS', 'VERTEXES']
		entries = {}
		# starting at '1' because we are skipping THINGS
		i = 1
		map_entries_index = 0
		info = {}
		mapname = str(level)
		
		if not self.get_lump_info(level):
			return 'No such MAP!'
			
		self.wadfile.seek(self.header['diroffset'])
		
		while i < self.header['numlumps']:
			info_packed = self.wadfile.read(16)
			info_unpacked = unpack("<ll8s", info_packed)
			info['lumpofs'] = info_unpacked[0]
			info['lumpsize'] = info_unpacked[1]
			info['lumpname'] = info_unpacked[2].strip(b'\x00')
			#decode...
			info['lumpname'] = info['lumpname'].decode("utf")
			i += 1
			if info['lumpname'] == mapname:
				# We are at the beginning of the level entries
				# and the file pointer is PAST the first  level 
				# info entry, which is THINGS. We need the following
				# three entries. LINEDEFS, SIDEDEFS, and VERTEXES in
				# that order. 
				self.maptable[mapname + '_' + info['lumpname']] = LumpInfo(info['lumpofs'], info['lumpsize'])
				while map_entries_index < 9:
					info_packed = self.wadfile.read(16)
					info_unpacked = unpack("<ll8s", info_packed)
					info['lumpofs'] = info_unpacked[0]
					info['lumpsize'] = info_unpacked[1]
					info['lumpname'] = info_unpacked[2].strip(b'\x00')
					# decode...
					info['lumpname'] = info['lumpname'].decode("utf")
					map_entries_index += 1
					i += 1
					self.maptable[mapname + '_' + info['lumpname']] = LumpInfo(info['lumpofs'], info['lumpsize'])

	def build_level(self, mapname):
		"""Assembles level data needed for plotting"""
		lines_offset = self.maptable[mapname + '_LINEDEFS'].offset
		lines_size = self.maptable[mapname + '_LINEDEFS'].size
		verts_offset = self.maptable[mapname + '_VERTEXES'].offset
		verts_size = self.maptable[mapname + '_VERTEXES'].size
		sides_offset = self.maptable[mapname + '_SIDEDEFS'].offset
		sides_size = self.maptable[mapname + '_SIDEDEFS'].size
		
		linedefs = LineDefs(lines_offset, lines_size, self.wadfile)
		vertexes = Vertexes(verts_offset, verts_size, self.wadfile)
		sidedefs = SideDefs(sides_offset, sides_size, self.wadfile)
		
		# Load the data
		linedefs.get_lines()
		verts_x, verts_y = vertexes.get_verts()
		sidedefs.get_sides()
		
		# Assemble
		level = Level(verts_x, verts_y, linedefs, sidedefs)
		
		for line in level.lines.lines:
			start_point = level.vertex_vectors[line['start_point']]
			end_point = level.vertex_vectors[line['end_point']]
			line['line-segment'] = LineSegment.from_points((start_point, end_point))
		"""for line in level.lines.lines:
			line['FRONT_SIDEDEF'] = level.sides[line['frontside_num']]
			line['BACK_SIDEDEF'] = level.sides[line['backside_num']]"""
		"""for line in level.lines.lines:
			if line['backside_num'] == -1:
				line['BACK_SIDEDEF']['SECTOR'] = '-' """
	
		level.map = mapname
		return level


class Plotter:
	"""Handles drawin the map to a turtle window"""
	def __init__(self, mapname, level, tracer=False):
		self.level = level
		self.level_name = mapname
		
		self.ONE_SIDED_COLOR = "GREEN"
		self.TWO_SIDED_COLOR = "RED"
		self.BACKGROUND_COLOR = "BLACK"
		
		self.win = turtle.Turtle()
		self.win.pencolor(self.ONE_SIDED_COLOR)
		self.win.screen.bgcolor(self.BACKGROUND_COLOR)
		self.win.tracer = tracer
		
		
		
		self.scale = planar.Affine.scale((.175))
		self.bbox = planar.BoundingBox.from_points(self.level.vertex_vectors)
		self.offset = planar.Affine.translation((-self.bbox.center))
		
		#For some fucked up reason tracer is changed?
		"""self.tracer = tracer
		if self.tracer is False:
			self.win.tracer(0)
		else:
			self.win.tracer(1)"""
			
	def plot(self, color=None):
		self.PLOTTING = True

		self.win.clear()
		
		if color != None:
			self.ONE_SIDED_COLOR = color[0]
			self.TWO_SIDED_COLOR = color[1]
		while self.PLOTTING:

			screen = self.win.getscreen()
			screen.bgcolor("GREY")
			for linedef in self.level.lines.lines:
				self.win.penup()
			
				if -1 in linedef.values(): self.win.pencolor(self.ONE_SIDED_COLOR)
				else: self.win.pencolor(self.TWO_SIDED_COLOR)
			
				self.win.goto(linedef['line-segment'].start * self.offset * self.scale)
				self.win.pendown()
				self.win.goto(linedef['line-segment'].end * self.offset * self.scale)
				self.win.penup()
			self.win.screen.update()


class Args:
	pass
	



def main():
	cmd_args = Args()
	parser = argparse.ArgumentParser(description='Plots levels from within DOOM wadfiles.')
	parser.add_argument('wadfile', metavar='WADFILE', type=str, help='DOOM wadfile to load.')
	parser.add_argument('--level', metavar='MAPxx/ExMx', type=str, help='Level to display within the wadfile.')
	parser.add_argument('--hide_turtle', metavar='True', type=bool, help='Makes the "turtle" invisible. Can speed up the complex drawings!')
	parser.add_argument('--one_sided_color', metavar='COLOR', type=str, help='One-sided walls pen color. "GREEN", "RED", "BLUE"...!!!')
	parser.add_argument('--two_sided_color', metavar='COLOR', type=str, help='Two-sided walls pen color. "BROWN", "YELLOW"....')
	parser.add_argument('--bgcolor', metavar='COLOR', type=str, help='Canvas background color. "BLACK", "WHITE", "PURPLE"... NOT YET IMPLEMENTED!!!')
	parser.add_argument('--tracer', metavar='Off', type=str, help='Turn the animation off. Instant Plot. "--tracer Off" for no animation.')
	parser.add_argument('--delay', metavar='1-xxx', type=int, help='Sets the delay(speed) of the turtle drawing movement. 0 is normal, 1 is slow and 50 is uber slow!')
	parser.add_argument('--plot_all', metavar='True', type=bool, help='If "True" is provided then all maps within the wadfile will be displayed in sequence. NOT YET IMPLEMENTED!!!')
	args= parser.parse_args(namespace=cmd_args)
	return cmd_args


if __name__ == '__main__':
	cmd_args = main()
	wadfile = open(cmd_args.wadfile, 'rb')
	wad = Wad(wadfile)
	print('Loaded wadfile: ' + cmd_args.wadfile)
	
	args = vars(cmd_args)
	print(args)
	
	if args['level'] == None:
		print('No level specified!')
	else:
		wad.load_level_info(args['level'])
		wad.level = wad.build_level(args['level'])
		
		if args['tracer'] == 'Off':
			anim = False
		else:
			anim = True
		
		plotter = Plotter(args['level'], wad.level, tracer=anim)
		
		if args['delay'] != None:
			plotter.win.screen.delay(args['delay'])
		
		if args['hide_turtle'] == True:
			plotter.win.hideturtle()
			
		if args['bgcolor'] != None:
			plotter.win.screen.bgcolor(args['bgcolor'])
			
		if args['one_sided_color'] != None:
			plotter.ONE_SIDED_COLOR = args['one_sided_color']
			
		if args['two_sided_color'] != None:
			plotter.TWO_SIDED_COLOR = args['two_sided_color']
		
		plotter.win.screen.title('WADdle Plot v0.5 ' + wad.wadfile.name + ' ' + plotter.level_name)
		print('Plotting ' + args['level'] + ' from ' + args['wadfile'])
		if args['one_sided_color'] and args['two_sided_color'] != None:
			colors = (args['one_sided_color'], args['two_sided_color'])
			plotter.plot(color=colors)
		else:
			plotter.plot()
		print('Press ENTER to quit!')
		quit_app = input()
