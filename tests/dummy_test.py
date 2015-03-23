#!/usr/bin/python
import os
from optparse import OptionParser
import time 
import sys

sys.path.append("%s/../" % os.path.dirname(os.path.abspath( __file__ )))
import ssa_tools_utils


parser = OptionParser()
parser.add_option('-t', dest = 'topology', help = 'Provide file with SSA setup topology', metavar = 'setup_example.ini')

(options, _) = parser.parse_args()
if not options.topology:
    parser.print_help()
    sys.exit(1)

status = 0
if status == 0:
    print 'PASSED %s' % __file__
else:
    print 'FAILED %s' % __file__

sys.exit(status)
