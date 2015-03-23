#!/usr/bin/python



import os
import sys
import inspect
from pprint import pprint
import time
import commands
import datetime
import random
random.seed(os.environ.get('SEED',0))

sys.path.append("%s/../" % os.path.dirname(os.path.abspath( __file__ )))
import ssa_tools_utils
import ssa_mpi

rch_global_dict = {}
rch_global_dict['test_description'] = {}
rch_global_dict['timeout'] = 300
rch_global_dict['exclude_nodes'] = ['dev-r-vrt-039']

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-t', dest = 'topology', help = 'Provide file with SSA setup topology', metavar = 'setup_example.ini')

(options, _) = parser.parse_args()
if not options.topology:
    parser.print_help()
    sys.exit(1)

rch_global_dict['topology'] = options.topology

def test_report( test_header, phase, status):
    if status == 0:
        print '-I- Passed. %s %s . status = %d.' % ( test_header, phase, status)
    else:
        print '-I- Failed. %s %s . status = %d.' % ( test_header, phase, status)
        return None


def find_all_tests():
    tests = []
    if os.environ.has_key('SSA_run_tests'):
        if os.environ['SSA_run_tests'].find('-') >= 0:
            t = os.environ['SSA_run_tests'].replace(' ','').replace(',','').split('-')
            a = t[0].split('_')
            b = t[1].split('_')
            for i in xrange(int(a[-1]), int(b[-1]) + 1):
                tests.append('%s_%d' % ( '_'.join(a[:-1]), i))
        else:
            tests = os.environ['SSA_run_tests'].replace(' ','').split(',')
    else:       
        tests = [l for l in globals() if l.startswith('test_') and 'report' not in l] 
        tests = sorted(tests) #+ sorted([l for l in globals() if l.startswith('%s_test_' % ssa_tools_utils.SSA_SETUP) and 'report' not in l])
        
    print 'Following tests about to be executed:', tests
    return tests


def test_0_0_0(ibmsnet):
    test_header = inspect.getframeinfo(inspect.currentframe()).function    
    phase = 'Run OMPI sanity check'
    rch_global_dict['test_description'][test_header] = phase
    status = 0
    log_dir = '%s/%s' % (rch_global_dict['log_dir'], test_header)
    os.mkdir(log_dir)

    errors = []
    acm_cache = {}
    acm_src = rch_global_dict['acm_nodes'][0]
    for node in rch_global_dict['acm_nodes']:
        acm_con = ssa_tools_utils.run_on_remote(node)
        acm_con.run('/usr/sbin/ibstat |grep Active')
        if acm_con.output.find('Active') <= 0:
            print 'ERROR IB on %s\n%s' % (node, acm_con.output)
            rch_global_dict['exclude_nodes'].append(node)
            continue
        acm_con.run('/usr/local/bin/ib_acme -P')
        cache = acm_con.output.split()
        if cache[-1] == '0x0':
            acm_cache[node] = cache[-4].split(',')
        else:
            acm_cache[node] = ' '.join(cache)
        
        mpi = ssa_mpi.mpi([node,node])
        mpi.mpihost = acm_src
        mpi.log = '%s/%s_mpi.log' % ( log_dir, node )
        mpi.benchmark_options = 'pingpong ' 
        mpi.connect()
        status = mpi.run()
        mpi.close()
        if status != 0:
            errors.append(node)
        acm_con.run('/usr/local/bin/ib_acme -P')
        o = acm_con.output.split()
        if o[-1] == '0x0':
            if (o[-4].split(',')[-1] <= acm_cache[node][-1]) or (o[-4].split(',')[2] == acm_cache[node][2]):
                print 'ERROR. %s ACM cache was not used during MPI tests' % node
                print '%s Cache before MPI is %s' % (node, acm_cache[node])
                print '%s Cache after MPI is %s' % (node, o[-4])
                status = status + 1
        else:
            print 'ERROR', ' '.join(o)
            status = status + 1
        try:
            d = int(o[-4].split(',')[-1]) - int(acm_cache[node][-1])
        except Exception as e:
            print 'ERROR %s Cache query failed %s' % (node, e)
            sys.exit(1)
        print '%s Cache query change during MPI test is %d' % (node, d)
        if d <=0 :
            print 'ERROR %s Cache query change during MPI test %d <= 0' % (node, d)
            sys.exit(1)

    valid = list(set(rch_global_dict['acm_nodes']).difference(set(errors)))
    hostfile = '%s/mpi_hosts_%s' % (log_dir, time.strftime("%Y%m%d_%H%M%S"))
    f = open(hostfile, 'w')
    f.write("\n".join(valid))
    f.close()
    print 'Found %d valid_nodes. Use mpirun --hostfile %s' % ( len(valid), hostfile)
    print 'The following nodes fail to run mpi\n',  sorted(errors)
    rch_global_dict['exclude_nodes'] = sorted(rch_global_dict['exclude_nodes'] + errors)
    test_report(test_header, phase, status)
    return status


def test_0_0_1(ibmsnet):
    test_header = inspect.getframeinfo(inspect.currentframe()).function    
    phase = 'Run OMPI with increasing np'
    rch_global_dict['test_description'][test_header] = phase
    status = 0
    log_dir = '%s/%s' % (rch_global_dict['log_dir'], test_header)
    os.mkdir(log_dir)

    valid = sorted(list(set(rch_global_dict['acm_nodes']).difference(set(rch_global_dict['exclude_nodes']))))
    i = 2
    while (i <= len(valid)):
        mpi = ssa_mpi.mpi(valid[0:i])
        mpi.mpihost = valid[0]
        print 'Running MPI from %s to %s' % ( mpi.mpihost, str(valid[0:i]))
        mpi.benchmark_options = 'barrier -msglen %s/tmp/length -npmin %d' % (ssa_tools_utils.SSA_HOME, i)
        mpi.connect()
        mpi.log = '%s/mpi_%d' % (log_dir, i)
        status = mpi.run()
        mpi.close()
        if status != 0:
            status = 1 
            break
        i = i + 1

    print 'Failed to run MPI at this point'
    test_report(test_header, phase, status)
    return status





#Check ib_acme cashe status before and after mpi 
#Still unstable test
def test_1_0_1(ibmsnet):
    test_header = inspect.getframeinfo(inspect.currentframe()).function    
    phase = 'Run OMPI IMB Benchmark'    
    rch_global_dict['test_description'][test_header] = phase
    status = 0
    log_dir = '%s/%s' % (rch_global_dict['log_dir'], test_header)
    os.mkdir(log_dir)
    ib_acme = {}
    acm_nodes = random.sample(rch_global_dict['acm_nodes'], min(len(rch_global_dict['acm_nodes']),4))
    for acm in acm_nodes:
        ib_acme[acm] = []
        ib_acme[acm].append(ssa_tools_utils.ib_acme(acm))         #ib_acme[0] is a connection
        ib_acme[acm].append(acm)                            #ib_acme[1] is a acm name
        ib_acme[acm].append(ib_acme[acm][0].show_cache())   #ib_acme[2] is ib_acme -P before MPI run
    
    hosts = acm_nodes
    mpi = ssa_mpi.mpi(hosts)    
    mpi.connect()
    mpi.log = '%s/mpi.log' % log_dir
    mpi.run()
    mpi.close()
    
    for acm in acm_nodes:        
        ib_acme[acm].append(ib_acme[acm][0].show_cache())   #ib_acme[3] is ib_acme -P after MPI run
        ib_acme[acm][0].close()
        
    print ','.join(['Error Count', 'Resolve Count', 'No Data', 'Addr Query Count', 'Addr Cache Count', 'Route Query Count', 'Route Cache Count'])
    
    for acm in acm_nodes:
        diff = map(int.__sub__,ib_acme[acm][3], ib_acme[acm][2])
        if acm == acm_nodes[0]:
            print 'Continuing since seems that cache is not quired on acm that runs OpenMPI'
            continue
        if len(diff) == 0 or diff[-1] == 0:
            print '-E- %s did not use cache' % acm
            status = 1 
        print 'SSA cache usage %s: %s' % (acm, diff)
    
    test_report(test_header, phase, status)
    return status

 

def run(simulator, sim_dir = '/tmp', opensm = 'opensm', memchk = False, osmargs = []):
    
    status = 0
    '''
    rch_global_dict['sources'] = os.environ['REGRESSION_SOURCE_PATH']
    rch_global_dict['opensm'] = '%s/usr/sbin/opensm' %  rch_global_dict['sources']
    rch_global_dict['simulator'] = simulator
    rch_global_dict['osm_dir'] = sim_dir
    rch_global_dict['memchk'] = memchk  
    rch_global_dict['log_dir'] = '%s/%d' % (rch_global_dict['osm_dir'], subtest_log_dir().id)
    rch_global_dict['distrib_nodes'] = []
    rch_global_dict['acm_nodes'] = []
    '''
    tests = find_all_tests()
    rch_global_dict['log_dir'] = '%s/%s_%s' % ( ssa_tools_utils.NFS_LOGS_DIR,  time.strftime("%Y%m%d_%H%M%S"), os.path.basename(__file__).rstrip('.py'))
    os.mkdir(rch_global_dict['log_dir'])
    #Simulator/Real Fabric Support    
    rch_global_dict.update(ssa_tools_utils.read_config(rch_global_dict['topology']))
    
    rch_global_dict['nodes'] = []
    rch_global_dict['tests_results'] = {}
    pprint(rch_global_dict)
   
    rch_global_dict['acm_nodes'] =  list(set(rch_global_dict['acm_nodes']) - set(rch_global_dict['exclude_nodes']))

#    rch_global_dict['pml_cfg'] = '%s/pml.cfg' % rch_global_dict['osm_dir']
      
        
    print 'The following tests will be executed', tests
    failed_tests = []
    for test in tests:
        if test == '':
            continue
        print '-I- STARTED %s' % test
        start_time = time.time()        
#        ssa_tools_utils.ssa_clean_setup(rch_global_dict)        
        rc = eval(test)(None)        
        total_time = round(time.time() - start_time, 2)
        if rc > 0:
            print '-I- ****************   Failed test %s **************************' % test
            rch_global_dict['tests_results'][test] = 'FAILED %s        %s sec' % (rch_global_dict['test_description'][test], total_time)
            status += 1
            failed_tests.append(test)
        elif rc == 0:
            rch_global_dict['tests_results'][test] = 'PASSED %s        %s sec' % (rch_global_dict['test_description'][test], total_time)
        elif rc == -1:
            rch_global_dict['tests_results'][test] = 'SKIPPED %s        %s sec' % (rch_global_dict['test_description'][test], total_time)        
        else:
            rch_global_dict['tests_results'][test] = 'UNKNOWN %s        %s sec' % (rch_global_dict['test_description'][test], total_time)
        
        print '-I- FINISHED %s and %s' % (test, rch_global_dict['tests_results'][test])
#        ssa_tools_utils.ssa_clean_setup(rch_global_dict)


    for stat in ['PASSED', 'SKIPPED', 'FAILED']:
        for k in sorted(rch_global_dict['tests_results'].keys()):
            if rch_global_dict['tests_results'][k].find(stat) >= 0 :
                print k, rch_global_dict['tests_results'][k]
    if len(failed_tests) > 0:
        print 'TEST_RUN_NOTE: Failed %s' % ','.join(failed_tests)
        print 'Test logs saved under %s' %  rch_global_dict['log_dir']
    else:
        print commands.getoutput('sudo -u lennyb zip %s.zip -r %s >/dev/null' % (rch_global_dict['log_dir'], rch_global_dict['log_dir']))
        os.system('rm -rf %s' % rch_global_dict['log_dir'])
        print 'Test logs saved under %s.zip' %  rch_global_dict['log_dir'] 

    return status

if __name__ == "__main__":
    status = run(None)
    if status == 0:
        print 'PASSED %s' % __file__
    else:
        print 'FAILED %s' % __file__
    sys.exit(status)

