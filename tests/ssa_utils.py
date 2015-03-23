#!/usr/bin/python

import os
import sys
import datetime
import random
import commands
import inspect
from pprint import pprint
import time
random.seed(os.environ.get('SEED',0))

TEST_NAME = ('%s' % os.path.basename(__file__)).rstrip('.py') 
sys.path.append("%s/../" % sys.path.append("%s/../" % os.path.dirname(os.path.abspath( __file__ ))))
import ssa_tools_utils


def test_report( test_header, phase, status):
    if status == 0:
        print '-I- Passed. %s %s . status = %d.' % ( test_header, phase, status)
    else:
        print '-I- Failed. %s %s . status = %d.' % ( test_header, phase, status)
    return None



def node_port_state_change(node, state):
    net = read_ibnetdiscover()
    pprint(net)        
    (rc, out) = ssa_tools_utils.execute_on_remote('/usr/sbin/ibstat |grep Node |grep GUID', node)
    try:
        SW_GID = net[out.split()[-1]][0]
        SW_PORT = net[out.split()[-1]][1]
        o = commands.getoutput('ibportstate -G %s %s %s' % ( SW_GID, SW_PORT, state ))
        print '[%s] ibportstate -G %s %s %s\n%s' % ( time.strftime("%b %d %H:%M:%S"), SW_GID, SW_PORT, state, o )
        return "%s %s" % ( SW_GID, SW_PORT )
    except:
        return None


def get_distribution_tree(master_sm_node):
    t = {}
    timeout = 300
    start_time = time.time()
    while ( time.time() - start_time <= timeout):
        print "%s>#cat %s |grep -v %s" % (master_sm_node, ssa_tools_utils.CFG_FILES['plugin_logfile'], time.strftime("%b"))
        (rc, out) = ssa_tools_utils.execute_on_remote("cat %s |grep -v %s" % (ssa_tools_utils.CFG_FILES['plugin_logfile'], time.strftime("%b")), 
            master_sm_node)
        tree = out.encode('ascii','ignore').split('General SSA distribution tree info')[-1].split('\n')
        print '[%s] Unfiltered Distribution tree looks like\n%s' % (master_sm_node, tree)
        if len(tree) > 1:
            return tree
    return tree
         
    

def read_ibnetdiscover():
    print 'Please wait, reading network'
    ibnetdiscover_log  = '/tmp/ibnetdiscover_%s.log' % time.strftime("%Y%m%d%H%M%S")
    cmd = '/usr/sbin/ibnetdiscover > %s' % ibnetdiscover_log
    o = commands.getoutput(cmd)
    print "%s\n%s" % (cmd, o)
    sysimgguid = None
    net = {}
    for line in open(ibnetdiscover_log).readlines():
        l = line.rstrip()
        if l.startswith('switchguid'):
            sysimgguid = l.split('=')[1].split('(')[0]
            continue

        if l.startswith('['):
            host = '0x' + l.split()[1].split('"')[1].split('-')[1]
            port = l.split()[0].rstrip(']').lstrip('[')
            if not net.has_key(host):
                net[host] = [sysimgguid, port]
    return net
    

def node_port_bounce(node, delay = 0):
        if node == commands.getoutput('hostname'):
            print 'Unable to execute port bounce on local node %s' % node
            return 1
        
        net = read_ibnetdiscover()
        (rc, out) = ssa_tools_utils.execute_on_remote('/usr/sbin/ibstat |grep Node |grep GUID', node)        
        
        SW_GID = net[out.split()[-1]][0]
        SW_PORT = net[out.split()[-1]][1]
        
        o = commands.getoutput('ibportstate -G %s %s disable' % ( SW_GID, SW_PORT ))
        print '[%s] ibportstate -G %s %s disable\n%s' % ( time.strftime("%b %d %H:%M:%S"), SW_GID, SW_PORT, o )        
        time.sleep(delay)
        o = commands.getoutput('ibportstate -G %s %s enable' % ( SW_GID, SW_PORT ))
        print '[%s] ibportstate -G %s %s enable\n%s'  % ( time.strftime("%b %d %H:%M:%S"), SW_GID, SW_PORT, o )
        return 0
            

def check_errors(rch_dict):
    status = 0
    for cmd in ['%s/maintain.py -t %s --setup status > %s/ssa_status.log' % (ssa_tools_utils.SSA_HOME, rch_dict['topology'], rch_dict['log_dir']) ,
                '%s/maintain.py -t %s -e > %s/ssa_errors.log' % (ssa_tools_utils.SSA_HOME, rch_dict['topology'], rch_dict['log_dir']),
                '%s/logcollector.py -t %s  -o %s' % (ssa_tools_utils.SSA_HOME, rch_dict['topology'], rch_dict['log_dir']) ]:
        print cmd
        o = commands.getoutput(cmd)
        
    o = commands.getoutput("cat  %s/ssa_errors.log" %  rch_dict['log_dir'])
    if o.find('Found errors found on') > 0:
        print 'There are errors in  %s/ssa_errors.log' %  rch_dict['log_dir']
        status = 1
    
    print 'See logs in %s' % rch_dict['log_dir']
    return status
