#!/usr/bin/python

import os
import sys
import datetime
import random
import commands
import inspect
from pprint import pprint
import time

#a number of simultanious ib_acme queries to SM
NUM_OF_QUERIES = 1
#Delay between counter sample
COUNTER_DELAY=10
IB_ACME_DELAY = 2

random.seed(os.environ.get('SEED',0))
TEST_NAME = ('%s' % os.path.basename(__file__)).rstrip('.py') 
LOG_DIR='/tmp/%s_counters' %  time.strftime("%Y%m%d_%H%M%S") 

sys.path.append("%s/../" % os.path.dirname(os.path.abspath( __file__ )))
import ssa_tools_utils

rch_global_dict = {}

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-t', dest = 'topology', help = 'Provide file with SSA setup topology', metavar = 'setup_example.ini')
parser.add_option('-s', '--start', dest = 'start', help = 'Starts stress test', metavar = '<counters|ib_acme>')
parser.add_option('-p', '--stop', dest = 'stop', help = 'Stops stress test', metavar = '<counters|ib_acme>')
parser.add_option('-n', '--node', dest = 'node', help = 'Run on specific node', metavar = 'hostname')
parser.add_option('-o', '--output_folder', dest = 'folder', help = 'Output folder', metavar = '/tmp')



(options, _) = parser.parse_args()
if not options.topology:
    parser.print_help()
    sys.exit(1)

rch_global_dict['topology'] = options.topology
if options.folder:
    LOG_DIR = options.folder



def start_counters(nodes):
    status = 0
    counters_log = '%s/`hostname`_counters.log' % LOG_DIR
    ssa_tools_utils.pdsh_run(nodes, 'mkdir -p %s' % LOG_DIR)
    ssa_tools_utils.pdsh_run(nodes, 'nohup %s/server_counters.sh `pgrep "ibacm|ibssa|opensm"` %d > %s &' % ( SSA_SCRIPTS, COUNTER_DELAY, counters_log))
    return 0

def stop_counters(nodes):
    ssa_tools_utils.pdsh_run(nodes, 'killall server_counters.sh 2>/dev/null')
    return 0

def start_ib_acme(nodes):
    ssa_tools_utils.pdsh_run(nodes, 'mkdir -p %s' % LOG_DIR)
    for i in xrange(0, NUM_OF_QUERIES):
        cmd = 'nohup %s/ib_stress.sh %d > /dev/null &' % ( SSA_SCRIPTS, IB_ACME_DELAY)
        ssa_tools_utils.pdsh_run(nodes, cmd)

    return 0


def stop_ib_acme(nodes):
    ssa_tools_utils.pdsh_run(nodes, 'killall ib_stress.sh 2>/dev/null')
    return 0



if __name__ == "__main__":

    status = 0
    rch_global_dict.update(ssa_tools_utils.read_config(rch_global_dict['topology']))

    if options.node:
        nodes = options.node
    else:
        nodes = rch_global_dict['access_nodes'] + rch_global_dict['distrib_nodes'] + rch_global_dict['acm_nodes'] + rch_global_dict['core_nodes']
        if options.start == 'ib_acme' or options.stop == 'ib_acme':
            nodes = rch_global_dict['acm_nodes']

    if options.topology:
        print 'TOPO = %s' % options.topology
    if options.start:
        status = eval("start_%s" % options.start)(nodes)
    if options.stop:
        status = eval("stop_%s" % options.stop)(nodes)

    sys.exit(status)
