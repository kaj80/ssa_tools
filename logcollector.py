#!/usr/bin/python

import ssa_tools_utils
from optparse import OptionParser
import time
import os
import sys
import threading
import commands

ssa_global_dict = {}
timestamp = time.strftime("%Y%m%d_%H%M%S")
def_log_dest = '/mswg/projects/osm/kodiak/mlnx/logs'
ssa_global_dict['logcollector_output_folder_archive'] = True

logs = ssa_tools_utils.CFG_FILES
file_list = {'core':    [logs['plugin_logfile'], logs['osm_logfile'], logs['opensm_cfg'],logs['plugin_config'], '/usr/local/sbin/opensm'],
             'acm':     [logs['acm_logfile'], logs['acm_opts'],logs['acm_addr'], '/usr/local/sbin/ibacm', '/usr/local/bin/ib_acme'],
             'access':  [logs['access_logfile'], logs['access_opts'], '/usr/local/sbin/ibssa'],
             'distrib': [logs['distrib_logfile'], logs['distrib_opts'], '/usr/local/sbin/ibssa'],
             'other_files': ['/tmp/node*ssa.kodiak.nx.log', '/tmp/core.*', '/var/log/*.valgrind',
                            '/tmp/*.cov', '/tmp/*_counters', '/var/log/messages', '/var/log/syslog']
              }

ssa_global_dict['topology'] = None


def get_system(node, dest_folder):

    commands = ['date', 'ibssa -v', 'ibacm -v','opensm --version|grep OpenSM',
                'cat /etc/sysctl.conf |grep core_pattern', "df -lh",
                '/usr/sbin/ibstat', 'uname -a', 'cat /etc/issue' ]
    server_info_file = '%s/%s.info' % ( dest_folder, node)
    f = open(server_info_file, 'w')
    for cmd in commands:
        (_, o) = ssa_tools_utils.execute_on_remote(cmd, node)
        f.write("#%s\n%s\n\n" % ( cmd, o ))
    f.close()
    return 0




def get_logs_from_node(node, dest_folder, node_type):    
    node_dest = '%s/%s' % (dest_folder, node)
    not os.path.exists(node_dest) and os.mkdir(node_dest)
    os.system('chmod 777 -R %s' % node_dest)
    get_system(node, dest_folder)
    for filename in file_list[node_type]:
        (_, o) = ssa_tools_utils.execute_on_remote('cp -r %s %s' % ( filename, node_dest), node) 
        f = '%s/%s' % (node_dest, os.path.basename(filename))
        if os.path.exists(f) and f.endswith('cfg'):
            for line in open(f, 'r'):
                if not line.startswith('#') and line.find('_dir') >= 0:
                    local_dirs = '%s*' % line.split()[1]
                    (_, o) = ssa_tools_utils.execute_on_remote('cp -r %s %s' % ( local_dirs, node_dest), node) 
    (_, o) = ssa_tools_utils.execute_on_remote('cp -r /etc/rdma %s' %  node_dest, node)
    (_, o) = ssa_tools_utils.execute_on_remote('/bin/dmesg -T > %s/%s_dmesg.log ' %  (node_dest, node), node)
    (_, o) = ssa_tools_utils.execute_on_remote('cp -r %s %s' % (' '.join(file_list['other_files']), node_dest), node)
    (_, libs) = ssa_tools_utils.execute_on_remote("ldd `which ibssa ibacm opensm`|awk '{print $3}'| grep '/'|sort|uniq", node)
    libs = ' '.join(libs.split())
    (_, o) = ssa_tools_utils.execute_on_remote('cp -rL %s %s ' % (libs, node_dest), node) 
    print o
    print '%s finished log collection %s' % (node, dest_folder)
    return 0


def collect_logs(ssa_global_dict):    
    dest = ssa_global_dict['logcollector_output_folder']
    if not os.path.exists(dest):       
        os.mkdir(dest)
        os.system('chmod 777 -R %s' % dest)
    for k, v in ssa_global_dict.iteritems():
        if not k.startswith('#') and k.endswith('_nodes'):
            node_type = k.split('_')[0]
            dest_folder = '%s/%s' % (dest, node_type) 
            not os.path.exists(dest_folder) and os.mkdir(dest_folder)
            for nodes in ssa_tools_utils.devide_list_chunks(v, ssa_tools_utils.MAX_THREAD):
                thread_list = []
                for node in nodes:
                    t = threading.Thread(target=get_logs_from_node, args=(node,dest_folder, node_type,))
                    thread_list.append(t)
            
                for thread in thread_list:
                    thread.start()
    
                for thread in thread_list:
                    thread.join()
    
    dmsgfiles = [os.path.join(root, name) for root, dirs, files in os.walk(dest) for name in files if name.endswith(("_dmesg.log"))]
    for dmsgfile in dmsgfiles:
        if os.path.getsize(dmsgfile) == 0:
            os.remove(dmsgfile)
    
    if ssa_global_dict['logcollector_output_folder_archive']:
        archive = '/%s/%s_SSA_logs.zip' % (def_log_dest, timestamp)
        cwd=os.getcwd()
        os.chdir(dest)
        print '-I- %s# zip -r %s *' % (dest ,archive)
        time.sleep(10)
        o = commands.getoutput('zip -r %s * >/dev/null' % archive)
        print o
        time.sleep(10)
        commands.getoutput('rm -rf %s' % dest)
        print 'Archived logs %s' % archive
    else:
        print 'All logs saved under %s' % dest 
    return 0


def main(argv):
    print '%s %s' % ( __file__, ' '.join(argv))
    parser = OptionParser()
    parser.add_option('-t', '--topology_file',
        dest = 'topology', help = 'Provide file with SSA setup topology', metavar = 'topofile.ini')
    
    parser.add_option('-o', '--output_folder', dest = 'output_folder', help = 'Output folder')
    (options, _) = parser.parse_args(argv)
    
    if not options.topology: 
        parser.print_help()
        return 1

    ssa_global_dict['topology'] = options.topology 
    ssa_global_dict.update(ssa_tools_utils.read_config(options.topology)) 

    ssa_global_dict['logcollector_output_folder'] = '%s/%s' % (def_log_dest, timestamp)
    if options.output_folder:
        ssa_global_dict['logcollector_output_folder_archive'] = False
    

    collect_logs(ssa_global_dict)
    if options.output_folder:
        os.system('chmod 777 -R %s' % (ssa_global_dict['logcollector_output_folder']))
        os.system('mv %s %s' % (ssa_global_dict['logcollector_output_folder'], options.output_folder))
    
    return 0


if __name__ == "__main__":    
    main(sys.argv[1:])
    
