#!/usr/bin/python
import os
import random
import sys
sys.path.append("%s/ssa_tools" % os.path.dirname(os.path.abspath( __file__ )))
import ssa_tools_utils      
import time
import socket

CFG_FILES = {'mpi_home' : '/usr/local/',
#--mca btl_openib_if_include mthca0:1
             'mpi_options' : '--mca btl openib,self --mca btl_openib_cpc_include rdmacm --map-by node --mca pml ob1 -quiet --allow-run-as-root',
             'mpi_benchmark' : '/.autodirect/mtrswgwork/lennyb/work/UFM/SSA/imb/src/IMB-MPI1',
             'mpi_benchmark_options' : 'PingPing PingPongPingPong Sendrecv Bcast Allgather Allgatherv Gather Gatherv Scatter Scatterv Alltoall Alltoallv Reduce Reduce_scatter Allreduce Barrier',
             'nfs_folder' : '/.autodirect/mtrswgwork/lennyb/tmp/'
}

class mpi():
    def __init__(self, hosts):        
        self.home = CFG_FILES['mpi_home'] #MPIHOME
        self.options = CFG_FILES['mpi_options']   #additional options        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.log = '/tmp/%s.mpirun.log' % timestamp
        
        self.benchmark = CFG_FILES['mpi_benchmark']   #benvhmark to run         
        self.benchmark_options = CFG_FILES['mpi_benchmark_options']
        
        self.mpihost = hosts[0]  #rum mpi from
        self.np = 0 
        self.pid = None
        
        self.hostfile = '%s/%s_hostfile.txt' % ( CFG_FILES['nfs_folder'], timestamp)
        f = open(self.hostfile, 'w')
        f.write('\n'.join(hosts))
        f.write('\n')
        f.close()  
        self.hosts = '--hostfile %s' % self.hostfile
        self.np = '-np %d' % len(hosts)


    def connect(self):       
        self.connection = ssa_tools_utils.run_on_remote(self.mpihost, root = False)
        return 0
                        
    def run(self):              
        command = 'sudo LD_LIBRARY_PATH=%s %s/bin/mpirun %s' % \
                ( self.home + '/lib', self.home, \
                  ' '.join([self.np, self.hosts, self.options, self.benchmark, self.benchmark_options ]))
        self.connection.run(command)
        f = open(self.log, 'w')
        print self.connection.output
        f.write(self.connection.output)
        f.close()
        print 'MPI log saved under %s' %  self.log
        return self.connection.status 
    
    def run_in_background(self, cmd):
        command = '%s/bin/mpirun %s ' % ( self.home, ' '.join([self.np, self.hosts, self.options, self.benchmark, self.benchmark_options ]))
        self.pid = self.connection.run_in_background(command)    
        return self.pid
    
    def close(self):
        if self.pid:
            self.connection.kill_pid(self.pid)        
        return self.connection.close()
    
    def error_check(self):
        for line in open(self.log, 'r'):
            for err in ['mpirun was unable', 'Your MPI job will now abort, sorry']:
                if line.find(err) >= 0:
                    print '-E- failed to run mpi\n%s' % line 
                    return 1
        return 0
    
    def _get_output(self):
        self.connection.run('scp %s %s:/%s' % (self.log, socket.gethostname(), self.log))
        
    def get_log(self):
        return self.log
        
    def randomize_hosts(self): 
        h = self.hosts.split(',')
        random.shuffle(h)
        self.hosts = ','.join(h)
        
