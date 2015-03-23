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
sys.path.append("%s/../" % os.path.dirname(os.path.abspath( __file__ )))
import ssa_tools_utils
import ssa_utils

rch_global_dict = {}
rch_global_dict['test_description'] = {}
rch_global_dict['timeout'] = 900
rch_global_dict['exclude_nodes'] = []

from optparse import OptionParser


class Logger(object):    
    def __init__(self, filename, mode="a", buff=0):
        self.stdout = sys.stdout
        self.file = open(filename, mode, buff)
        sys.stdout = self

    def __del__(self):
        self.close()

    def __enter__(self):
        pass

    def __exit__(self, *args):
        pass

    def write(self, message):
        self.stdout.write(message)
        self.file.write(message)

    def flush(self):
        self.stdout.flush()
        self.file.flush()
        os.fsync(self.file.fileno())

    def close(self):
        if self.stdout != None:
            sys.stdout = self.stdout
            self.stdout = None

        if self.file != None:
            self.file.close()
            self.file = None
            
            
            
def find_all_tests(tests = None):
    if tests:
        return sorted(tests.split(','))
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
    phase = 'Restart Master SM'
    rch_global_dict['test_description'][test_header] = phase
    status = 0
    #sm0 should be Master SM
    sm0 = ssa_tools_utils.core(rch_global_dict['core_nodes'][0])
    sm1 = ssa_tools_utils.core(rch_global_dict['core_nodes'][1])
    print '[%s] Stopping Standby SM' % time.strftime("%b %d %H:%M:%S")
    sm1.stop()
    start_test = time.strftime("%b %d %H:%M:%S")
    print '%s Restarting Master SM' %  start_test
    sm0.restart()
    print 'Wait 2m'
    time.sleep(120)
    stop_time = time.strftime("%b %d %H:%M:%S")
    print '%s Collecting logs' % stop_time    
    status = ssa_utils.check_errors(rch_global_dict)
    
    print '%s Starting Standby SM' % time.strftime("%b %d %H:%M:%S")
    sm1.start()
    print "Relevant test time interval %s - %s" % (start_test, stop_time)
    return status



def test_0_0_1(ibmsnet):
    test_header = inspect.getframeinfo(inspect.currentframe()).function    
    phase = 'Change SM from Master to Standby'
    rch_global_dict['test_description'][test_header] = phase
    status = 0
    
    sm0 = ssa_tools_utils.core(rch_global_dict['core_nodes'][0])
    sm1 = ssa_tools_utils.core(rch_global_dict['core_nodes'][1])

    start_test = time.strftime("%b %d %H:%M:%S")
    print '[%s] Stopping Master SM' % start_test
    sm0.stop()
    
    print 'Wait'
    time.sleep(120)
    stop_test = time.strftime("%b %d %H:%M:%S")
    print '%s Collecting logs' % stop_test    
    status = ssa_utils.check_errors(rch_global_dict)
    
    print '%s Starting Master SM' % time.strftime("%b %d %H:%M:%S")
    sm0.start()
    print "Relevant test time interval %s - %s" % (start_test, stop_test)
    status = status + ssa_utils.check_errors(rch_global_dict)    
    return status


def test_0_0_2(ibmsnet):
    test_header = inspect.getframeinfo(inspect.currentframe()).function    
    phase = 'Change SM from Master to Standby by priority'
    rch_global_dict['test_description'][test_header] = phase
    status = 0
    
    sm0 = ssa_tools_utils.core(rch_global_dict['core_nodes'][0])
    sm1 = ssa_tools_utils.core(rch_global_dict['core_nodes'][1])

    print '[%s] Change Standby SM priority' % time.strftime("%b %d %H:%M:%S")
    start_test = time.strftime("%b %d %H:%M:%S")
    sm1.set_value('sm_priority', 1)
    print 'Wait'
    time.sleep(120)
    stop_time = time.strftime("%b %d %H:%M:%S")
    print '%s Collecting logs' % stop_time    
    status = ssa_utils.check_errors(rch_global_dict)
    
    print '%s Change SM priority back to 0' % time.strftime("%b %d %H:%M:%S")    
    sm1.set_value('sm_priority', 0)
    print "Relevant test time interval %s - %s" % (start_test, stop_time)
    
    return status

def test_0_0_3(ibmsnet):
    test_header = inspect.getframeinfo(inspect.currentframe()).function    
    phase = 'Bounce Master SM port'
    rch_global_dict['test_description'][test_header] = phase
    status = 0
    
    sm0 = ssa_tools_utils.core(rch_global_dict['core_nodes'][0])
    sm1 = ssa_tools_utils.core(rch_global_dict['core_nodes'][1])

    sm1.stop()
    start_test = time.strftime("%b %d %H:%M:%S")
    print '%s Bouncing Master SM port' %  start_test
    sw_guid_port = ssa_utils.node_port_state_change(rch_global_dict['core_nodes'][0], 'disable')
    print 'Wait'
    time.sleep(1)
    o = commands.getoutput('ibportstate -G %s enable' % sw_guid_port)
    print '[%s] ibportstate -G %s enable \n%s' % ( time.strftime("%b %d %H:%M:%S"), sw_guid_port, o )
    stop_time = time.strftime("%b %d %H:%M:%S")
    print '%s Collecting logs' % stop_time    
    status = ssa_utils.check_errors(rch_global_dict)
    
    print '%s Starting Standby SM' % time.strftime("%b %d %H:%M:%S")
    sm1.start()
    print "Relevant test time interval %s - %s" % (start_test, stop_time)
    return status



def run(simulator, sim_dir = '/tmp', opensm = 'opensm', memchk = False, osmargs = []):
  
    status = 0
    parser = OptionParser()
    parser.add_option('-t', dest = 'topology', help = 'Provide file with SSA setup topology', metavar = 'setup_example.ini')
    parser.add_option('-i', '--tests', dest = 'tests', help = 'Run specific tests', metavar = ','.join(find_all_tests()))

    (options, _) = parser.parse_args()
    if not options.topology:
        parser.print_help()
        sys.exit(1)

    rch_global_dict['topology'] = options.topology
    tests = find_all_tests(options.tests)

    #Simulator/Real Fabric Support    
    rch_global_dict.update(ssa_tools_utils.read_config(rch_global_dict['topology']))
    rch_global_dict['log_dir'] = '%s/%s_%s' % ( ssa_tools_utils.NFS_LOGS_DIR,  time.strftime("%Y%m%d_%H%M%S"), os.path.basename(__file__).rstrip('.py'))
    os.mkdir(rch_global_dict['log_dir'])

    rch_global_dict['nodes'] = []
    rch_global_dict['tests_results'] = {}
    pprint(rch_global_dict)
    rch_global_dict['acm_nodes'] =  list(set(rch_global_dict['acm_nodes']) - set(rch_global_dict['exclude_nodes']))

    print 'The following tests will be executed', tests
    failed_tests = []
    for test in tests:
        if test == '':
            continue
        print '-I- STARTED %s' % test
        start_time = time.time()        
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

    for stat in ['PASSED', 'SKIPPED', 'FAILED']:
        for k in sorted(rch_global_dict['tests_results'].keys()):
            if rch_global_dict['tests_results'][k].find(stat) >= 0 :
                print k, rch_global_dict['tests_results'][k]
    if len(failed_tests) > 0:
        print 'TEST_RUN_NOTE: Failed %s' % ','.join(failed_tests)
        print 'FAILED %s' %  rch_global_dict['log_dir']
    else:
        print commands.getoutput('zip %s.zip -r %s >/dev/null' % (rch_global_dict['log_dir'], rch_global_dict['log_dir']))
        os.system('rm -rf %s' % rch_global_dict['log_dir'])
        print 'PASSED %s.zip' %  rch_global_dict['log_dir'] 
    return status




if __name__ == "__main__":
    log_file = '/tmp/%s' % os.path.basename(__file__).replace('.py','.log')
    print log_file
    Log=Logger(log_file)
    status = run(None)
    Log.close()
    sys.exit(status)






