#!/usr/bin/python

import os
import sys
import time 
import json
import random
import commands

from  pprint   import pprint
from  optparse import OptionParser

sys.path.append("%s/../" % os.path.dirname(os.path.abspath( __file__ )))
import ssa_tools_utils

########################### CONSTANTS ###################################
(TYPE, STATUS, LID, GID, VERSION) = (0, 1, 2, 3, 4)

ib_acme         = '/usr/local/bin/ib_acme'
retries         = 30
sample_size     = 10
##############################################################

def get_opts ():
    parser = OptionParser()
    parser.add_option('-t', \
                      dest = 'topology', \
                      help = 'Provide file with SSA setup topology', \
                      metavar = 'setup_example.ini')
    
    (options, _) = parser.parse_args()
    if not options.topology:
        parser.print_help()
        sys.exit(1)
    
    if not os.path.exists(options.topology):
        print '%s not found' % options.topology
        sys.exit(1)

    return options

def get_data (topology):
    json_file_str   = commands.getoutput('%s/maintain.py -t %s --setup status|grep Saved' % (ssa_tools_utils.SSA_HOME, topology))
    json_file       = json_file_str.split()[2]
    print '%s/maintain.py -t %s --setup status|grep Saved' % (ssa_tools_utils.SSA_HOME, topology)
    
    json_data   = open(json_file).read()
    data        = json.loads(json_data)
    pprint(data)

    return data

def sanity_test_0 (cores, als, acms, data):

    status = 0

    print 'CORE nodes:'
    for node in cores:
        print '%s %s' % ( node, data[node][LID] )
    
    print 'ACCESS nodes:'
    for node in als:
        print '%s %s' % ( node, data[node][LID] )
    
    print 'ACM nodes:'
    for node in acms:
        print '%s %s' % ( node, data[node][LID] )
    
    #for node in acms:
    #    if node == '': continue
    #    (_, sgid) = ssa_tools_utils.execute_on_remote("/usr/sbin/ibaddr |awk '{print $2}'", node)
    #    slid = data[node][LID]
    #
    #    (_, _) = ssa_tools_utils.execute_on_remote('%s -f g -d %s -s %s -c -v' % (ib_acme, osmgid, sgid), node)
    #    (_, _) = ssa_tools_utils.execute_on_remote('%s -f l -d %s -s %s -c -v' % (ib_acme, osmlid, slid), node)
    #    time.sleep(10)
    #        
    #    print 'Testing %s with %d GIDs' % (node, len(sample_gids))
    #    (rc, out0) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
    #    print 'Before GID test\n', out0
    #    for gid in sample_gids:        
    #        print '%s#  %s -f g -d %s -s %s -c -v' % (node, ib_acme, gid, sgid)
    #        (rc, out0) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
    #        (rc, out) = ssa_tools_utils.execute_on_remote('%s -f g -d %s -s %s -c -v' % (ib_acme, gid, sgid), node)
    #        print out
    #        if out.find('failed') >= 0 and out.find('success') < 0:
    #            print 'ERROR. ACM on %s failed' % node
    #            status = 1    
    #            break
    #        (rc, out1) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
    #        if out1.split()[-4].split(',')[-1] == out0.split()[-4].split(',')[-1]:
    #            print 'ERROR. %s PR was not taken from cache' % node
    #            status = 2
    #            break
    #    (rc, out0) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
    #    print 'After GID test\n', out0
    #
    #print 'Run on %d nodes, each to %d s' % ( len(acms), len(sample_gids))
    
    return status

def main (argv):

    opts = get_opts()

    #
    # Fabric data dictionary format:
    # { "dev-r-vrt-045" : ["acm", "STOPPED", "4", "fe80::2:c903:21:fa01", "1.0.8.1_62e2157"], ... }
    #
    # Dictionary fields for each key:
    # (TYPE, STATUS, LID, GID, VERSION) = (0, 1, 2, 3, 4)
    #
    fabric_data = get_data(opts.topology)

    hostname    = commands.getoutput('hostname')
    slid        = commands.getoutput("/usr/sbin/ibstat |grep -a5 Act|grep Base|awk '{print $NF}'").rstrip('\n')
    osmlid      = commands.getoutput("/usr/sbin/ibstat |grep -a5 Act|grep SM|awk '{print $NF}'").rstrip('\n')
    osmgid      = commands.getoutput("/usr/sbin/saquery --src-to-dst %s:%s|grep dgid" % ( slid, osmlid)).split('.')[-1]
    
    if len(osmlid.split() + slid.split() + osmgid.split() + hostname.split()) != 4 :
            print 'Failed to get basic info'
            print "/usr/sbin/ibstat |grep -a5 Act|grep SM|awk '{print $NF}'\n%s" % osmlid
            print "/usr/sbin/ibstat |grep -a5 Act|grep Base|awk '{print $NF}'\n%s" % slid
            print "/usr/sbin/saquery --src-to-dst %s:%s|grep dgid\n%s" % ( slid, osmlid, osmgid)
            print "hostname\n%s" % hostname
            sys.exit(1)
    
    cores   = []
    als     = []
    acms    = []
    
    status  = 0
    
    for node in fabric_data.keys():
        if fabric_data[node][STATUS] != 'RUNNING':
            continue
        elif fabric_data[node][type] == 'core':
            cores.append(node)
        elif fabric_data[node][type] == 'access':
            als.append(node)
        elif fabric_data[node][TYPE] == 'acm':
            acms.append(node)
    
    if len(cores) < 2 or len(als) < 2 or len(acms) < 2:
        status = 1
    else:
        status = sanity_test_0(cores, als, acms, fabric_data)

    if status == 0:
        print 'PASSED %s' % __file__
    else:
        print 'FAILED %s' % __file__

    sys.exit(status)

if __name__ == "__main__":
        main(sys.argv[1:])
