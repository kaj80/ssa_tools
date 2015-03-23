#!/usr/bin/python
import random
import commands
import json
from  pprint import pprint
import sys
import os
from optparse import OptionParser
import time 

########################### CONSTANTS ###################################
random.seed(os.environ.get('SEED',0))

ib_acme = '/usr/local/bin/ib_acme'
(TYPE, STATUS, LID, GID, VERSION) = (0,1,2,3,4)
retries = 30
sample_size = 10
##############################################################
sys.path.append("%s/../" % os.path.dirname(os.path.abspath( __file__ )))
import ssa_tools_utils



acms = []

parser = OptionParser()
parser.add_option('-t', dest = 'topology', help = 'Provide file with ssa_tools_utils.SSA setup topology', metavar = 'setup_example.ini')
parser.add_option('-l', '--local', dest = 'local', help = 'Run acm test on local host', action = 'store_true')
parser.add_option('-j', '--json', dest = 'json', help = 'Provide JSON file from maintain --setup status', metavar = 'setup.ini_status.json')

(options, _) = parser.parse_args()
if not options.topology:
    parser.print_help()
    sys.exit(1)
if not os.path.exists(options.topology):
    print '%s not found' % options.topology
    sys.exit(1)

if options.local:
    try:
        import paramiko
    except:
        if not options.json:
            print 'paramiko is not installed.\n.Please provide JSON file'
            sys.exit(1)

if not options.json:            
    o = commands.getoutput('%s/maintain.py -t %s --setup status|grep Saved' % (ssa_tools_utils.SSA_HOME, options.topology))
    print '%s/maintain.py -t %s --setup status|grep Saved' % (ssa_tools_utils.SSA_HOME, options.topology)
    json_file = o.split()[2]
else:
    if os.path.exists(options.json):
        json_file = '/tmp/%s' % os.path.basename(options.json)
        os.system('cp %s %s' % ( options.json, json_file))
    else:
        print '%s not found' % options.json
        sys.exit(1)

json_data=open(json_file).read()
data = json.loads(json_data)
pprint(data)

osmlid = commands.getoutput("/usr/sbin/ibstat |grep -a5 Act|grep SM|awk '{print $NF}'").rstrip('\n')
slid =  commands.getoutput("/usr/sbin/ibstat |grep -a5 Act|grep Base|awk '{print $NF}'").rstrip('\n')
osmgid = commands.getoutput("/usr/sbin/saquery --src-to-dst %s:%s|grep dgid" % ( slid, osmlid)).split('.')[-1]
hostname = commands.getoutput('hostname')
if len(osmlid.split() + slid.split() + osmgid.split() + hostname.split()) !=4 :
        print 'Failed to get basic info'
        print "/usr/sbin/ibstat |grep -a5 Act|grep SM|awk '{print $NF}'\n%s" % osmlid
        print "/usr/sbin/ibstat |grep -a5 Act|grep Base|awk '{print $NF}'\n%s" % slid
        print "/usr/sbin/saquery --src-to-dst %s:%s|grep dgid\n%s" % ( slid, osmlid, osmgid)
        print "hostname\n%s" % hostname
        sys.exit(1)

status = 0
lids = []
gids = []
for node in data.keys():
    if data[node][STATUS] != 'RUNNING':
        continue
    elif data[node][TYPE] == 'acm':
        acms.append(node)
    try:
        lids.append(int(data[node][LID]))
        gids.append(data[node][GID].encode('ascii','ignore'))
    except:
        pass

if len(acms) == 0:
    status = 1

if options.local:
    acms = [hostname,]
    sample_gids = gids
    sample_lids = lids
else:
    sample_gids = random.sample(gids, min(len(gids), sample_size))
    sample_lids = random.sample(lids, min(len(lids), sample_size))

for node in acms:
    slid = data[node][LID]
    print '%s %s' % ( node, slid )

for node in acms:
    if node == '': continue
    (_, sgid) = ssa_tools_utils.execute_on_remote("/usr/sbin/ibaddr |awk '{print $2}'", node)
    slid = data[node][LID]

    (_, _) = ssa_tools_utils.execute_on_remote('%s -f g -d %s -s %s -c -v' % (ib_acme, osmgid, sgid), node)
    (_, _) = ssa_tools_utils.execute_on_remote('%s -f l -d %s -s %s -c -v' % (ib_acme, osmlid, slid), node)
    time.sleep(10)
        
    print 'Testing %s with %d GIDs' % (node, len(sample_gids))
    (rc, out0) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
    print 'Before GID test\n', out0
    for gid in sample_gids:        
        print '%s#  %s -f g -d %s -s %s -c -v' % (node, ib_acme, gid, sgid)
        (rc, out0) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
        (rc, out) = ssa_tools_utils.execute_on_remote('%s -f g -d %s -s %s -c -v' % (ib_acme, gid, sgid), node)
        print out
        if out.find('failed') >= 0 and out.find('success') < 0:
            print 'ERROR. ACM on %s failed' % node
            status = 1    
            break
        (rc, out1) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
        if out1.split()[-4].split(',')[-1] == out0.split()[-4].split(',')[-1]:
            print 'ERROR. %s PR was not taken from cache' % node
            status = 2
            break
    (rc, out0) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
    print 'After GID test\n', out0
print 'Run on %d nodes, each to %d s' % ( len(acms), len(sample_gids))
if status == 0:
    print 'PASSED %s' % __file__
else:
    print 'FAILED %s' % __file__


for node in acms:
    if node == '': continue
    slid = data[node][LID]
    print 'Testing %s with %d LIDs' % (node, len(sample_lids))
    (rc, out0) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
    print 'Before LID test', out0
    for lid in sample_lids:
        print '%s -f l -d %s -s %s -c -v' % (ib_acme, lid, slid), node
        (rc, out0) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
        (rc, out) = ssa_tools_utils.execute_on_remote('%s -f l -d %s -s %s -c -v' % (ib_acme, lid, slid), node)
        print out
        if out.find('failed') >= 0 and out.find('success') < 0:
            print 'ERROR. ACM on %s failed' % node
            (_, o) = ssa_tools_utils.execute_on_remote('/usr/local/bin/ibv_devinfo', node)
            print o
            status = 1    
        (rc, out1) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
        try:
            if out1.split()[-4].split(',')[-1] == out0.split()[-4].split(',')[-1]:
                print 'ERROR. %s PR was not taken from cache' % node
                (_, o) = ssa_tools_utils.execute_on_remote('/usr/local/bin/ibv_devinfo', node)
                print o
                status = 2
        except:
            print 'ERROR. %s failed' % node
            (_, o) = ssa_tools_utils.execute_on_remote('/usr/local/bin/ibv_devinfo', node)
            print o
            status = 3
            break
    (rc, out0) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
    print 'After LID test\n', out0
print 'Run on %d nodes, each to %d lids' % ( len(acms), len(lids))

if status == 0:
    print 'PASSED %s' % __file__
else:
    print 'FAILED %s' % __file__
os.system('rm -f %s' % json_file)
sys.exit(status)
