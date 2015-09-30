

"""
@copyright:
    Copyright (C) Mellanox Technologies Ltd. 2001-2014.  ALL RIGHTS RESERVED.
    This software product is a proprietary product of Mellanox Technologies Ltd.
    (the "Company") and all right, title, and interest in and to the software product,
    including all associated intellectual property rights, are and shall
    remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

Created on 26-Jan-2014

@author: Lenny Verkhovsky lennyb@mellanox.com
"""



import sys
import commands
import os
import threading
try:
    import paramiko
except:
    commands.getoutput('yum install python-paramiko.noarch -y')

from pprint import pprint
import time

SSA_HOME = os.path.dirname(os.path.abspath( __file__ ))
NFS_LOGS_DIR = "/mswg/projects/osm/kodiak/mlnx/logs"
SSA_SCRIPTS = "%s/scripts" % SSA_HOME



MAX_THREAD = 20
#PATH = os.environ.get('SSA_DEST', '%s/..' % os.path.dirname(os.path.abspath( __file__ )))
#PATH = '/proj/SSA/Mellanox/'
IPERF = 'perf'

# Valgrind run.
# 0 - dont run
# 1 - run default
# 10 - --show-reachable=yes --undef-value-errors=no
# 11 - --leak-check=full

# 20 - run helgrind default
# 21 - run helgrind with --leak-check=full

# VALGRIND_OPTs = additional options to be passed to valgrind

#this is changed from runner.py
MEMCHECK = None

VALGRIND_OPTS = '--xml=yes  --trace-children=yes '

if MEMCHECK == 'LEAKCHECK':
    VALGRIND_OPTS += '--leak-check=full '
elif MEMCHECK == 'VALGRIND':
    VALGRIND_OPTS += '--show-reachable=yes --undef-value-errors=no '
elif MEMCHECK == 'HELGRIND':
    VALGRIND_OPTS += '--tool=helgrind'

#--sim-hints=deactivate-pthread-stack-cache-via-hack
#-free-is-write=yes   // experimental, default no
#--history-level=none  // uses less memory



CFG_FILES = {'opensm_cfg': '/usr/local/etc/rdma/opensm.conf',
             'osm_logfile':'/var/log/opensm.log',
             'opensm' : '/usr/local/sbin/opensm' ,

             'plugin_logfile': '/var/log/ibssa.log',
             'core_logfile': '/var/log/ibssa.log',
             'plugin_config': '/usr/local/etc/rdma/ibssa_core_opts.cfg',
             'plugin_valgrind_logfile': '/var/log/ibssa_core.log.valgrind.xml',


             'smdb_dump' : 3,   # 0 - no dump, 1 - Binary, 2 - Debug, 3-human readble

             'acm_opts':'/usr/local/etc/rdma/ibacm_opts.cfg',
             'acm_addr':'/usr/local/etc/rdma/ibacm_addr.cfg',
             'acm_logfile' : '/var/log/ibacm.log',
             'acm_valgrind_logfile': '/var/log/ibacm.log.valgrind.xml',

             'distrib_logfile': '/var/log/ibssa.log',
             'distrib_opts': '/usr/local/etc/rdma/DL_ibssa_opts.cfg',
             'distrib_valgrind_logfile': '/var/log/ibssa.distrib.log.valgrind.xml',

             'access_opts':'/usr/local/etc/rdma/AL_ibssa_opts.cfg',
             'access_logfile': '/var/log/ibssa.log',
             'access_valgrind_logfile': '/var/log/ibssa.access.log.valgrind.xml',

             'core_lockfile': '/var/run/ibssa.pid',
             'acm_lockfile': '/var/run/ibssa.pid',
             'distrib_lockfile': '/var/run/ibacm.pid'
             }


devide_list_chunks = lambda x, n, acc=[]: devide_list_chunks(x[n:], n, acc+[(x[:n])]) if x else acc
conn_dict = {}

def _ssa_action(host, action, typ):
    if host == '':
        return 0
    c = eval(typ)(host)
    if action == 'start':
        c.start()
    elif action == 'stop':
        c.stop()
    elif action == 'restart':
        ssa_clean_setup(ssa_global_dict)
        print 'Please wait before start'
        time.sleep(180)
        c.start()
    return c.get_status()

def read_config(config_file):

    int_dict = {}
    if not os.path.exists(config_file):
        print '-E- %s Does not exist' % config_file
        return int_dict

    with open(config_file, 'r') as f:
        for line in f:
            if line.startswith('#') or len(line) < 3:
                continue
            l = line.split()
            int_dict[l[0]] = ''.join(l[1:]).replace(' ','').split(',')

    print 'Loaded from %s' % config_file
    f.close()
    return int_dict


def get_file(host, filename, destination):
    if filename == '':
        return ''
    if type(filename) != list:
        for f in filename:
            commands.getoutput('scp -r lennyb@%s:/%s %s' % ( host, f, destination))
    else:
        return commands.getoutput('scp -r lennyb@%s:/%s %s' % ( host, filename, destination))


def pdsh_run(hosts, cmd):
    #sudo -u lennyb -E
    if type(hosts) == list:
        cmd = 'pdsh -w %s \'%s\'' % ( ','.join(hosts), cmd)
    else:
        cmd = 'pdsh -w %s \'%s\'' % (hosts, cmd)
    o = commands.getoutput(cmd)
    print o
    return o


def run_iperf(hosts):

    if len(hosts) != 2:
        print '-E- please provide a list of 2 hosts'
        return 1

    client_ip = hosts[0]
    server_ip = hosts[1]
    #Start Server
    server = run_on_remote(server_ip)
    s_cmd = '%s -s' % (IPERF)
    server_pid = server.run_in_background(s_cmd)

    #Start client
    client = run_on_remote(client_ip)
    cmd = '%s -c %s' % (IPERF, server_ip)
    client.run(cmd)
    status = client.get_status()
    output = client.get_output()
    #print '%s returned %s\n%s' % (cmd, status, output )
    server.kill_pid(server_pid)
    return status



def execute_on_remote(cmds, host):
    global conn_dict

    if host == commands.getoutput('hostname'):
        if type(cmds) == list:
            o =  commands.getoutput(';'.join(cmds))
            return (0, commands.getoutput(';'.join(cmds)))
        else:
            return(0, commands.getoutput(cmds))

    #print 'Executing on %s' % host

    status	= 0
    output	= ''

    if conn_dict.has_key(host):
        c = conn_dict[host]
    else:
	c = run_on_remote(host)
        conn_dict[host] = c

    if type(cmds) == list:
        for cmd in cmds:
            c.run(cmd)
            status = status + c.status
            output = output + c.output
    else:
        c.run(cmds)
        status = c.status
        output = c.output

    #c.close()
    return (status, output)

def execute_on_remote_cleanup():
    global conn_dict

    for c in conn_dict.values():
        c.close()

def rm_exec(cmd, hosts):
    if type(hosts) != list:
        (s, _) = execute_on_remote(cmd, hosts)
        return s

    for nodes in devide_list_chunks(hosts, MAX_THREAD):
        thread_list = []
        for node in nodes:
            #print 'Executing execute_on_remote(%s,%s)' % ( cmd, node)
            t = threading.Thread(target=execute_on_remote, args=(cmd, node,))
            thread_list.append(t)

        for thread in thread_list:
            thread.start()

        for thread in thread_list:
            thread.join()

    return 0

def ssa_clean_setup(ssa_global_dict):
    node_list = []
    for k, v in ssa_global_dict.iteritems():
        if not k.startswith('#') and k.endswith('_nodes'):
            node_list = node_list + v
    node_list = list(set(node_list))

    print 'Trying to stop SSA first', node_list
    cmds = []
    for i in ['opensm', 'ibacm', 'ibssa']:
        cmds.append('/usr/local/etc/init.d/%s stop' % i)
    for i in ['opensm', 'ibacm', 'ibssa']:
        cmds.append('pkill -9 -f %s' % i)
    rm_exec(cmds, node_list)
    time.sleep(10)


    cmds = []
    for k in CFG_FILES.keys():
        if k.endswith('_logfile') or k.endswith('_lockfile'):
            cmds.append('rm -f %s*' % CFG_FILES[k])

    for i in ['opensm', 'ibacm', 'ibssa']:
        cmds.append('/usr/local/etc/init.d/%s stop' % i)
        cmds.append('pkill -9 -f  %s`' % i)
        cmds.append('rm -rf /var/lock/subsys/%s /var/run/%s.pid /var/log/ibssa.log /var/log/ibacm.log' % (i, i) )
    cmds.append('rm -rf /etc/rdma/*db_dump.*')
    cmds.append('/bin/dmesg -c >/dev/null' )
#    cmds.append('/sbin/ifconfig ib0 down' )

    return rm_exec(cmds, node_list)


class prdb():
        def __init__(self, ssa_global_dict, access_node):
            self.db = {}
            self.dict = ssa_global_dict
            self.ac_node = access_node

        def load(self):
            self.db[self.ac_node] = {'prdb':{}, 'ib_acme' : {}}
            c = run_on_remote( self.ac_node)
            cmd = 'ls %s/|grep prdb_dump' % (self.dict['prdb_dump_dir'])
            c.run(cmd)
            print c.output
            prdb = {}
            for folder in c.output.split():
                guid = folder.split('.')[1]
                prdb[guid] = {}
                for l in open('%s/%s/PR/data' % (self.dict['prdb_dump_dir'], folder), 'r'):
                    line=l.split()
                    prdb[guid] = {}
                    for i in range(0, len(line), 2):
                        prdb[guid][line[i]] = line[i+1]
            c.close()
            pprint(prdb)
            return prdb





class run_on_remote():

    def __init__(self, host = 'localhost', root = True):

        print 'Connecting to %s' % (host)

        self.client	= paramiko.SSHClient()
        self.output	= ""
        self.host	= host
        self.pid	= None
        self.root	= root

        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self.client.connect(host, timeout = 9999)
            #please set user/password.
            #self.client.connect(host, username = 'lennyb', password = '******', timeout = 9999)
            print 'Established remote connection with %s ' % (host)

        except:
            print 'Failed to established remote connection with %s' % host
            return None


    def run(self, cmd):
        ex_time = time.strftime("%b %d %H:%M:%S")

        if self.root:
            cmd = cmd
            #cmd = 'sudo -E %s' % cmd
        try:
            _, stdout, _	= self.client.exec_command(cmd)
            self.status		= stdout.channel.recv_exit_status()
            self.output		= stdout.channel.recv(4096).decode('ascii')

            print '%s [%s]# %s\n%s' % (ex_time, self.host, cmd, self.output)
            return self.status

        except:
            self.status = 1
            self.output = ''

            print 'failed to execute %s [%s]# %s' % (ex_time, self.host, cmd)
            return self.status


    def run_in_background(self, cmd):
        channel	= self.client.get_transport().open_session()
        pty	= channel.get_pty()
        shell	= self.client.invoke_shell()
        print " ****************nohup %s 2>&1 &\n" % cmd
        shell.send("nohup %s 2>&1 &\n" % cmd)
        print ' ********************************'
        return 0
        _, _, _ = self.client.exec_command("nohup %s &" % cmd)
        print ' *************///////////////////////**************'
        print ("nohup %s &" % cmd)
        _, pid, _ = self.client.exec_command('pgrep %s ' % os.path.basename(cmd.split()[0]))
        return pid.channel.recv(4096).decode('ascii')

    def close(self):
        return self.client.close()

    def get_output(self):
        return self.output.rstrip()

    def kill_pid(self, pid):
        self.client.exec_command("kill -9 %s " % pid)
        return self.stdout.channel.recv_exit_status()


class ssa(object):
    def __init__(self, host = 'localhost'):
        self.host = host
        self.connection = run_on_remote(self.host)
        self.output = None
        self.opts_file = None
        self.make_default_config()
        self.bin = None
        self.basenem = None
        self.daemon = None
        self.cfg_opt = '-O'
        if MEMCHECK:
            self.valgrind_log = None

    def make_default_config(self):
        pass

    def start(self):
         s = self.connection.run('COVFILE=/tmp/%s.cov LD_LIBRARY_PATH=/usr/local/lib %s %s %s' % (self.host, self.bin, self.cfg_opt, self.opts_file))
         return s

    def restart(self):
        self.stop()
        self.start()
        return self.get_status()

    def stop(self):
        self.connection.run('/usr/local/etc/init.d/%s stop' % os.path.basename(self.daemon))
        self.connection.run('pgrep %s' % os.path.basename(self.bin))
        if self.connection.output:
            print 'ERROR. %s was not stopped. Killing it' % os.path.basename(self.bin)
            self.connection.run('pkill -9 -f  %s' % self.basename)



    def kill(self):
        s = self.connection.run('pkill -9 -f %s` ' % self.basename)
        for k in CFG_FILES.keys():
            if k.endswith('_lockfile'):
                self.connection.run('rm -f %s*' % CFG_FILES[k])
        return s

    def get_status(self):
        if MEMCHECK:
            s = self.connection.run('pidof %s' % 'valgrind')
        else:
            s = self.connection.run('pidof %s' % os.path.basename(self.bin))
        return s

    def run(self, cmd):
        self.connection.run(cmd)
        self.output = self.connection.output
        return self.connection.status

    def clear_log(self):
        self.run('rm -f %s' % self.log)
        return self.connection.status

    def save_log(self, destination_folder):
        get_file(self.host, self.log, destination_folder)

    def check_log(self, pattern):
        self.connection.run('cat %s | grep %s' % (self.log, pattern))
        if self.output == '':
            return 0
        print self.output
        return 1

    def close(self):
        self.connection.close()

    def get_value(self, key):
        self.connection.run("cat %s|grep %s|egrep -v '#'" % (self.opts_file, key ))
        try:
            return self.connection.output.split()[1]
        except:
            return None

    def set_value(self, key, value):
        self.connection.run("cat %s|grep %s|egrep -v '#'" % (self.opts_file, key ))
        l = self.connection.output.rstrip('\n')
        self.connection.run("sed -i 's/%s/%s %s/g' %s" % (l, key, value, self.opts_file))
        if self.bin.find('opensm') >= 0:
            self.connection.run("kill -s HUP `pidof opensm valgrind`")
        return self.connection.status

class acm(ssa):
    def __init__(self, host = 'localhost'):
        super(acm, self).__init__(host)
        self.daemon  = '%s/etc/init.d/ibacm' % '/usr/local'
        self.log = CFG_FILES['acm_logfile']
        self.opts_file = CFG_FILES['acm_opts']
        self.bin = '/usr/local/sbin/ibacm'
        self.basename = 'ibacm'
        if MEMCHECK:
            self.valgrind_log = CFG_FILES['acm_valgrind_logfile']
            self.bin = 'valgrind %s --xml-file=%s %s' % (VALGRIND_OPTS, self.valgrind_log, self.bin)


class distrib(ssa):
    def __init__(self, host = 'localhost'):
        super(distrib, self).__init__(host)
        self.daemon = '%s/etc/init.d/ibssa' % '/usr/local'
        self.log = CFG_FILES['distrib_logfile']
        self.opts_file = CFG_FILES['distrib_opts']
        self.bin = '/usr/local/sbin/ibssa'
        self.basename = 'ibssa'
        if MEMCHECK:
            self.valgrind_log = CFG_FILES['distrib_valgrind_logfile']
            self.bin = 'valgrind %s --xml-file=%s %s' % (VALGRIND_OPTS, self.valgrind_log, self.bin)


class access(ssa):
    def __init__(self, host = 'localhost'):
        super(access, self).__init__(host)
        self.daemon = '%s/etc/init.d/ibssa' % '/usr/local'
        self.log = CFG_FILES['access_logfile']
        self.opts_file = CFG_FILES['access_opts']
        self.bin = '/usr/local/sbin/ibssa'
        self.basename = 'ibssa'
        if MEMCHECK:
            self.valgrind_log = CFG_FILES['access_valgrind_logfile']
            self.bin = 'valgrind %s --xml-file=%s %s' % (VALGRIND_OPTS, self.valgrind_log, self.bin)

class core(ssa):
    def __init__(self, host = 'localhost'):
        super(core, self).__init__(host)
        self.daemon = '%s/etc/init.d/opensmd' % '/usr/local'
        self.log = [CFG_FILES['plugin_logfile'], CFG_FILES['osm_logfile'] ]
        self.opts_file = CFG_FILES['opensm_cfg']
        self.bin = "%s -B " % CFG_FILES['opensm']
        self.basename = 'opensm'
        self.cfg_opt = '-F'
        if MEMCHECK:
            self.valgrind_log = CFG_FILES['plugin_valgrind_logfile']
            self.bin = 'valgrind %s --xml-file=%s %s' % (VALGRIND_OPTS, self.valgrind_log, self.bin)

    def get_status(self):
        if MEMCHECK:
            s = self.connection.run('pidof %s' % 'valgrind')
        else:
            s = self.connection.run('pidof %s' % os.path.basename(self.bin.split()[0]))
        return s

    def stop(self):
        if MEMCHECK:
            s = self.connection.run('pkill -TERM -f %s' % self.basename)
        else:
            self.connection.run('/usr/local/etc/init.d/%s stop' % os.path.basename(self.daemon))
            self.connection.run('pgrep opensm')
            if self.connection.output:
                print 'ERROR. OpenSM was not stopped. Killing it'
                self.connection.run('pkill -TERM -f %s' % 'opensm')
'''
./configure --enable-openib-rdmacm-ibaddr --prefix $PREFIX --enable-mpirun-prefix-by-default --with-verbs=/usr/local --enable-debug --disable-openib-connectx-xrc

    /.autodirect/mtrswgwork/lennyb/work/UFM/SSA/OMPI_INSTALL/length; /.autodirect/mtrswgwork/lennyb/work/UFM/SSA/OMPI_INSTALL/bin/mpirun -np $np --host dev-r-vrt-030,dev-r-vrt-034,dev-r-vrt-035 --display-map --report-bindings --bind-to core  --mca btl openib,self,sm --mca btl_openib_cpc_include rdmacm --mca pml ob1 --mca btl_openib_if_include mlx4_0:1 --mca btl_base_verbose 0 //.autodirect/mtrswgwork/lennyb/work/UFM/SSA/OMPI_SRC/imb/src/IMB-MPI1 alltoall -npmin $np  -msglen /.autodirect/mtrswgwork/lennyb/work/UFM/SSA/OMPI_INSTALL/length

'''




class ib_acme():
    def __init__(self, host):
        self.host = host
        self.cmd = 'ib_acme'
        self.connection = run_on_remote(self.host)
        self.output = None

    def run(self, options = ''):
        self.connection.run('COVFILE=/tmp/%s.cov LD_LIBRARY_PATH=/usr/local/lib %s %s' % (self.host, self.cmd, options))
        self.output = self.connection.output
        return self.connection.status

    def get_pr(self, dlid):
        IBACMEDB = {}
        if self.run('-f l -d %s' % dlid) != 0:
            return IBACMEDB
        lines = self.output.split('\n')
        for key in lines:

            s = key.split(': ')
            if s[0].startswith('  '):
                k = str(s[0].lstrip(' '))
                #dgid: fe80::f452:1403:17:2011 -> f452:1403:0017:2011 -> f452140300172011

                if k.endswith('gid'):
                    gid = []
                    for g in s[1].split('::')[1].split(':'):
                        gid.append(g.zfill(4))
                    s[1] = ''.join(gid)
                IBACMEDB[k] = str(s[1])

        return IBACMEDB

    def create_cfg(self, destination_folder = '/tmp'):
        return self.run('-A -O -D %s' % destination_folder)

    def close(self):
        self.connection.close()

    def show_cache(self):
        self.run('-P')
        o = self.output.rstrip('\n').replace('\n',',').split(',')
        if o[-1] == 'return status 0x0':
            print o[0:7]
            return map(int, o[8:15])
        else:
            print o[1:2]
            return []




def start_ib_acme(nodes, delay = 600, amount = 1):
    for i in xrange(0, amount):
        cmd = 'nohup %s/ib_stress.sh %d > /dev/null &' % ( SSA_SCRIPTS, delay)
    pdsh_run(nodes, cmd)
    return 0

def stop_ib_acme(nodes):
    pdsh_run(nodes, 'killall ib_stress.sh 2>/dev/null')
    return 0

def start_counters(nodes, delay, output_dir):
    status = 0
    counters_log = '%s/`hostname`_counters.log' % output_dir
    pdsh_run(nodes, 'mkdir -p %s' % LOG_DIR)
    pdsh_run(nodes, 'nohup %s/server_counters.sh `pgrep "ibacm|ibssa|opensm"` %d > %s &' % ( SSA_SCRIPTS, delay, counters_log))
    return 0

def stop_counters(nodes):
    pdsh_run(nodes, 'killall server_counters.sh 2>/dev/null')
    return 0

