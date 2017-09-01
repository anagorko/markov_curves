#! /usr/bin/env python
# -*- coding: utf-8 -*-

from graph_tool.all import *
from gi.repository import Gtk, Gdk, GdkPixbuf, GObject

g = Graph()
g.load("../diagrams/81.graphml")

graph_draw(g, pos=fruchterman_reingold_layout(g), vertex_fill_color=g.vp.color)

