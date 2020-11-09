#!/usr/bin/env python3

"""Main."""

import sys
from cpu import *

cpu = CPU()

x=1
d=0
if "-d" in sys.argv:
    cpu.debug = True
    x=2
    d=sys.argv.index("-d")

filename = None

if "-f" in sys.argv:
    filename = sys.argv[sys.argv.index("-f")+1]
elif "-x" in sys.argv:
    name = sys.argv[sys.argv.index("-x")+1]
    filename = f"{name}.ls8"
elif len(sys.argv) > x:
    if d==1:
        filename = sys.argv[2]
    else:
        filename = sys.argv[1]

if filename is not None:
    cpu.load(filename)
    cpu.run()
else:
    print(f"Usage: python {sys.argv[0]} [[-f] <filename> | -x <shortname>] [-d]")

exit()
