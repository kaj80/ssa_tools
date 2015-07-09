#!/usr/bin/python

import ssa_tools_utils
from optparse import OptionParser
import threading
import time
from pprint import pprint
import sys
import os
import json
import time
import random

ssa_global_dict = {}
ssa_global_dict['no_random'] = False

if ssa_tools_utils.MEMCHECK:
    delay = 60
else:
    delay = 0


def _ssa_action(host, action, typ):
        if host == '':
            return 0
        c = eval('ssa_tools_utils.%s' % typ)(host)
        if action == 'start':
            c.start()
        elif action == 'stop':
            c.stop()
        elif action == 'status':
            pass
        elif action == 'restart':
            c.stop()
            c.start()
        return c.get_status()



def check_setup(global_dict):
    report = {}
    status = 0

    for typ in ['core', 'acm', 'distrib', 'access']:
        for nodes in ssa_tools_utils.devide_list_chunks(global_dict['%s_nodes' % typ], ssa_tools_utils.MAX_THREAD):
            for node in nodes:
                if node == '':
                    continue
                c = eval('ssa_tools_utils.%s' % typ)(node)
                try:
                    rc = c.get_status()
                except:
                    rc = 1
                report[node] = [typ]
                if int(rc) == 0:
                    report[node].append('RUNNING')
                else:
                    report[node].append('STOPPED')
                    status = 1

                try:
                    if typ == 'acm':
                        (_, version) = ssa_tools_utils.execute_on_remote('ibacm -v', node)
                    else:
                        (_, version) = ssa_tools_utils.execute_on_remote('ibssa -v', node)
                    version = version.split()[-1]
                except:
                    version = 'unknown'
                try:
                    (rc, lid) = ssa_tools_utils.execute_on_remote("/usr/sbin/ibstat|egrep -a5 \"Act|Initializing\"|grep Base| awk '{print $NF}'", node)
                except:
                    lid = 'None'
                report[node].append(lid.rstrip('\n').encode('ascii','ignore'))
                (rc, gid) = ssa_tools_utils.execute_on_remote("/usr/sbin/ibaddr|awk '{print $2}'", node)
                report[node].append(gid.rstrip('\n').encode('ascii','ignore'))
                report[node].append(version)

                (a,b) = ssa_tools_utils.execute_on_remote("/usr/sbin/ibstat|egrep -a5 \"Act|Initializing\"|grep Base| awk '{print $NF}';/usr/sbin/ibaddr|awk '{print $2}';ibssa -v;ibacm -v", node)

    print "*************  check_setup ********************"
    print "node: [ssa_type, status, lid, gid, version]"
    sum = {}
    for n in sorted(report.keys()):
        print '%s: %s' % (n, str(report[n]))
        if not sum.has_key(report[n][0]):
            sum[report[n][0]] = 1
        else:
            sum[report[n][0]] += 1
    print 'Running %s summary' % global_dict['topology']
    pprint (sum)

    status_file = '/tmp/%s_%s_status.json' % (time.strftime("%Y%M%d_%H%M%S"), global_dict['topology'])
    f = open(status_file, 'w')
    json.dump(report, f)
    print "Saved under %s \n***********************************************" % status_file

    return status


def action_setup(global_dict, action):
    pprint(global_dict)
    if action == 'status':
        return check_setup(global_dict)
    elif action == 'clean':
        return ssa_tools_utils.ssa_clean_setup(global_dict)

    if not global_dict['no_random']:
        nodes = []
        for typ in [ 'core', 'distrib', 'access', 'acm' ]:
            for node in global_dict['%s_nodes' % typ]:
                nodes.append({node:typ})
        random.shuffle(nodes)
        for n in nodes:
            node = n.keys()[0]
            s = _ssa_action(node, action, n[node])
    else:
        for typ in [ 'core', 'distrib', 'access', 'acm' ]:
            print global_dict['%s_nodes' % typ]
            for node in global_dict['%s_nodes' % typ]:
                 if node == '':
                     continue
                 s = _ssa_action(node, action, typ)
        print 'Wait %s before %sing %s' % (delay, action, typ)
        time.sleep(delay)
    return 0

def check_error(global_dict):
    status = 0
    for osm_node in global_dict.get('core_nodes', 'osm'):
        ssa_tools_utils.execute_on_remote('cat %s | egrep "ERROR|ERR:"' % (ssa_tools_utils.CFG_FILES['osm_logfile']), osm_node)

    errors = {}
    for typ in [ 'distrib', 'access', 'acm' ]:
        for nodes in ssa_tools_utils.devide_list_chunks(global_dict['%s_nodes' % typ], ssa_tools_utils.MAX_THREAD):
            for node in nodes:
                if node == '':
                    continue

                (rc, out) = ssa_tools_utils.execute_on_remote('cat %s | egrep "ERROR|ERR:|BACKTRACE" | grep -v "ERROR 111"' % (ssa_tools_utils.CFG_FILES['%s_logfile' % typ]), node)
                if out != "":
                    print '%s %s \n%s' % ( typ, node, out)
                    errors[node] = out
                    status = 1
                (rc, out) =  ssa_tools_utils.execute_on_remote('/usr/sbin/ibstat | grep -i active', node)
                out = out.rstrip('\n')
                if int(rc) != 0 or out == '':
                    print 'ERROR. Check ib modules on %s:%s' % (node, out)
                    #status = 2
                    #errors[node] = out
    if status == 0:
        print 'Report: No errors found in logs'
    else:
        print 'Report: Found errors found on'
        for h,e in errors.iteritems():
            if len(e) == 0:
                continue
            print '*************** %s ***********************' % h
            print e
    return status

def run_cmd(global_dict, cmd):
    status = 0
    for typ in [ 'distrib', 'access', 'acm', 'core']:
        for nodes in ssa_tools_utils.devide_list_chunks(global_dict['%s_nodes' % typ], ssa_tools_utils.MAX_THREAD):
            for node in nodes:
                (rc, out) = ssa_tools_utils.execute_on_remote(cmd, node)
                if int(rc) != 0:
                    status = 1

    return status


def main(argv):

    print '%s %s' % ( __file__, ' '.join(argv))

    status = 0

    actions = [ 'stop', 'start', 'status', 'clean', 'restart' ]

    parser = OptionParser()
    parser.add_option('-t', dest = 'topology', help = 'Provide file with SSA setup topology', metavar = 'setup_example.ini')
    parser.add_option('--setup', dest = 'setup', help = 'Start/Stop SSA daemons or clean all logs and procs', metavar = '<%s>' % '|'.join(actions))
    parser.add_option('-e', '--err_check', dest = 'check_error', help = 'Check SSA logs for errors', action = 'store_true')
    parser.add_option('-c', '--command', dest = 'cmd', help = 'Run cmd on all nodes')
    parser.add_option('--ignore_nodes', dest = 'ignore_nodes', help = 'cs list of nodes to be ignored')
    parser.add_option('-n', dest = 'no_random', help = 'no random stop|start', action = 'store_true')

    (options, _) = parser.parse_args()
    if options.setup and options.setup not in actions:
        options.setup = 'status'

    if not options.topology:
        parser.print_help()
        return 1

    if not os.path.exists(options.topology):
        print 'Error: %s is missing' % options.topology
        return 1

    ssa_global_dict.update(ssa_tools_utils.read_config(options.topology))
    ssa_global_dict['topology'] = os.path.basename(options.topology)

    if options.ignore_nodes:
        for typ in [ 'distrib', 'access', 'acm', 'core' ]:
            for n in options.ignore_nodes.split(','):
                if n in ssa_global_dict['%s_nodes' % typ ]:
                    ssa_global_dict['%s_nodes' % typ ].remove(n)

    if options.no_random:
        ssa_global_dict['no_random'] = True

    if options.setup:
        status = status + action_setup(ssa_global_dict, options.setup)

    if options.check_error:
        status = status + check_error(ssa_global_dict)

    if options.cmd:
        status = status + run_cmd(ssa_global_dict, options.cmd)

    ssa_tools_utils.execute_on_remote_cleanup()

    return status


if __name__ == "__main__":
    main(sys.argv[1:])
