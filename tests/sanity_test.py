#!/usr/bin/python

#
# This test should be run when the following SSA fabric is configured:
#
# CORES     : 2
# DISTRIB   : >= 1
# ACCESS    : 2
# ACM       : >= 2
#

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

################ CONSTANTS ###################################
(TYPE, STATUS, LID, GID, VERSION) = (0, 1, 2, 3, 4)

ib_acme         = '/usr/local/bin/ib_acme'
sample_size     = 5
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


def get_ip_data ():
    #takes ip data from the file used for data preloading
    file_location = '/etc/rdma'
    file_name = 'ibssa_hosts.data'
    ip_data_str = commands.getoutput("cat %s/%s | awk '{print $1}'" % (file_location,file_name))
    return ip_data_str.split()


def compare_outs (out0, out1, index):

	try:
		if out1.split()[-4].split(',')[index] == out0.split()[-4].split(',')[index]:
			return "Equal"
	except:
		return "Exception"

	return "Unequal"


def find_active_ib_port(node):

    #assumes onlu 2 ports, called ib0 and ib1
    (rc, out) = ssa_tools_utils.execute_on_remote('ibportstate -D 0 1 | grep LinkUp', node)
    if len(out) > 0:
        return 'ib0'
    return 'ib1'


def test_acm_by_lid_query (node, slid, dlid, initial_query = 0, print_err = 1):

    status = 0

    if initial_query == 1:
        print 'Executing initial ib_acme query on %s (lid %s) node' % (node, slid)
        (rc, out) = ssa_tools_utils.execute_on_remote('%s -f l -d %s -s %s -c' % (ib_acme, dlid, slid), node)
        time.sleep(10)

    print '%s -f l -d %s -s %s -c -v' % (ib_acme, dlid, slid), node
    (rc, out0) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
    (rc, out) = ssa_tools_utils.execute_on_remote('%s -f l -d %s -s %s -c -v' % (ib_acme, dlid, slid), node)
    #print out

    if out.find('failed') >= 0 and out.find('success') < 0:
        if print_err == 1:
            print 'ERROR. ACM on %s failed' % node
            (_, o) = ssa_tools_utils.execute_on_remote('/usr/local/bin/ibv_devinfo', node)
            print o
        status = 1

    (rc, out1) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)

    ret = compare_outs(out0, out1, -1)
    if ret == "Equal":
        if print_err == 1:
            print 'ERROR. %s PR was not taken from cache' % node
            (_, o) = ssa_tools_utils.execute_on_remote('/usr/local/bin/ibv_devinfo', node)
            print o
        status = 2
    elif ret == "Exception":
        print 'ERROR. %s failed' % node
        (_, o) = ssa_tools_utils.execute_on_remote('/usr/local/bin/ibv_devinfo', node)
        print o
        status = 3

    return status

def test_acm_by_lid (acms, sample_lids, data):

    status = 0

    print '==================================================================='
    print '======================= TEST ACM BY LID ==========================='
    print '==================================================================='

    for node in acms:

        if node == '':
            continue

        slid = data[node][LID]

        print 'Testing %s with %d LIDs' % (node, len(sample_lids))
        (rc, out0) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
        print 'Before LID test', out0

        for lid in sample_lids:
            status = test_acm_by_lid_query(node, slid, lid)
            if status != 0:
                break

        (rc, out0) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
        print 'After LID test\n', out0

    print 'Run on %d nodes, each to %d lids' % (len(acms), len(sample_lids))

    print '==================================================================='
    print '========= TEST ACM BY LID COMPLETE (status: %d) ====================' % (status)
    print '==================================================================='

    return status

def test_acm_by_gid_query (node, sgid, dgid, initial_query = 0, print_err = 1):

    status = 0

    if initial_query == 1:
        print 'Executing initial ib_acme query on %s (gid %s) node' % (node, sgid)
        (rc, out) = ssa_tools_utils.execute_on_remote('%s -f g -d %s -s %s -c' % (ib_acme, dgid, sgid), node)
        time.sleep(10)

    print '%s#  %s -f g -d %s -s %s -c -v' % (node, ib_acme, dgid, sgid)
    (rc, out0) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
    (rc, out) = ssa_tools_utils.execute_on_remote('%s -f g -d %s -s %s -c -v' % (ib_acme, dgid, sgid), node)
    #print out

    if out.find('failed') >= 0 and out.find('success') < 0:
        if print_err == 1:
            print 'error. acm on %s failed' % node
        status = 1

    (rc, out1) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
    ret = compare_outs(out0, out1, -1)
    if ret == "Equal":
        if print_err == 1:
            print 'error. %s pr was not taken from cache' % node
        status = 2

    return status


def test_acm_by_gid (acms, sample_gids, data):

    status = 0

    print '==================================================================='
    print '======================= TEST ACM BY GID ==========================='
    print '==================================================================='

    for node in acms:

        if node == '':
            continue

        (_, sgid)   = ssa_tools_utils.execute_on_remote("/usr/sbin/ibaddr |awk '{print $2}'", node)

        print 'Testing %s with %d GIDs' % (node, len(sample_gids))
        (rc, out0) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
        print 'Before GID test\n', out0

        for gid in sample_gids:

            status = test_acm_by_gid_query(node, sgid, gid)
            if status != 0:
                break

        (rc, out0) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
        print 'After GID test\n', out0

    print 'Run on %d nodes, each to %d gids' % (len(acms), len(sample_gids))

    print '==================================================================='
    print '========== TEST ACM BY GID COMPLETE (status: %d) ===================' % (status)
    print '==================================================================='

    return status


def test_acm_by_ip_query (node, sip, dip, initial_query = 0, print_err = 1):

    status = 0

    if initial_query == 1:
        print 'Executing initial ib_acme query on %s (ip %s) node' % (node, sip)
        (rc, out) = ssa_tools_utils.execute_on_remote('%s -f i -d %s -s %s -c' % (ib_acme, dip, sip), node)
        time.sleep(10)

    print '%s -f i -d %s -s %s -c -v' % (ib_acme, dip, sip), node
    (rc, out0) = ssa_tools_utils.execute_on_remote('%s -P ' %ib_acme, node)
    (rc, out) = ssa_tools_utils.execute_on_remote('%s -f i -d %s -s %s -c -v' % (ib_acme, dip, sip), node)
    #print_out

    if out.find('failed') >= 0 and out.find('success') < 0:
        if print_err == 1:
            print 'ERROR. ACM on %s failed' % node
        status = 1

    (rc, out1) = ssa_tools_utils.execute_on_remote('%s -P' % ib_acme, node)

    ret = compare_outs(out0, out1, -3)
    if ret == "Equal":
        if print_err == 1:
             print 'error. %s pr was not taken from cache' % node
        status = 2

    return status


def test_acm_by_ip (acms, sample_ips, data):

    status = 0

    print '==================================================================='
    print '======================= TEST ACM BY IP ==========================='
    print '==================================================================='

    for node in acms:

        if node == '':
            continue

        (_, sip)   = ssa_tools_utils.execute_on_remote("cat /tmp/ip", node)
        #the /tmp/ip file is created by the gen_host_data.sh script

        print 'Testing %s with %d IPs' % (node, len(sample_ips))
        (rc, out0) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
        print 'Before IP test\n', out0

        for ip in sample_ips:

            status = test_acm_by_ip_query(node, sip, ip)
            if status != 0:
                break
    

        (rc, out0) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
        print 'After IP test\n', out0

    print 'Run on %d nodes, each to %d ips' % (len(acms), len(sample_ips))

    print '==================================================================='
    print '========== TEST ACM BY IP COMPLETE (status: %d) ===================' % (status)
    print '==================================================================='

    return status

def test_acm_ip_kernel_cache (acms, sample_ips):

    status = 0

    print '==================================================================='
    print '================== TEST ACM IP KERNEL CACHE ======================='
    print '==================================================================='

    for node in acms:

        if node == '':
            continue

        print 'Executing kernel cache test on node %s' % (node)

        active_port = find_active_ib_port(node)

        (_, ip_line) = ssa_tools_utils.execute_on_remote("ip address show dev %s | grep inet" % active_port, node)

        for ip in sample_ips:

            if ip_line.find(ip) > 0:
                print "no need to look for node %s ip in its own cache:" % (node)
                print "therefore the serach for ip %s is skipped" % (ip)
                print ''
                continue
            (rc, out) = ssa_tools_utils.execute_on_remote('ip neigh show dev %s %s' % (active_port, ip), node)
            if len(out) == 0:
                print 'ERROR: ip %s not found in node %s cache' % (ip, node)
                status = 2
                break
            if out.split()[-1] != 'PERMANENT':
                print 'ERROR: ip %s node %s cache is not PERMANENT' % (ip, node)
                status = 2
                break

    print 'Run on %d nodes, eact to %d ips' % (len(acms), len(sample_ips))

    print '==================================================================='
    print '========== TEST ACM IP KERNEL CACHE COMPLETE (status: %d) =========' % (status)
    print '==================================================================='

    return status


def sanity_test_0 (cores, als, acms, lids, gids, ips, data):

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

    print '==================================================================='
    print '========================= SANITY TEST 0 ==========================='
    print '==================================================================='

    # Initial ib_acme query in order to make sure there was PRDB update
    for node in acms:
        if node == '':
            continue

        (_, sgid)   = ssa_tools_utils.execute_on_remote("/usr/sbin/ibaddr |awk '{print $2}'", node)
        slid        = data[node][LID]

        (_, _)      = ssa_tools_utils.execute_on_remote('%s -f g -d %s -s %s -c -v' % (ib_acme, osmgid, sgid), node)
        (_, _)      = ssa_tools_utils.execute_on_remote('%s -f l -d %s -s %s -c -v' % (ib_acme, osmlid, slid), node)
        time.sleep(10)


    sample_gids = random.sample(gids, min(len(gids), sample_size))
    sample_lids = random.sample(lids, min(len(lids), sample_size))
    sample_ips = random.sample(ips, min(len(ips), sample_size))

    status = test_acm_by_gid(acms, sample_gids, data)
    if status != 0:
        return status

    status = test_acm_by_lid(acms, sample_lids, data)
    if status != 0:
        return status

    status = test_acm_by_ip(acms, sample_ips, data)
    if status != 0:
        return status

    status = test_acm_ip_kernel_cache(acms, sample_ips)
    if status != 0:
        return status

    print '==================================================================='
    print '==================== SANITY TEST 0 COMPLETE ======================='
    print '==================================================================='

    return status


def get_node_remote (node):
    #
    # HACK: it is assumed that node machine is connected to a remote node with port 1
    #
    (rc, out) = ssa_tools_utils.execute_on_remote('smpquery PI -D 0,1 | grep ^Lid', node)
    remote_lid = out.split('.')[-1].rsplit('\n')[0]

    (rc, out) = ssa_tools_utils.execute_on_remote('smpquery NI -D 0,1 | grep LocalPort', node)
    remote_port = out.split('.')[-1].rsplit('\n')[0]

    return (remote_lid, remote_port)


def start_services (core, access, acm):
    status = 0

    sm_master   = ssa_tools_utils.core(core)
    access_svc  = ssa_tools_utils.access(access)
    acm_svc     = ssa_tools_utils.acm(acm)

    print '[%s] Start MASTER SM' % time.strftime("%b %d %H:%M:%S")
    sm_master.start()
    print '[%s] Start ACCESS layer' % time.strftime("%b %d %H:%M:%S")
    access_svc.start()
    print '[%s] Start ACM layer' % time.strftime("%b %d %H:%M:%S")
    acm_svc.start()

    print 'Wait'
    time.sleep(60)

    return status


def stop_services (core, access, acm):
    status = 0

    sm_master   = ssa_tools_utils.core(core)
    access_svc  = ssa_tools_utils.access(access)
    acm_svc     = ssa_tools_utils.acm(acm)

    print '[%s] Stop MASTER SM' % time.strftime("%b %d %H:%M:%S")
    sm_master.stop()
    print '[%s] Stop ACCESS layer' % time.strftime("%b %d %H:%M:%S")
    access_svc.stop()
    print '[%s] Stop ACM layer' % time.strftime("%b %d %H:%M:%S")
    acm_svc.stop()

    return status


def sanity_test_1 (cores, als, acms, data):

    status = 0

    osmlid      = commands.getoutput("/usr/sbin/ibstat |grep -a5 Act|grep SM|awk '{print $NF}'").rstrip('\n')

    for core in cores:
        if data[core][LID] == osmlid:
            core_master = core
            break

    access_svc  = als[0]
    acm_svc     = acms[0]

    print '==================================================================='
    print '========================= SANITY TEST 1 ==========================='
    print '==================================================================='

    for acm in acms:
        if acm == acm_svc:
            continue

        status = test_acm_by_lid_query(acm, data[acm][LID], data[acm_svc][LID])
        if status != 0:
            return status

        status = test_acm_by_gid_query(acm, data[acm][GID], data[acm_svc][GID])
        if status != 0:
            return status

    stop_services(core_master, access_svc, acm_svc)

    # Disconect ACM from fabric
    (remote_lid, remote_port) = get_node_remote(acm_svc)
    cmd = 'ibportstate %s %s disable' % (remote_lid, remote_port)
    print cmd
    ssa_tools_utils.pdsh_run(core_master, cmd)
    print 'Wait'
    time.sleep(120)

    for acm in acms:
        if acm == acm_svc:
            continue

        status = test_acm_by_lid_query(acm, data[acm][LID], data[acm_svc][LID], initial_query = 1, print_err = 0)
        if status == 0:
            print 'ERROR. ACM %s LID %s still exists in %s LID %s cache' % \
                    (acm_svc, str(data[acm_svc][LID]), acm, str(data[acm][LID]))
            cmd = 'ibportstate %s %s enable' % (remote_lid, remote_port)
            print cmd
            ssa_tools_utils.pdsh_run(core_master, cmd)
            return 1

        status = test_acm_by_gid_query(acm, data[acm][GID], data[acm_svc][GID], print_err = 0)
        if status == 0:
            print 'ERROR. ACM %s GID %s still exists in %s GID %s cache' % \
                    (acm_svc, str(data[acm_svc][GID]), acm, str(data[acm][GID]))
            cmd = 'ibportstate %s %s enable' % (remote_lid, remote_port)
            print cmd
            ssa_tools_utils.pdsh_run(core_master, cmd)
            return 1

    # Reconnect ACM back to fabric
    cmd = 'ibportstate %s %s enable' % (remote_lid, remote_port)
    print cmd
    # command can be run on any node except for the disconected ACM
    ssa_tools_utils.pdsh_run(core_master, cmd)
    time.sleep(60)

    start_services(core_master, access_svc, acm_svc)
    status = not status

    print '==================================================================='
    print '==================== SANITY TEST 1 COMPLETE ======================='
    print '==================================================================='

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

    ip_data = get_ip_data()

    cores   = []
    als     = []
    acms    = []

    lids    = []
    gids    = []
    ips     = []

    status  = 0

    for node in fabric_data.keys():
        if fabric_data[node][STATUS] != 'RUNNING':
            print 'FAILED one of SSA fabric nodes (%s) is not RUNNING' % node
            sys.exit(1)

        elif fabric_data[node][TYPE] == 'core':
            cores.append(node)
        elif fabric_data[node][TYPE] == 'access':
            als.append(node)
        elif fabric_data[node][TYPE] == 'acm':
            acms.append(node)

        try:
            lids.append(int(fabric_data[node][LID]))
            gids.append(fabric_data[node][GID].encode('ascii','ignore'))
        except:
            pass

    for ip in ip_data:
            ips.append(ip)

    if len(cores) != 2 or len(als) != 2 or len(acms) < 2:
        status = 1
    else:
        status = sanity_test_0(cores, als, acms, lids, gids, ips, fabric_data)
        if status == 0:
            status = sanity_test_1(cores, als, acms, fabric_data)

    # close all cached connections
    ssa_tools_utils.execute_on_remote_cleanup()

    if status == 0:
        print 'PASSED %s' % __file__
    else:
        print 'FAILED %s' % __file__

    sys.exit(status)

if __name__ == "__main__":
        main(sys.argv[1:])
