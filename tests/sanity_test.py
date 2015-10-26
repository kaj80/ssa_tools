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
import socket

from  pprint   import pprint
from  optparse import OptionParser

sys.path.append("%s/../" % os.path.dirname(os.path.abspath( __file__ )))
import ssa_tools_utils

################ CONSTANTS ###################################
(TYPE, STATUS, LID, GID, VERSION) = (0, 1, 2, 3, 4)

ib_acme         = '/usr/local/bin/ib_acme'
route_cache_count_index = -1
addr_cache_count_index = -3
sample_size     = 5
# assumes default file location and name:
CORE_PRELOAD_FILE_PATH = '/usr/local/etc/rdma/ibssa_hosts.data'
ALT_NODE_IP = '113.0.0.113'
ALT_NODE_NETMASK = '255.255.0.0' # currently - no change
##############################################################

def get_opts ():
    parser = OptionParser()
    parser.add_option('-t', \
                      dest = 'topology', \
                      help = 'Provide file with SSA setup topology', \
                      metavar = 'setup_example.ini')

    parser.add_option('-s', \
                      dest = 'sample_size', \
                      help = 'Provide number of ACM clients to be tested', \
                      metavar = '<sample size>')

    (options, _) = parser.parse_args()
    if not options.topology:
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(options.topology):
        print '%s not found' % options.topology
        sys.exit(1)

    if options.sample_size and int(options.sample_size) < 0:
        print 'Invalid sample size specified (%s)' % options.sample_size
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
    # takes ip data from the file used for data preloading
    file_location = '/etc/rdma'
    file_name = 'ibssa_hosts.data'
    ip_data_str = commands.getoutput("cat %s/%s | awk '{print $1}'" % (file_location,file_name))
    return ip_data_str.split()

def compare_outs (out0, out1, index_to_compare):

    try:
        if out1.split()[-4].split(',')[index_to_compare] == out0.split()[-4].split(',')[index_to_compare]:
            return 0
            # values are equal
    except:
        return -1

    return 1
    # values are not equal

def get_active_ib_interface(node):

    # assumes only 2 ports, called ib0 and ib1
    (rc, out) = ssa_tools_utils.execute_on_remote('ibportstate -D 0 1 | grep LinkUp', node)
    if len(out) > 0:
        return 'ib0'
    return 'ib1'

def get_node_ip(node,node_active_interface):

    (_, ip)   = ssa_tools_utils.execute_on_remote("ip address show dev %s | grep 'inet ' \
                                        | awk '{print $2}'  | cut -f1 -d'/' \
                                        | tr -d '\n'" \
                                        % (node_active_interface), node)
    return ip

def get_IPv6_addr(node, node_active_interface):

    (_, IPv6_lines) = ssa_tools_utils.execute_on_remote("ip address show dev %s | grep 'inet6'" % (node_active_interface), node)
    num_lines = IPv6_lines.count('\n')
    if num_lines > 1: # FIXME: necessary?
        print 'ERROR: node %s interface %s has more than 1 IPv6 address' % (node, node_active_interface)
        return -1
    if num_lines < 1: #FIXME: same
        print 'ERROR: node %s interface %s has no IPv6 address' % (node, node_active_interface)
        return "-1"

    (_, IPv6)   = ssa_tools_utils.execute_on_remote("ip address show dev %s | grep 'inet6' \
                                        | awk '{print $2}'  | cut -f1 -d'/' \
                                        | tr -d '\n'" \
                                        % (node_active_interface), node)
    return IPv6

def get_node_ip_mask(node,node_active_interface):

    (_, mask) = ssa_tools_utils.execute_on_remote("ifconfig %s | grep Mask \
                                        | awk '{print $4}' | tr -d '\n'" \
                                        % (node_active_interface), node)

    return mask


def ib_acme_query(addr_format, dest, src, additional_flags, node):

    str_to_exec = ib_acme + ' -f ' + addr_format + ' -d ' + str(dest) + \
                  ' -s ' + str(src) + ' ' + additional_flags

    return ssa_tools_utils.execute_on_remote(str_to_exec, node)

def ib_acme_get_counters(node):

    str_to_exec = ib_acme + ' -P '
    return ssa_tools_utils.execute_on_remote(str_to_exec, node)

def test_acm_by_lid_query (node, slid, dlid, initial_query = 0, print_err = 1):

    status = 0

    if initial_query == 1:
        print 'Executing initial ib_acme query on %s (lid %s) node' % (node, slid)
        (rc, out) = ib_acme_query('l', dlid, slid, '-c', node)
        time.sleep(10)

    print '%s -f l -d %s -s %s -c -v' % (ib_acme, dlid, slid), node
    (rc, out0) = ib_acme_get_counters(node)
    (rc, out) = ib_acme_query('l', dlid, slid, '-c -v', node)
    # print out

    if out.find('failed') >= 0 and out.find('success') < 0:
        if print_err == 1:
            print 'ERROR. ACM on %s failed (lid test)' % node
            (_, o) = ssa_tools_utils.execute_on_remote('/usr/local/bin/ibv_devinfo', node)
            print o
        status = 1

    (rc, out1) = ib_acme_get_counters(node)

    ret = compare_outs(out0, out1, route_cache_count_index)
    if ret == 0:
        if print_err == 1:
            print 'ERROR. %s PR was not taken from cache (lid test)' % node
            (_, o) = ssa_tools_utils.execute_on_remote('/usr/local/bin/ibv_devinfo', node)
            print o
        status = 2
    elif ret == "-1":
        print 'ERROR. %s failed' % node
        (_, o) = ssa_tools_utils.execute_on_remote('/usr/local/bin/ibv_devinfo', node)
        print o
        status = 3

    return status

def test_acm_by_gid_query (node, sgid, dgid, initial_query = 0, print_err = 1):

    status = 0

    if initial_query == 1:
        print 'Executing initial ib_acme query on %s (gid %s) node' % (node, sgid)
        (rc, out) = ib_acme_query('g', dgid, sgid, '-c', node)
        time.sleep(10)

    print '%s#  %s -f g -d %s -s %s -c -v' % (node, ib_acme, dgid, sgid)
    (rc, out0) = ib_acme_get_counters(node)
    (rc, out) = ib_acme_query('g', dgid, sgid, '-c -v', node)
    # print out

    if out.find('failed') >= 0 and out.find('success') < 0:
        if print_err == 1:
            print 'error. acm on %s failed (gid test)' % node
        status = 1

    (rc, out1) = ib_acme_get_counters(node)
    ret = compare_outs(out0, out1, route_cache_count_index)
    if ret == 0:
        if print_err == 1:
            print 'error. %s pr was not taken from cache (gid test)' % node
        status = 2

    return status

def test_acm_by_lid_gid (acms, sample_lids, sample_gids, data):

    status = 0

    print '==================================================================='
    print '=================== TEST ACM BY LID AND GID ======================='
    print '==================================================================='

    for node in acms:

        if node == '':
            continue

        slid = data[node][LID]

        print 'Testing %s with %d LIDs' % (node, len(sample_lids))
        (rc, out0) = ib_acme_get_counters(node)
        print 'Before LID test', out0

        for lid in sample_lids:
            status = test_acm_by_lid_query(node, slid, lid)
            if status != 0:
                break

        (rc, out0) = ib_acme_get_counters(node)
        print 'After LID test\n', out0


        (_, sgid)   = ssa_tools_utils.execute_on_remote("/usr/sbin/ibaddr |awk '{print $2}'", node)

        print 'Testing %s with %d GIDs' % (node, len(sample_gids))
        (rc, out0) = ssa_tools_utils.execute_on_remote('%s -P ' % ib_acme, node)
        print 'Before GID test\n', out0

        for gid in sample_gids:

            status = test_acm_by_gid_query(node, sgid, gid)
            if status != 0:
                break

        if status != 0:
            break

        (rc, out0) = ib_acme_get_counters(node)
        print 'After GID test\n', out0

    print 'Run on %d nodes, each to %d lids and %d gids' % (len(acms), len(sample_lids), len(sample_gids))

    print '==================================================================='
    print '========= TEST ACM BY LID AND GID COMPLETE (status: %d) ===========' % (status)
    print '==================================================================='

    return status

def test_acm_by_ip_query (node, sip, dip, initial_query = 0, print_err = 1):

    status = 0

    if initial_query == 1:
        print 'Executing initial ib_acme query on %s (ip %s) node' % (node, sip)
        (rc, out) = ib_acme_query('i', dip, sip, '-c', node)
        time.sleep(10)

    print '%s -f i -d %s -s %s -c -v' % (ib_acme, dip, sip), node
    (rc, out0) = ib_acme_get_counters(node)
    (rc, out) = ib_acme_query('i', dip, sip, '-c -v', node)
    # print_out

    if out.find('failed') >= 0 and out.find('success') < 0:
        if print_err == 1:
            print 'ERROR. ACM on %s failed' % node
        status = 1

    (rc, out1) = ib_acme_get_counters(node)

    ret = compare_outs(out0, out1, addr_cache_count_index)
    if ret == 0:
        if print_err == 1:
             print 'error. %s pr was not taken from cache' % node
        status = 2

    return status

def kcache_ip_lookup(node, active_interface, addr_to_search, entry_type):

    status = 0
    (rc, out) = ssa_tools_utils.execute_on_remote('ip neigh show dev %s %s' % (active_interface, addr_to_search), node)
    if len(out) == 0:
        print 'ERROR: ip %s not found in node %s cache' % (addr_to_search, node)
        status = 2
        return status
    if out.split()[-1] != entry_type:
        print 'ERROR: ip %s node %s cache is not %s' % (addr_to_search, node, entry_type)
        status = 2
    return status

def test_ip (acms, sample_ipv4s, sample_ipv6s):

    status = 0

    print '==================================================================='
    print '======================= TEST ACM BY IP ============================'
    print '=======            (kernel and user caches)                ========'
    print '==================================================================='

    for node in acms:

        if node == '':
            continue

        active_interface = get_active_ib_interface(node)

        print 'Testing %s with %d IPv4s, %d IPv6s' % (node, len(sample_ipv4s), len(sample_ipv6s))
        (rc, out0) = ib_acme_get_counters(node)
        print 'Before IP test\n', out0
        node_ip = get_node_ip(node, active_interface)
        node_ipv6 = get_IPv6_addr(node, active_interface)

        if node_ipv6 == "-1":
            status = 2
            break

        print 'Executing IPv4 kernel and user cache tests on node %s' % (node)
        for ip in sample_ipv4s:

            status = test_acm_by_ip_query(node, node_ip, ip)
            if status != 0:
                break

            if ip == node_ip:
                print "no need to look for node %s ip in its own cache:" % (node)
                print "therefore the serach for ip %s is skipped" % (ip)
                print ''
                continue
            status = kcache_ip_lookup(node, active_interface, ip, 'PERMANENT')
            if status != 0:
                break

        if status != 0:
            break

        (rc, out0) = ib_acme_get_counters(node)
        print 'After IPv4 test\n', out0
        print ''
        print 'Executing IPv6 kernel and user cache tests on node %s' % (node)

        for ipv6 in sample_ipv6s:

            status = test_acm_by_ip_query(node, node_ipv6, ipv6)
            if status != 0:
                break

            if ipv6 == node_ipv6:
                print "no need to look for node %s ip in its own cache:" % (node)
                print "therefore the serach for ip %s is skipped" % (ipv6)
                print ''
                continue
            status = kcache_ip_lookup(node, active_interface, ipv6, 'PERMANENT')
            if status != 0:
                break

        if status != 0:
            break
        (rc, out0) = ib_acme_get_counters(node)
        print 'After IPv6 test\n', out0
        print ''

    print 'Run on %d nodes, each to %d IPv4s, %d IPv6s' % (len(acms), len(sample_ipv4s), len(sample_ipv6s))
    print '==================================================================='
    print '========== TEST ACM BY IP COMPLETE (status: %d) ===================' % (status)
    print '==================================================================='

    return status


def sanity_test_0 (cores, als, acms, lids, gids, ipv4s, ipv6s, data):

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

        (_, _)      = ib_acme_query('g', osmgid, sgid, '-c -v', node)
        (_, _)      = ib_acme_query('l', osmlid, slid, '-c -v', node)
        time.sleep(10)


    sample_gids = random.sample(gids, min(len(gids), sample_size))
    sample_lids = random.sample(lids, min(len(lids), sample_size))
    sample_ipv4s = random.sample(ipv4s, min(len(ipv4s), sample_size))
    sample_ipv6s = random.sample(ipv6s, min(len(ipv6s), sample_size))

    status = test_acm_by_lid_gid(acms, sample_lids, sample_gids, data)
    if status != 0:
        return status

    status = test_ip(acms, sample_ipv4s, sample_ipv6s)
    if status != 0:
        return status

    print '==================================================================='
    print '==================== SANITY TEST 0 COMPLETE ======================='
    print '==================================================================='

    return status

def change_node_ip(node, new_ip, new_netmask):

    active_interface = get_active_ib_interface(node)
    (rc, ret) = ssa_tools_utils.execute_on_remote('ifconfig %s %s netmask %s' % (active_interface, new_ip, new_netmask), node)
    # assumes reconfiguring doesn't fail  FIXME
    return 0

def change_and_load_ip(cores, old_ip, new_ip):

    for core in cores:
        (_, out) = ssa_tools_utils.execute_on_remote("sed -i 's/^%s/%s/g' %s" % (old_ip, new_ip, CORE_PRELOAD_FILE_PATH), core)
        (_, out) = ssa_tools_utils.execute_on_remote("kill -s HUP `pidof opensm`", core)

    return 0

def test_mod_flow(acms, data, changed_node, old_ip, new_ip):

    status = 0
    for node in acms:
        node_lid = data[node][LID]
        node_active_interface = get_active_ib_interface(node)
        (_,_) = ib_acme_query('l', node_lid, node_lid, '-c -v', node)
        status = kcache_ip_lookup(node,node_active_interface,new_ip,'PERMANENT')
        if status != 0:
            break
        arr = [new_ip]
        sip = get_node_ip(node, node_active_interface)
        status = test_acm_by_ip_query(node, sip, new_ip)
        if status != 0:
            break

    return status

def ip_mod_flow_test(cores, als, acms, data):

    print '==================================================================='
    print '================== TEST IP MODIFICATION FLOW  ====================='
    print '==================================================================='

    status = 0
    if len(als) == 0:
        print 'no access node found, CHANGING CORE INSTEAD'
        changed_node = cores[0]
    else:
        changed_node = als[0]
    active_interface = get_active_ib_interface(changed_node)
    old_ip = get_node_ip(changed_node, active_interface)
    old_mask = get_node_ip_mask(changed_node,active_interface)
    status = change_node_ip(changed_node, ALT_NODE_IP, ALT_NODE_NETMASK)
    if status != 0: #FIXME: if no error check added on change_node_ip - remove these lines 
        status = 3
    else:
        change_and_load_ip(cores, old_ip, ALT_NODE_IP)
        sample_acms = random.sample(acms, min(len(acms), sample_size))
        status = test_mod_flow(sample_acms, data, changed_node, old_ip, ALT_NODE_IP)

    undo_status = -1
    if status != 3:
        undo_status = 0
        undo_status = change_node_ip(changed_node, old_ip, old_mask)
    if undo_status > 0: #FIXME: if no error check added on change_node_ip - remove these lines 
        print 'ERROR: FAILED TO UNDO CHANGES TO NODE IP IN MODIFICATION FLOW TEST'
    if undo_status == 0:
        undo_status = change_and_load_ip(cores, ALT_NODE_IP, old_ip)
        if undo_status > 0: #FIXME: if no error check added on change_and_load - remove these lines
            print 'ERROR: FAILED TO UNDO CHANGES TO PRELOADED FILES IN MODIFICATION FLOW TEST'

    print '==================================================================='
    print '========= TEST IP MODIFICATION FLOW COMPLETE (status: %d) =========' % (status)
    print '=========       (modification-undo status: %d)            =========' % (undo_status)
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

def run_tests(cores, als, acms, lids, gids, ipv4s, ipv6s, fabric_data):

    status = 0
    status = sanity_test_0(cores, als, acms, lids, gids, ipv4s, ipv6s, fabric_data)
    if status != 0:
        return status

    status = ip_mod_flow_test(cores, als, acms, fabric_data)
    if status != 0:
         return status
    status = sanity_test_1(cores, als, acms, fabric_data)
    return status


def main (argv):

    global sample_size

    opts = get_opts()

    if opts.sample_size:
        sample_size = int(opts.sample_size)

    #
    # Fabric data dictionary format:
    # { "dev-r-vrt-045" : ["acm", "STOPPED", "4", "fe80::2:c903:21:fa01", "1.0.8.1_62e2157"], ... }
    #
    # Dictionary fields for each key:
    # (TYPE, STATUS, LID, GID, VERSION) = (0, 1, 2, 3, 4)
    #
    fabric_data = get_data(opts.topology)

    cores   = []
    als     = []
    acms    = []

    lids    = []
    gids    = []

    ipv4s   = []
    ipv6s   = []

    ips = get_ip_data()
    for ip in ips:
        type = 4
        try:
            ret = socket.inet_pton(socket.AF_INET, ip)
        except:
            type = 6
            try:
                ret = socket.inet_pton(socket.AF_INET6, ip)
            except:
                type = 0
        if type == 4:
            ipv4s.append(ip)
        elif type == 6:
           ipv6s.append(ip)
        else:
           print 'ERROR: get_ip_data retrieved %s - which is not an ip' % ip
           return 1

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

    if len(cores) != 2 or len(als) != 2 or len(acms) < 2:
        status = 1
    else:
         status = run_tests(cores, als, acms, lids, gids, ipv4s, ipv6s, fabric_data)

    # close all cached connections
    ssa_tools_utils.execute_on_remote_cleanup()

    if status == 0:
        print 'PASSED %s' % __file__
    else:
        print 'FAILED %s' % __file__

    sys.exit(status)

if __name__ == "__main__":
        main(sys.argv[1:])
