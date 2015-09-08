#!/usr/bin/python

import ssa_tools_utils

import os
import sys
import time
import commands
import threading

from optparse import OptionParser


timestamp = time.strftime("%Y%m%d_%H%M%S")
shared_dir = '/mswg/projects/osm/kodiak/mlnx/logs'

dict_global = {}
dict_global['topology'] = None
dict_global['dest_dir'] = '%s/%s' % (shared_dir, timestamp)
dict_global['dest_dir_archive'] = True

logs = ssa_tools_utils.CFG_FILES
file_list = {
              'core' :        [ logs['plugin_logfile'],  logs['osm_logfile'],  logs['opensm_cfg'], logs['plugin_config'],   '/usr/local/sbin/opensm'],
              'acm' :         [ logs['acm_logfile'],     logs['acm_opts'],     logs['acm_addr'],   '/usr/local/sbin/ibacm', '/usr/local/bin/ib_acme'],
              'access' :      [ logs['access_logfile'],  logs['access_opts'],  '/usr/local/sbin/ibssa'],
              'distrib' :     [ logs['distrib_logfile'], logs['distrib_opts'], '/usr/local/sbin/ibssa'],
              'other_files' : [ '/tmp/node*ssa.kodiak.nx.log',
                                '/tmp/core.*',
                                '/var/log/*.valgrind',
                                '/tmp/*.cov',
                                '/tmp/*_counters',
                                '/var/log/messages',
                                '/var/log/syslog' ]
              }

def get_system_info(node, dest_dir):

    commands = [ 'date',
                 'df -lh',
                 'ibssa -v',
                 'ibacm -v',
                 'uname -a',
                 'cat /etc/issue',
                 '/usr/sbin/ibstat',
                 'opensm --version | grep OpenSM',
                 'cat /etc/sysctl.conf | grep core_pattern' ]

    node_info_file = '%s/%s.info' % ( dest_dir, node)
    f = open(node_info_file, 'w')

    for cmd in commands:
        (_, out) = ssa_tools_utils.execute_on_remote(cmd, node)
        f.write("#%s\n%s\n\n" % ( cmd, out ))

    f.close()

    return 0


def get_logs_from_node(node, dest_dir, node_type):
    node_dest = '%s/%s' % (dest_dir, node)

    if not os.path.exists(node_dest):
        os.mkdir(node_dest)

    os.system('chmod 777 -R %s' % node_dest)

    get_system_info(node, dest_dir)

    for file in file_list[node_type]:
        (_, _) = ssa_tools_utils.execute_on_remote('cp -r %s %s > /dev/null' % (file, node_dest), node)

        f = '%s/%s' % (node_dest, os.path.basename(file))
        if os.path.exists(f) and f.endswith('cfg'):
            for line in open(f, 'r'):
                if not line.startswith('#') and line.find('_dir') >= 0:
                    local_dirs = '%s*' % line.split()[1]
                    (_, _) = ssa_tools_utils.execute_on_remote('cp -r %s %s > /dev/null' % (local_dirs, node_dest), node)

    cmds = { 'rdma'       : 'cp -r /etc/rdma %s > /dev/null' %  node_dest,
             'dmesg'      :'/bin/dmesg -T > %s/%s_dmesg.log' % (node_dest, node),
             'misc_files' : 'cp -r %s %s > /dev/null' % (' '.join(file_list['other_files']), node_dest),
             'libs'       : "ldd `which ibssa ibacm opensm` | awk '{print $3}' | grep '/' | sort | uniq" }
    for cmd_type in cmds.keys():
        (_, out) = ssa_tools_utils.execute_on_remote(cmds[cmd_type], node)

        if cmd_type == 'libs':
            libs = ' '.join(out.split())
            (_, _) = ssa_tools_utils.execute_on_remote('cp -rL %s %s > /dev/null' % (libs, node_dest), node)

    print '%s finished log collection %s' % (node, dest_dir)

    return 0


def collect_logs(dict_global):

    dest = dict_global['dest_dir']
    if not os.path.exists(dest):
        os.mkdir(dest)

    os.system('chmod 777 -R %s' % dest)

    for k, v in dict_global.iteritems():
        if not k.startswith('#') and k.endswith('_nodes'):
            node_type = k.split('_')[0]

            dest_dir = '%s/%s' % (dest, node_type)
            if not os.path.exists(dest_dir):
                os.mkdir(dest_dir)

            for nodes in ssa_tools_utils.devide_list_chunks(v, ssa_tools_utils.MAX_THREAD):
                thread_list = []
                for node in nodes:
                    t = threading.Thread(target=get_logs_from_node, args=(node, dest_dir, node_type,))
                    thread_list.append(t)

                for thread in thread_list:
                    thread.start()

                for thread in thread_list:
                    thread.join()

    dmsgfiles = [os.path.join(root, name) for root, dirs, files in os.walk(dest) for name in files if name.endswith(("_dmesg.log"))]
    for dmsgfile in dmsgfiles:
        if os.path.getsize(dmsgfile) == 0:
            os.remove(dmsgfile)

    if dict_global['dest_dir_archive']:
        archive = '/%s_SSA_logs.zip' % (dict_global['dest_dir'])
        print '-I- %s# zip -r %s *' % (dest, archive)

        os.chdir(dest)

        out = commands.getoutput('zip -r %s * >/dev/null' % archive)
        print out
        time.sleep(10)

        commands.getoutput('rm -rf %s' % dest)
        print 'Archived logs %s' % archive

    return 0


def main(argv):

    print '%s %s' % ( __file__, ' '.join(argv))

    parser = OptionParser()
    parser.add_option('-t', '--topology_file', dest = 'topology',
                      help = 'Provide file with SSA setup topology',
                      metavar = 'topofile.ini')
    parser.add_option('-o', '--output_folder', dest = 'output_folder', help = 'Output folder')
    (options, _) = parser.parse_args(argv)

    if not options.topology:
        parser.print_help()
        return 1

    dict_global['topology'] = options.topology
    dict_global.update(ssa_tools_utils.read_config(options.topology))

    if options.output_folder:
        dict_global['dest_dir_archive'] = False

    collect_logs(dict_global)

    if options.output_folder:
        os.system('chmod 777 -R %s' % (dict_global['dest_dir']))
        os.system('mv %s %s' % (dict_global['dest_dir'], options.output_folder))
        print 'All logs saved under %s' % (options.output_folder)

    return 0


if __name__ == "__main__":
    main(sys.argv[1:])
