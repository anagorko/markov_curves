#! /usr/bin/env python
# -*- coding: utf-8 -*-

from graph_tool.all import *
from termcolor import colored
import math

def middle(a,b):
	return [(a[0] + b[0])/2.0, (a[1] + b[1])/2.0]

class Map(object):
	def __init__(self, source = None, target = None):
		if source is None:
			self.source = Graph()
		else:
			self.source = source

		if target is None:
			self.target = Graph()
		else:
			self.target = target

		self.f = dict()

	def get_target(self):
		return self.target

	def get_source(self):
		return self.source

	def inverse(self, b):
		a = []
		for v in self.source.vertices():
			if self.f[v] == b:
				a.append(v)
		return a

	def __setitem__(self, a, b):
		self.f[a] = b

	def __getitem__(self, a):
		return self.f[a]

	def __contains__(self, a):
		return a in self.f

	def __str__(self):
		s = ""
		for v in self.f:
			if not s == "":
				s += ", "
			s += str(v) + " -> "
			if type(self.f[v]) is list:
				s += str(self.f[v][0]) + ":" + str(self.f[v][1])
			else:
				s += str(self.f[v])
		return s

class Production(object):
	top = None
	bottom = None
	bonding_map = None

	@classmethod
	def get_top(cls):
		return cls.top

	@classmethod
	def get_bottom(cls):
		return cls.bottom

	@classmethod
	def get_bonding_map(cls):
		return cls.bonding_map

class Gluing(object):
	bottom_glue = None
	top_glue = None
	source_production = None
	target_production = None

	@classmethod
	def get_top_glue(cls):
		return cls.top_glue

	@classmethod
	def get_bottom_glue(cls):
		return cls.bottom_glue

	@classmethod
	def get_source_production(cls):
		return cls.source_production
	@classmethod
	def get_target_production(cls):
		return cls.target_production

class Decomposition(object):
	def __init__(self, cls):
		self.cls = cls
		self.assembly_graph = None
		self.upper_chart = None
		self.lower_chart = None

		self.bottom_graph = None
		self.top_graph = None
		self.bonding_map = None

	def __str__(self):
		return "Decomposition"

	def glue_in(self, v):
		"""Glue into top graph a subgraph corresponding to top graph of a production corresponding to assembly graph vertex v"""

		if v in self.upper_chart:
			return

		vertex_production = self.cls.productions[self.assembly_graph.vertex_properties["productions"][v]]

		self.upper_chart[v] = Map(vertex_production.get_top(), self.upper_graph)

		# Chart vertices that are already glued in
		for w in self.assembly_graph.get_in_neighbours(v):
			self.glue_in(w)
			e = self.assembly_graph.edge(w, v)

			for u in self.upper_chart[w].get_source().vertices():
				gl = self.cls.gluings[self.assembly_graph.edge_properties["gluings"][e]]

				self.upper_chart[v][gl.get_top_glue()[u]] = self.upper_chart[w][u]

		# Add new vertices
		for w in self.upper_chart[v].get_source().vertices():
			if not w in self.upper_chart[v]:
				x = self.upper_chart[v][w] = self.upper_graph.add_vertex()
				# update bonding map
				if type(vertex_production.get_bonding_map()[w]) is list:
					bx0 = self.lower_chart[v][vertex_production.get_bonding_map()[w][0]]
					bx1 = self.lower_chart[v][vertex_production.get_bonding_map()[w][1]]
					bx = [ bx0, bx1 ]
				else:
					bx = self.lower_chart[v][vertex_production.get_bonding_map()[w]]
				self.bonding_map[x] = bx
				# save relative position
				self.upper_graph.vp.relpos[x] = self.upper_chart[v].get_source().vp.pos[w]

		# Add new edges
		for e in self.upper_chart[v].get_source().edges():
			if self.upper_graph.edge(self.upper_chart[v][e.source()], self.upper_chart[v][e.target()]) is None:
				self.upper_graph.add_edge(self.upper_chart[v][e.source()], self.upper_chart[v][e.target()])

	def assemble(self):
		"""Create upper graph, upper charts and bonding map of the decomposition using assembly graph and lower charts"""

		self.upper_chart = dict()
		self.upper_graph = Graph(directed=False)
		self.upper_graph.vp["relpos"] = self.upper_graph.new_vertex_property("vector<double>")

		self.bonding_map = Map(self.upper_graph, self.bottom_graph)

		for v in self.assembly_graph.vertices():
			self.glue_in(v)


	def layout(self, d1, d2):
		if "pos" in self.upper_graph.vp:
			return self.upper_graph.vp.pos

		self.upper_graph.vp["pos"] = self.upper_graph.new_vertex_property("vector<double>")

		for v in self.upper_graph.vertices():
			bv = self.bonding_map[v]
			if type(bv) is list:
				abs_pos = middle(self.bottom_graph.vp.pos[bv[0]], self.bottom_graph.vp.pos[bv[1]])
			else:
				abs_pos = self.bottom_graph.vp.pos[bv]

			rel_pos = self.upper_graph.vp.relpos[v]

			p = [0,0]
			p[0] = abs_pos[0] + rel_pos[0]*d1[0] + rel_pos[1]*d2[0]
			p[1] = abs_pos[1] + rel_pos[0]*d1[1] + rel_pos[1]*d2[1]

			self.upper_graph.vp.pos[v] = p

		return self.upper_graph.vp.pos

class MarkovDiagram(object):
	@classmethod
	def get_starting_graph(cls):
		return cls.starting_graph

	@classmethod
	def get_productions(cls):
		return cls.productions

	@classmethod
	def get_gluings(cls):
		return cls.gluings

class ElementaryMarkovDiagram(MarkovDiagram):
	@classmethod
	def get_vertex_production(cls):
		return None

	@classmethod
	def get_edge_production(cls):
		return None

	@classmethod
	def decompose(cls, g):
		"""Create assembly graph and lower charts for given bottom graph"""
		d = Decomposition(cls)
		d.bottom_graph = g

		# Create assembly graph and lower charts
		ag = Graph()
		productions = ag.new_vertex_property("string")
		gluings = ag.new_edge_property("string")
 		lower_chart = dict()
		inverse_lower_chart = dict()

		ag.vertex_properties["productions"] = productions
		ag.edge_properties["gluings"] = gluings

		for v in g.vertices():
			w = ag.add_vertex()
			inverse_lower_chart[v] = w
			productions[w] = "V"

			lower_chart[w] = Map(cls.productions["V"].get_bottom(), g)
			lower_chart[w][cls.productions["V"].get_bottom().get_vertices()[0]] = v

		for e in g.edges():
			w = ag.add_vertex()

			agv_s = inverse_lower_chart[e.source()]
			agv_t = inverse_lower_chart[e.target()]

			productions[w] = "E"

			f = ag.add_edge(agv_s, w)
			gluings[f] = "L"
			f = ag.add_edge(agv_t, w)
			gluings[f] = "R"

			bottom_production_vertex = cls.productions["V"].get_bottom().get_vertices()[0]

			edge = cls.productions["E"].get_bottom()
			left_vertex = cls.gluings["L"].get_bottom_glue()[bottom_production_vertex]
			right_vertex = cls.gluings["R"].get_bottom_glue()[bottom_production_vertex]

			lower_chart[w] = Map(edge, g)
			lower_chart[w][left_vertex] = lower_chart[agv_s][bottom_production_vertex]
			lower_chart[w][right_vertex] = lower_chart[agv_t][bottom_production_vertex]

		d.assembly_graph = ag
		d.lower_chart = lower_chart
		d.upper_chart = None

		return d

class MarkovSequence(object):
	"""Holds a (finite) inverse sequence with corresponding decompositions"""

##########################################################################################################################
# Nobeling n=1, kappa=3
##########################################################################################################################

class NobelingPoint(Production):
	@classmethod
	def init(cls):
		cls.top = top = Graph()
		a, b, c = top.add_vertex(), top.add_vertex(), top.add_vertex()
		top.add_edge(a, b)
		top.add_edge(b, c)
		top.add_edge(a, c)
		pos = top.new_vertex_property("vector<double>")
		pos[a] = (-0,0)
		pos[b] = (1,0.2)
		pos[c] = (0.8, 0.6)
		top.vp["pos"] = pos

		cls.bottom = bot = Graph()
		A = bot.add_vertex()
		pos = bot.new_vertex_property("vector<double>")
		pos[A] = (0, 0)
		bot.vp["pos"] = pos

		cls.bonding_map = Map(bot, top)
		cls.bonding_map[a] = A
		cls.bonding_map[b] = A
		cls.bonding_map[c] = A
NobelingPoint.init()

class NobelingEdge(Production):
	@classmethod
	def init(cls):
		cls.top = top = Graph()
		a, b, c, d, e, f = top.add_vertex(), top.add_vertex(), top.add_vertex(), top.add_vertex(), top.add_vertex(), top.add_vertex()
		top.add_edge_list([(a,b), (b,c), (a,c), (d,e), (d,f), (e,f), (a,d), (a,e), (a,f), (b,d), (b,e), (b,f), (c,d), (c,e), (c,f)])

		pos = top.new_vertex_property("vector<double>")
		pos[a] = (-1,0)
		pos[b] = (0,0.2)
		pos[c] = (-0.2, 0.6)
		pos[d] = (1,0)
		pos[e] = (2,0.2)
		pos[f] = (1.8, 0.6)
		top.vp["pos"] = pos

		cls.bottom = bot = Graph()
		A,B = bot.add_vertex(), bot.add_vertex()
		pos = bot.new_vertex_property("vector<double>")
		pos[A] = (-1, 0)
		pos[B] = (1, 0)
		bot.vp["pos"] = pos

		cls.bonding_map = Map(bot, top)
		cls.bonding_map[a] = A
		cls.bonding_map[b] = A
		cls.bonding_map[c] = A
		cls.bonding_map[d] = B
		cls.bonding_map[e] = B
		cls.bonding_map[f] = B
NobelingEdge.init()

class NobelingGluing_Left(Gluing):
	@classmethod
	def init(cls):
		g1 = NobelingPoint.get_top()
		g2 = NobelingEdge.get_top()

		cls.top_glue = tg = Map(g1, g2)
		tg[g1.get_vertices()[0]] = g2.get_vertices()[0]
		tg[g1.get_vertices()[1]] = g2.get_vertices()[1]
		tg[g1.get_vertices()[2]] = g2.get_vertices()[2]

		g1 = NobelingPoint.get_bottom()
		g2 = NobelingEdge.get_bottom()
		cls.bottom_glue = bg = Map(g1, g2)
		bg[g1.get_vertices()[0]] = g2.get_vertices()[0]
NobelingGluing_Left.init()

class NobelingGluing_Right(Gluing):
	@classmethod
	def init(cls):
		g1 = NobelingPoint.get_top()
		g2 = NobelingEdge.get_top()

		cls.top_glue = tg = Map(g1, g2)
		tg[g1.get_vertices()[0]] = g2.get_vertices()[3]
		tg[g1.get_vertices()[1]] = g2.get_vertices()[4]
		tg[g1.get_vertices()[2]] = g2.get_vertices()[5]

		g1 = NobelingPoint.get_bottom()
		g2 = NobelingEdge.get_bottom()
		cls.bottom_glue = bg = Map(g1, g2)
		bg[g1.get_vertices()[0]] = g2.get_vertices()[1]
NobelingGluing_Right.init()

class NobelingDiagram(ElementaryMarkovDiagram):
	@classmethod
	def init(cls):
		cls.starting_graph = g = Graph(directed=False)
		pos = g.new_vertex_property("vector<double>")
		a=g.add_vertex()
		pos[a] = (0,1)
		b=g.add_vertex()
		pos[b] = (0,-1)
		g.add_edge(a,b)
		g.vp["pos"] = pos

		cls.productions = {
			"V": NobelingPoint,
			"E": NobelingEdge
		}
		cls.gluings = {
		 	"L": NobelingGluing_Left, 
			"R": NobelingGluing_Right
		}
NobelingDiagram.init()


##########################################################################################################################
# Menger Curve "18" Sequence
##########################################################################################################################

class Production_1(Production):
	@classmethod
	def init(cls):
		cls.top = top = Graph()
		a, b = top.add_vertex(), top.add_vertex()
		top.add_edge(a, b)
		pos = top.new_vertex_property("vector<double>")
		pos[a] = (-1,0)
		pos[b] = (1,0)
		top.vp["pos"] = pos

		cls.bottom = bot = Graph()
		A = bot.add_vertex()
		pos = bot.new_vertex_property("vector<double>")
		pos[A] = (0, 0)
		bot.vp["pos"] = pos

		cls.bonding_map = Map(bot, top)
		cls.bonding_map[a] = A
		cls.bonding_map[b] = A
Production_1.init()

class Production_8(Production):
	@classmethod
	def init(cls):
		cls.top = top = Graph()
		a,b,c,d,e,f = top.add_vertex(), top.add_vertex(), top.add_vertex(), top.add_vertex(), top.add_vertex(), top.add_vertex()
		top.add_edge_list([(a,b), (e,f), (a,c), (b,d), (c,d), (c,e), (d,f) ])
		pos = top.new_vertex_property("vector<double>")
		pos[a] = (-1, -1)
		pos[b] = (1, -1)
		pos[c] = (-1, 0)
		pos[d] = (1, 0)
		pos[e] = (-1,1)
		pos[f] = (1,1)
		top.vp["pos"] = pos

		cls.bottom = bot = Graph()
		A, B = bot.add_vertex(), bot.add_vertex()
		bot.add_edge(A, B)
		pos = bot.new_vertex_property("vector<double>")
		pos[A] = (0, 0)
		pos[B] = (1, 0)
		bot.vp["pos"] = pos

		cls.bonding_map = Map(top, bot)
		cls.bonding_map[a] = A
		cls.bonding_map[b] = A
		cls.bonding_map[c] = [A, B]
		cls.bonding_map[d] = [A, B]
		cls.bonding_map[e] = B
		cls.bonding_map[f] = B
Production_8.init()

class Gluing_18_Left(Gluing):
	@classmethod
	def init(cls):
		g1 = Production_1.get_top()
		g2 = Production_8.get_top()

		cls.top_glue = tg = Map(g1, g2)
		tg[g1.get_vertices()[0]] = g2.get_vertices()[0]
		tg[g1.get_vertices()[1]] = g2.get_vertices()[1]

		g1 = Production_1.get_bottom()
		g2 = Production_8.get_bottom()
		cls.bottom_glue = bg = Map(g1, g2)
		bg[g1.get_vertices()[0]] = g2.get_vertices()[0]
Gluing_18_Left.init()

class Gluing_18_Right(Gluing):
	@classmethod
	def init(cls):
		g1 = Production_1.get_top()
		g2 = Production_8.get_top()

		cls.top_glue = tg = Map(g1, g2)
		tg[g1.get_vertices()[0]] = g2.get_vertices()[4]
		tg[g1.get_vertices()[1]] = g2.get_vertices()[5]

		g1 = Production_1.get_bottom()
		g2 = Production_8.get_bottom()
		cls.bottom_glue = bg = Map(g1, g2)
		bg[g1.get_vertices()[0]] = g2.get_vertices()[1]
Gluing_18_Right.init()

class Menger18Diagram(ElementaryMarkovDiagram):
	@classmethod
	def init(cls):
		cls.starting_graph = g = Graph(directed=False)
		pos = g.new_vertex_property("vector<double>")
		a=g.add_vertex()
		pos[a] = (-1,0)
		b=g.add_vertex()
		pos[b] = (1,0)
		g.add_edge(a,b)
		g.vp["pos"] = pos

		cls.productions = {
			"V": Production_1,
			"E": Production_8
		}
		cls.gluings = {
		 	"L": Gluing_18_Left, 
			"R": Gluing_18_Right
		}
Menger18Diagram.init()

##########################################################################################################################
# Diamond curve
##########################################################################################################################

class Production_Diamond(Production):
	@classmethod
	def init(cls):
		cls.top = top = Graph()
		a, b, c, d = top.add_vertex(), top.add_vertex(), top.add_vertex(), top.add_vertex()
		top.add_edge_list([(a, b), (a,c), (b,d), (c,d)])
		pos = top.new_vertex_property("vector<double>")
		pos[a] = (0, 1)
		pos[b] = (-1, 0)
		pos[c] = (1, 0)
		pos[d] = (0, -1)
		top.vp["pos"] = pos

		cls.bottom = bot = Graph()
		A = bot.add_vertex()
		B = bot.add_vertex()

		cls.bonding_map = Map(bot, top)
		cls.bonding_map[a] = A
		cls.bonding_map[b] = [A,B]
		cls.bonding_map[c] = [A,B]
		cls.bonding_map[d] = B
Production_Diamond.init()

class Production_VertexID(Production):
	@classmethod
	def init(cls):
		cls.top = top = Graph()
		a = top.add_vertex()
		pos = top.new_vertex_property("vector<double>")
		pos[a] = (0, 0)
		top.vp["pos"] = pos

		cls.bottom = bot = Graph()
		A = bot.add_vertex()
		cls.bonding_map = Map(bot, top)
		cls.bonding_map[a] = A
Production_VertexID.init()

class Gluing_Diamond_Left(Gluing):
	@classmethod
	def init(cls):
		g1 = Production_VertexID.get_top()
		g2 = Production_Diamond.get_top()

		cls.top_glue = tg = Map(g1, g2)
		tg[g1.get_vertices()[0]] = g2.get_vertices()[0]

		g1 = Production_VertexID.get_bottom()
		g2 = Production_Diamond.get_bottom()
		cls.bottom_glue = bg = Map(g1, g2)
		bg[g1.get_vertices()[0]] = g2.get_vertices()[0]
Gluing_Diamond_Left.init()

class Gluing_Diamond_Right(Gluing):
	@classmethod
	def init(cls):
		g1 = Production_VertexID.get_top()
		g2 = Production_Diamond.get_top()

		cls.top_glue = tg = Map(g1, g2)
		tg[g1.get_vertices()[0]] = g2.get_vertices()[3]

		g1 = Production_VertexID.get_bottom()
		g2 = Production_Diamond.get_bottom()
		cls.bottom_glue = bg = Map(g1, g2)
		bg[g1.get_vertices()[0]] = g2.get_vertices()[1]
Gluing_Diamond_Right.init()

class DiamondDiagram(ElementaryMarkovDiagram):
	@classmethod
	def init(cls):
		cls.starting_graph = g = Graph(directed=False)
		a, b = g.add_vertex(), g.add_vertex()
		g.add_edge(a,b)

		pos = g.new_vertex_property("vector<double>")
		pos[a] = (0, -1)
		pos[b] = (0, 1)
		g.vp["pos"] = pos

		cls.productions = {
			"V": Production_VertexID,
			"E": Production_Diamond
		}
		cls.gluings = {
		 	"L": Gluing_Diamond_Left, 
			"R": Gluing_Diamond_Right
		}
DiamondDiagram.init()

##########################################################################################################################
# Cantor Set
##########################################################################################################################

class DoubleVertex(Production):
	@classmethod
	def init(cls):
		cls.top = top = Graph(directed=False)
		a, b = top.add_vertex(), top.add_vertex()

		pos = top.new_vertex_property("vector<double>")
		pos[a] = (0, -1)
		pos[b] = (0, 1)
		top.vp["pos"] = pos

		cls.bottom = bot = Graph(directed=False)
		A = bot.add_vertex()

		cls.bonding_map = Map(bot, top)
		cls.bonding_map[a] = A
		cls.bonding_map[b] = A
DoubleVertex.init()

class CantorDiagram(ElementaryMarkovDiagram):
	@classmethod
	def init(cls):
		cls.starting_graph = g = Graph()
		a = g.add_vertex()
		pos = g.new_vertex_property("vector<double>")
		pos[a] = (0, 0)
		g.vp["pos"] = pos

		cls.productions = {
			"V": DoubleVertex,
			"E": None
		}
		cls.gluings = {
		 	"L": None, 
			"R": None
		}
CantorDiagram.init()

##########################################################################################################################
# Join of two Cantor Sets
##########################################################################################################################

class XtoI(Production):
	@classmethod
	def init(cls):
		cls.top = top = Graph(directed=False)
		a, b, c, d = top.add_vertex(), top.add_vertex(), top.add_vertex(), top.add_vertex()
		#top.add_edge_list([(a, d), (a,c), (b,c), (b,d)])
		top.add_edge_list([(a,b),(c,d), (a,d), (b,c)])
		pos = top.new_vertex_property("vector<double>")
		pos[a] = (0, 1)
		pos[b] = (1, 1)
		pos[c] = (0, 0)
		pos[d] = (1, 0)
		top.vp["pos"] = pos

		cls.bottom = bot = Graph(directed=False)
		A = bot.add_vertex()
		B = bot.add_vertex()

		cls.bonding_map = Map(bot, top)
		cls.bonding_map[a] = A
		cls.bonding_map[b] = A
		cls.bonding_map[c] = B
		cls.bonding_map[d] = B
XtoI.init()

class Gluing_Join_Left(Gluing):
	@classmethod
	def init(cls):
		g1 = DoubleVertex.get_top()
		g2 = XtoI.get_top()

		cls.top_glue = tg = Map(g1, g2)
		tg[g1.get_vertices()[0]] = g2.get_vertices()[0]
		tg[g1.get_vertices()[1]] = g2.get_vertices()[2]

		g1 = DoubleVertex.get_bottom()
		g2 = XtoI.get_bottom()
		cls.bottom_glue = bg = Map(g1, g2)
		bg[g1.get_vertices()[0]] = g2.get_vertices()[0]
Gluing_Join_Left.init()

class Gluing_Join_Right(Gluing):
	@classmethod
	def init(cls):
		g1 = DoubleVertex.get_top()
		g2 = XtoI.get_top()

		cls.top_glue = tg = Map(g1, g2)
		tg[g1.get_vertices()[0]] = g2.get_vertices()[1]
		tg[g1.get_vertices()[1]] = g2.get_vertices()[3]

		g1 = DoubleVertex.get_bottom()
		g2 = XtoI.get_bottom()
		cls.bottom_glue = bg = Map(g1, g2)
		bg[g1.get_vertices()[0]] = g2.get_vertices()[0]
Gluing_Join_Right.init()

class CantorJoinDiagram(ElementaryMarkovDiagram):
	@classmethod
	def init(cls):
		cls.starting_graph = g = Graph(directed=False)
		a,b = g.add_vertex(), g.add_vertex()
		g.add_edge(a,b)
		pos = g.new_vertex_property("vector<double>")
		pos[a] = (0, 0)
		pos[b] = (0, 1)
		g.vp["pos"] = pos

		cls.productions = {
			"V": DoubleVertex,
			"E": XtoI
		}
		cls.gluings = {
		 	"L": Gluing_Join_Left, 
			"R": Gluing_Join_Right
		}
CantorJoinDiagram.init()


############################

def generate_Cantor_diagram(w, h):
	n = 6
	m = [ 1.0, 0.4, 0.4 * 0.4, 0.4 * 0.4 * 0.4, 0.4 * 0.4 * 0.4 * 0.3, 0.4 * 0.4 * 0.4 * 0.3 * 0.3 ]
	g = dict()
	i = 0
	g[i] = CantorDiagram.starting_graph

	while i < n:
		d = CantorDiagram.decompose(g[i])
		d.assemble()
		d.layout((0,m[i]), (0,m[i]))
		i = i + 1
		g[i] = d.upper_graph

	i = 0
	while i < n:
		size = g[i].new_vertex_property("float")
		color = g[i].new_vertex_property("vector<float>")

		for v in g[i].vertices():
			size[v] = 16
			if i == 5:
				size[v] = 12

			color[v] = [0., 0., 0., 1.]

			g[i].vp.pos[v][0] = w/2
			g[i].vp.pos[v][1] = g[i].vp.pos[v][1] * h/3.34 + h/2

		graph_draw(g[i], vertex_size=size, vertex_color=color, vertex_fill_color=color, pos=g[i].vp.pos, output_size=(w,h), fit_view=False, output="diagrams/cantor_"+str(i)+".png")
		i = i + 1

def generate_CantorJoin_diagram(w, h):
	n = 6
	m = [ 1.0, 0.4, 0.4 * 0.4, 0.4 * 0.4 * 0.4, 0.4 * 0.4 * 0.4 * 0.3, 0.4 * 0.4 * 0.4 * 0.3 * 0.3 ]
	sz = [ 0.02, 0.02, 0.015, 0.015, 0.002, 0.001 ]
	g = dict()
	i = 0
	g[i] = CantorJoinDiagram.starting_graph

	while i < n:
		d = CantorJoinDiagram.decompose(g[i])
		d.assemble()
		d.layout((m[i],0), (m[i],0))
		i = i + 1
		g[i] = d.upper_graph

	i = 0
	while i < n:
		size = g[i].new_vertex_property("float")
		color = g[i].new_vertex_property("vector<float>")

		for v in g[i].vertices():
			size[v] = sz[i] * w

			color[v] = [0., 0., 0., 1.]

			g[i].vp.pos[v][0] = g[i].vp.pos[v][0] * w/3.34 + w/2
			g[i].vp.pos[v][1] = g[i].vp.pos[v][1] * h/3.34 + h/2

		graph_draw(g[i], vertex_size=size, vertex_color=color, vertex_fill_color=color, pos=g[i].vp.pos, output_size=(w,h), fit_view=False, output="diagrams/cantor_join_"+str(i)+".png")
		i = i + 1

def generate_Menger18_diagram(w, h):
	n = 5
	m = [ 1.0, 0.4, 0.4 * 0.4, 0.4 * 0.4 * 0.3, 0.4 * 0.4 * 0.3 * 0.3, 0.4 * 0.4 * 0.3 * 0.3 * 0.3 ]
	dr = [ [0,1], [2,3], [1,4], [-1, 3], [-3,2]]
	sz = [ 0.02, 0.02, 0.015, 0.015, 0.01, 0.005 ]
	g = dict()
	i = 0
	g[i] = Menger18Diagram.starting_graph

	while i < n:
		d = Menger18Diagram.decompose(g[i])
		d.assemble()
		z = dr[i]
		zn = math.sqrt(z[0]*z[0] + z[1]*z[1])
		z[0] = z[0]/zn * m[i]
		z[1] = z[1]/zn * m[i]
		d.layout(z,z)
		i = i + 1
		g[i] = d.upper_graph

	i = 0
	while i <= n:
		size = g[i].new_vertex_property("float")
		color = g[i].new_vertex_property("vector<float>")
		width = g[i].new_edge_property("float")

		for v in g[i].vertices():
			size[v] = sz[i] * w
	
			color[v] = [0., 0., 0., 1.]

			g[i].vp.pos[v][0] = g[i].vp.pos[v][0] * w/3.34 + w/2
			g[i].vp.pos[v][1] = g[i].vp.pos[v][1] * h/3.34 + h/2

		for e in g[i].edges():
			width[e] = sz[i] * w * 0.4

		graph_draw(g[i], edge_pen_width=width, vertex_size=size, vertex_color=color, vertex_fill_color=color, pos=g[i].vp.pos, output_size=(w,h), fit_view=False, output="diagrams/menger_"+str(i)+".png")
		i = i + 1

def generate_Diamond_diagram(w, h):
	n = 5
	m = [ 1.0, 0.2, 0.2 * 0.2, 0.2 * 0.2 * 0.2, 0.2 * 0.2 * 0.2 * 0.2, 0.2 * 0.2 * 0.2 * 0.2 * 0.2 ]
	sz = [ 0.02, 0.02, 0.02, 0.015, 0.01, 0.02 ]
	g = dict()
	i = 0
	g[i] = DiamondDiagram.starting_graph

	while i < n:
		d = DiamondDiagram.decompose(g[i])
		d.assemble()
		z = [m[i], 0]
		d.layout(z,z)
		i = i + 1
		g[i] = d.upper_graph

	i = 0
	while i <= n:
		size = g[i].new_vertex_property("float")
		color = g[i].new_vertex_property("vector<float>")
		width = g[i].new_edge_property("float")

		for v in g[i].vertices():
			size[v] = sz[i] * w
	
			color[v] = [0., 0., 0., 1.]

			g[i].vp.pos[v][0] = g[i].vp.pos[v][0] * w/3.34 + w/2
			g[i].vp.pos[v][1] = g[i].vp.pos[v][1] * h/3.34 + h/2

		for e in g[i].edges():
			width[e] = sz[i] * w * 0.4

		graph_draw(g[i], edge_pen_width=width, vertex_size=size, vertex_color=color, vertex_fill_color=color, pos=g[i].vp.pos, output_size=(w,h), fit_view=False, output="diagrams/diamond_"+str(i)+".png")
		graph_draw(g[i], edge_pen_width=width, vertex_size=size, vertex_color=color, vertex_fill_color=color, pos=sfdp_layout(g[i]), output_size=(w,h), fit_view=True, output="diagrams/diamond_sfdp_"+str(i)+".png")
		i = i + 1


def generate_Nobeling_diagram(w, h):
	n = 3
	m = [ 1.0, 0.4, 0.4 * 0.4, 0.4 * 0.4 * 0.4, 0.4 * 0.4 * 0.4 * 0.3, 0.4 * 0.4 * 0.4 * 0.3 * 0.3 ]
	sz = [ 0.02, 0.02, 0.015, 0.015, 0.002, 0.001 ]
	g = dict()
	i = 0
	g[i] = NobelingDiagram.starting_graph

	lay = [ [(1.0, 0.0), (0.0, 0.8)], [(1.0, 0.0), (0.0, 0.8)], [(0.0, 1.0), (0.8, 0.0)] ]

	while i < n:
		d = NobelingDiagram.decompose(g[i])
		d.assemble()
		d.layout((lay[i][0][0]*m[i],lay[i][0][1]*m[i]), (lay[i][1][0]*m[i],lay[i][1][1]*m[i]))
		i = i + 1
		g[i] = d.upper_graph

	i = 0
	while i < n:
		print i
		size = g[i].new_vertex_property("float")
		color = g[i].new_vertex_property("vector<float>")
		width = g[i].new_edge_property("float")

		for v in g[i].vertices():
			size[v] = sz[i] * w

			color[v] = [0., 0., 0., 1.]

			g[i].vp.pos[v][0] = g[i].vp.pos[v][0] * w/3.34 + w/2
			g[i].vp.pos[v][1] = g[i].vp.pos[v][1] * h/3.34 + h/2

		for e in g[i].edges():
			width[e] = sz[i] * w * 0.4

		graph_draw(g[i], vertex_size=size, vertex_color=color, vertex_fill_color=color, pos=g[i].vp.pos, output_size=(w,h), fit_view=False, output="diagrams/nobeling_"+str(i)+".png")
		graph_draw(g[i], edge_pen_width=width, vertex_size=size, vertex_color=color, vertex_fill_color=color, pos=sfdp_layout(g[i]), output_size=(w,h), fit_view=True, output="diagrams/nobeling_sfdp_"+str(i)+".png")
		i = i + 1
	
############################

print colored("Elementary Markov Sequence Generator", 'blue')

#generate_CantorJoin_diagram(1000,1000)
#generate_Cantor_diagram(40,1600)
#generate_Menger18_diagram(1000,1000)
#generate_Diamond_diagram(1000,1000)
generate_Nobeling_diagram(1000,1000)

