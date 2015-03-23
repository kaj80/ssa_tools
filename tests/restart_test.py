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
rch_global_dict['timeout'] = 600
rch_global_dict['exclude_nodes'] = []
rch_global_dict['min_interval'] = 0
rch_global_dict['max_interval'] = 100
 
from optparse import OptionParser
parser = OptionParser()
parser.add_option('-t', dest = 'topology', help = 'Provide file with SSA setup topology', metavar = 'setup_example.ini')
parser.add_option('-l', '--local', dest = 'local', help = 'Run acm test on local host', action = 'store_true')
parser.add_option('-i', '--test_time', dest = 'timeout', help = 'Run time for each test', metavar = 'a number of sec or -1 for endless' )
parser.add_option('-o', '--output_folder', dest = 'log_dir', help = 'Output folder')

(options, _) = parser.parse_args()
if not options.topology:
    parser.print_help()
    sys.exit(1)

rch_global_dict['topology'] = options.topology
if options.log_dir:
    rch_global_dict['log_dir'] = options.log_dir

if options.timeout:
    if options.timeout == '-1':
        rch_global_dict['timeout'] = 9999999999999999
    else:
        rch_global_dict['timeout'] =int(options.timeout)


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



def test_0_0_1(ibmsnet):
    test_header = inspect.getframeinfo(inspect.currentframe()).function 
    phase = 'Reconnect Test'
    rch_global_dict['test_description'][test_header] = phase
    status = 0
    nodes = []
    for typ in [ 'core', 'distrib', 'access', 'acm' ]:
        for node in rch_global_dict['%s_nodes' % typ]:
             nodes.append({node:typ})
    random.shuffle(nodes)
    stop_time = time.time() + rch_global_dict['timeout']
    while ( stop_time - time.time() > 0):
        n = random.choice(nodes)        
        node = n.keys()[0]
        delay = random.randint(  rch_global_dict['min_interval'],  rch_global_dict['max_interval'])
        print 'Restarting %s after %d s' % (str(n), delay )
        s = ssa_tools_utils._ssa_action(node, 'stop', n[node])
        time.sleep(delay)
        s = ssa_tools_utils._ssa_action(node, 'start', n[node])

        delay = random.randint(  rch_global_dict['min_interval'],  rch_global_dict['max_interval'])
        time.sleep(delay)
        

    print 'See logs in %s' % rch_global_dict['log_dir']
    test_report(test_header, phase, status)

    return status


def run(simulator, sim_dir = '/tmp', opensm = 'opensm', memchk = False, osmargs = []):
    
    status = 0
    tests = find_all_tests()
    #Simulator/Real Fabric Support    
    rch_global_dict.update(ssa_tools_utils.read_config(rch_global_dict['topology']))
    rch_global_dict['log_dir'] = rch_global_dict.get('log_dir', '%s/%s_%s' % ( ssa_tools_utils.NFS_LOGS_DIR,  time.strftime("%Y%m%d_%H%M%S"), os.path.basename(__file__).rstrip('.py')))
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

    print commands.getoutput('zip %s.zip -r %s >/dev/null' % (rch_global_dict['log_dir'], rch_global_dict['log_dir']))
    os.system('rm -rf %s' % rch_global_dict['log_dir'])
    print 'Test logs saved under %s.zip' %  rch_global_dict['log_dir'] 
    return status

if __name__ == "__main__":
    status = run(None)
    if status == 0:
        print 'PASSED'
    else:
        print 'FAILED'
    sys.exit(status)


