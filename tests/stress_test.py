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
TIMESTAMP = time.strftime("%Y%m%d_%H%M%S")

sys.path.append("%s/../" % os.path.dirname(os.path.abspath( __file__ )))
import ssa_tools_utils


rch_global_dict = {}
rch_global_dict['test_description'] = {}
rch_global_dict['timeout'] = 300
rch_global_dict['exclude_nodes'] = []

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-t', dest = 'topology', help = 'Provide file with SSA setup topology', metavar = 'setup_example.ini')
parser.add_option('-s', '--start', dest = 'start', help = 'Starts stress test', action = 'store_true')
parser.add_option('-p', '--stop', dest = 'stop', help = 'Stops stress test', action = 'store_true')
parser.add_option('-d', '--scratch_directory', dest = 'scretch_folder', help = 'Mandatory and same for start and stop' )

(options, _) = parser.parse_args()
if not options.topology or (not options.scretch_folder and (options.start or options.stop)):
    parser.print_help()
    sys.exit(1)

if not options.scretch_folder:
    rch_global_dict['scretch_folder'] = '/tmp/%s' % TIMESTAMP
else:
    rch_global_dict['scretch_folder'] = options.scretch_folder

if not os.path.exists(rch_global_dict['scretch_folder']):
    os.mkdir(rch_global_dict['scretch_folder'])

rch_global_dict['topology'] = options.topology
rch_global_dict['test_folder'] = '%s/%s_%s' % (ssa_tools_utils.NFS_LOGS_DIR, TIMESTAMP, TEST_NAME) 
os.mkdir(rch_global_dict['test_folder'])

def test_report( test_header, phase, status):
    if status == 0:
        print '-I- Passed. %s %s . status = %d.' % ( test_header, phase, status)
    else:
        print '-I- Failed. %s %s . status = %d.' % ( test_header, phase, status)
    return None



def find_all_tests():
    if options.stop:
        return ['stop_stress']
    elif options.start:
        return ['start_stress']
    else:
        return ['start_stress','stop_stress']



def start_stress(ibmsnet):
    test_header = inspect.getframeinfo(inspect.currentframe()).function    
    phase = 'Stress Test'
    rch_global_dict['test_description'][test_header] = phase
    status = 0
    counter_delay = 30
    number_of_queries = 10

    acm_nodes = rch_global_dict['acm_nodes']
    #acm_nodes = random.sample(rch_global_dict['acm_nodes'],len(rch_global_dict['acm_nodes'])/2)

    print 'Start counters on %s' % ','.join(acm_nodes)
    counters_log = '%s/`hostname`_counters.log' % (rch_global_dict['scretch_folder'])
    ssa_tools_utils.pdsh_run(acm_nodes, 'mkdir -p %s' % rch_global_dict['scretch_folder'])
    ssa_tools_utils.pdsh_run(acm_nodes, 'nohup %s/server_counters.sh `/usr/bin/pgrep ibacm` %d > %s &' % ( ssa_tools_utils.SSA_SCRIPTS, counter_delay, counters_log))

    print 'Start ACM stress on %s' % ','.join(acm_nodes)

    for i in xrange(0, number_of_queries):
        ib_acme_log = '%s/`hostname`_ibstress_%d.log' % (rch_global_dict['scretch_folder'], i)
        cmd = 'nohup %s/ib_stress.sh %d > %s &' % ( ssa_tools_utils.SSA_SCRIPTS, i, ib_acme_log)
        ssa_tools_utils.pdsh_run(acm_nodes,cmd)

    test_report(test_header, phase, status)
    return status

def stop_stress(ibmsnet):
    test_header = inspect.getframeinfo(inspect.currentframe()).function    
    phase = 'Stress Test'
    rch_global_dict['test_description'][test_header] = phase
    status = 0
    acm_nodes = rch_global_dict['acm_nodes']

    o = ssa_tools_utils.pdsh_run(acm_nodes, 'killall ib_stress.sh server_counters.sh 2>/dev/null')
    time.sleep(5)
    o = ssa_tools_utils.pdsh_run(acm_nodes, 'sudo mv %s/* %s/ 2>/dev/null' % (rch_global_dict['scretch_folder'], rch_global_dict['test_folder']))
    time.sleep(10)
    
    o = commands.getoutput('%s/maintain.py -t %s -e' % (ssa_tools_utils.SSA_HOME, rch_global_dict['topology']))
    o = commands.getoutput('%s/logcollector.py -t %s -o %s' % (ssa_tools_utils.SSA_HOME, rch_global_dict['topology'], rch_global_dict['test_folder']))

    for cmd in ['grep -rni "failed|ERR" %s' % rch_global_dict['scretch_folder'],]:
        o = commands.getoutput(cmd)
        print "%s\n%s" % (cmd, o)
        if o != '':
            status = 1

    test_report(test_header, phase, status)
    return status



def run(simulator, sim_dir = '/tmp', opensm = 'opensm', memchk = False, osmargs = []):
    
    status = 0
    tests = find_all_tests()
    #Simulator/Real Fabric Support    
    rch_global_dict.update(ssa_tools_utils.read_config(rch_global_dict['topology']))
    
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

    print commands.getoutput('zip %s.zip -r %s >/dev/null' % (rch_global_dict['test_folder'], rch_global_dict['test_folder']))
    os.system('rm -rf %s' % rch_global_dict['test_folder'])
    print 'Test logs saved under %s.zip' % rch_global_dict['test_folder']

    return status

if __name__ == "__main__":
    status = run(None)
    if status == 0:
        print 'PASSED'
    else:
        print 'FAILED'
    sys.exit(status)

