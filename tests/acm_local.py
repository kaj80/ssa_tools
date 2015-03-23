#!/usr/bin/python
import random
import commands
import json
from  pprint import pprint
import sys
import time 
import os
########################### CONSTANTS ###################################
sys.path.append("/proj/SSA/Mellanox/ssa_tools")
ib_acme = '/usr/local/bin/ib_acme'
retries = 30
delay = 0
(TYPE, STATUS, LID, GID, VERSION) = (0,1,2,3,4)
##############################################################

try:
    status_file = sys.argv[1]
except:
    print 'Please provide json status output file'
    print 'ex: /tmp/ssa_universal_2Al_big.ini_status.json'
    sys.exit(1)


#random.seed(os.environ.get('SEED',0))

json_data=open(status_file).read()
data = json.loads(json_data)
pprint(data)

status = 0
sys.exit(status)
lids = []
gids = []
for node in data.keys():
    if data[node][STATUS] != 'RUNNING':
        continue
    #try:
    else:
        print '%s: %s' % (node, data[node])
        pprint(data[node])
        lids.append(int(data[node][LID]))
        gids.append(data[node][GID].encode('ascii','ignore'))
    #except:
    #    pass

hostname = commands.getoutput('hostname')
'''
print 'First SM query to triger cache pull'
smlid = commands.getoutput("ibstat |grep SM|awk '{print $3}'")
o2 = commands.getoutput('%s -f l -d %s ' % (ib_acme, smlid))
while ( o2.find('success') <= 0):
    o2 = commands.getoutput('%s -f l -d %s ' % (ib_acme, smlid))
    print o2
    time.sleep(delay)
    retries = retries - 1
    if retries == 0:
        print 'ERROR first query'
        print '%s -f l -d %s ' % (ib_acme, smlid)
        sys.exit(1)
'''


osmlid = commands.getoutput("ibstat |grep -a5 Act|grep SM|awk '{print $NF}'")
slid =  commands.getoutput("ibstat |grep -a5 Act|grep Base|awk '{print $NF}'") 
sgid = commands.getoutput("ibaddr |awk '{print $2}'")
osmgid = commands.getoutput("saquery --src-to-dst %s:%s|grep dgid" % ( slid, osmlid)).split('.')[-1]

print slid, osmlid, osmgid

print 'Starting %s on %s' % ( __file__, hostname)
print 'Current  cache status is \n%s' % commands.getoutput('%s -P ' % ib_acme)
print '[%s] Starting first cache query' % time.strftime("%b %d %H:%M:%S")
cmd = '%s -f l -d %s ' % (ib_acme, osmlid)
print '%s\n%s' % (cmd, commands.getoutput(cmd))
cmd = '%s -f g -d %s ' % (ib_acme, osmgid)
print '%s\n%s' % (cmd, commands.getoutput(cmd))
time.sleep(10)
print 'Current  cache status is \n%s' % commands.getoutput('%s -P ' % ib_acme)
print '[%s] Starting test' % time.strftime("%b %d %H:%M:%S")
# SA has now 2 additional queries
o = commands.getoutput('%s -P ' % ib_acme).split()[-4].split(',')[-2:]
try:
    offset = int(o[0]) - int(o[1]) 
except:
    print 'Failed to run ib_acme -P\n%s' % commands.getoutput('%s -P ' % ib_acme)
    sys.exit(1)

print '*****************************'
print gids
print '***********************************'
print lids

for gid in gids:
    o1 = commands.getoutput('%s -P ' % ib_acme)
    date = time.strftime("%b %d %H:%M:%S")
    cmd = '%s -f g -d %s -v -s %s -c ' % (ib_acme, gid, sgid)
    o2 = commands.getoutput(cmd)
    o3 = commands.getoutput('%s -P ' % ib_acme)
    print '[%s] %s# %s' % (date, hostname, cmd)
    if o2.find('failed') >= 0 or o2.find('refused') >= 0:
        print 'Failed %s SA verification\n%s' % (hostname, o2)
        status = status + 1
    elif (o1.split()[-4].split(',')[-1] == o3.split()[-4].split(',')[-1]):
        print 'Failed %s cache change %s == %s ' % ( hostname, o1, o3)
        status = status + 1
    elif (int(o3.split()[-4].split(',')[-2]) != int(o3.split()[-4].split(',')[-1]) + offset):
        print o3
        print 'Warning to query cache only\n%s != %s + %d' % (o3.split()[-4].split(',')[-2], o3.split()[-4].split(',')[-1], offset)
    else:
        print "Passed %s acm cache query to %s\n%s" % ( hostname, gid, o2)
    time.sleep(delay)

for lid in lids:
    o1 = commands.getoutput('%s -P ' % ib_acme)
    date = time.strftime("%b %d %H:%M:%S")
    cmd = '%s -f l -d %s -v -s %s -c ' % (ib_acme, lid, slid)
    o2 = commands.getoutput(cmd)
    o3 = commands.getoutput('%s -P ' % ib_acme)
    print '[%s] %s# %s' % (date, hostname, cmd)
    if o2.find('failed') >= 0 or o2.find('refused') >= 0:
        print 'Failed %s SA verification\n%s' % (hostname, o2)
        status = status + 1
    elif (o1.split()[-4].split(',')[-1] == o3.split()[-4].split(',')[-1]):
        print 'Failed %s cache change %s == %s ' % ( hostname, o1, o3)
        status = status + 1
    else:
        print "Passed %s acm cache query to %s\n%s" % ( hostname, lid, o2)
    time.sleep(delay)

if status == 0:
    print "%s PASSED" % __file__
else:
    print "%s FAILED" % __file__
sys.exit(status)






