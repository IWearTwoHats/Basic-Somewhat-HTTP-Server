#!/usr/bin/env python3

import sys
from htmlificate import HTML

args = sys.argv[1:]
current = None
for arg in args:
	if current:
		if current == 'path':
			path = arg
			current = None
	else:
		if arg == '--path':
			current = 'path'

h = HTML()

h.start_tag('html')
h.start_tag('head')
h.end_tag() # head
h.start_tag('body')

h.h1(path)

h.end_tag() # body
h.end_tag() # html

print(h.get())
exit(0)
