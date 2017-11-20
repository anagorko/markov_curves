# Diagram generator for Markov curves

This repository contains software that imlements diagram representations of Markov compacta as described in

G. C. Bell, A. Nagórko "Detecting topological properties of Markov compacta with combinatorial properties of their diagrams"

## Creating new diagrams

Below we describe steps needed to extend `elementary.py` to generate diagrams and sequence for paper

G. C. Bell, A. Nagórko "A construction of {N}\"obeling manifolds of arbitrary weight"

Steps:

* For each production, define a subclass of the `Production` class. Here we defined `NobelingPoint` and `NobelingEdge` productions (this is elementary Markov sequence).
* For each gluing, define a subclass of the `Gluing` class. Here we defined `NobelingGluing_Left` and `NobelingGluing_Right` for gluing `NobelingPoint` production over left and right end of `NobelingEdge`.
* Create subclass of `ElementaryMarkovDiagram` that contains information about the starting graph, productions and gluings.

### Implementation Details

#### Productions

```python
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
```

#### Gluings

```python
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
```

#### Diagram class

```python
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
```

## Installation

Run `make` to generate diagrams.

Software dependencies:

* [graph-tool](https://graph-tool.skewed.de/) 
* `python-termcolor`
