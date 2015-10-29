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
rch_global_dict['timeout'] = 10
rch_global_dict['exclude_nodes'] = []
rch_global_dict['min_interval'] = 0
rch_global_dict['max_interval'] = 100
rch_global_dict['boot_retries'] = 200 
rch_global_dict['ib_acme_delay'] = 5
rch_global_dict['ib_acme_num'] = 1

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
        tests = sorted(tests)
        
    print 'Following tests about to be executed:', tests
    return tests


def test_0_0_0(ibmsnet):
    test_header = inspect.getframeinfo(inspect.currentframe()).function 
    phase = 'Reboot Test'
    rch_global_dict['test_description'][test_header] = phase
    status = 0
    nodes = []
    for typ in [ 'acm', ]:
    #for typ in [ 'core', 'distrib', 'access', 'acm' ]:
        for node in rch_global_dict['%s_nodes' % typ]:
             nodes.append({node:typ})
    random.shuffle(nodes)
    stop_time = time.time() + rch_global_dict['timeout']
    while ( stop_time - time.time() > 0):
        n = random.choice(nodes)        
        node = n.keys()[0]
        delay = random.randint(  rch_global_dict['min_interval'],  rch_global_dict['max_interval'])
        print 'Restarting %s after %d s' % (str(n), delay )
        (s, o) = ssa_tools_utils.execute_on_remote('reboot', node)
	del ssa_tools_utils.conn_dict[node]
        time.sleep(120)

        #Wait for boot
        r = rch_global_dict['boot_retries']
        print 'Waiting for %s to boot\n%s\n%s' % (node, s, o)
        (s, _) = ssa_tools_utils.execute_on_remote('uptime', node)
        while (s > 0):         
            print 'Waiting for %s to boot\n%s\n%s' % (node, s, o)
            (s, _) = ssa_tools_utils.execute_on_remote('uptime', node)
            time.sleep(10)
            r = r - 1
            if (r <= 0):
                print 'ERROR %s still down' % node
                status = 1
                test_report(test_header, phase, status)
                return status

        #Start SSA
        s = ssa_tools_utils._ssa_action(node, 'start', n[node])

        #Start ib_acme
        (s, o) = ssa_tools_utils.execute_on_remote('pgrep ib_stress.sh', node)
        if s > 0:
            if ssa_tools_utils.start_ib_acme(node, rch_global_dict['ib_acme_delay'], rch_global_dict['ib_acme_num']) > 0:
                print 'ERROR to execute ib_acme on %s' % node
                status = 1
                break

        else:
            print 'ERROR ib_acme already running on %s' % node
            break

        delay = random.randint(  rch_global_dict['min_interval'],  rch_global_dict['max_interval'])
        time.sleep(delay)

    for node in nodes:
	ssa_tools_utils.stop_ib_acme(node.keys())
  
    for cmd in ['%s/maintain.py -t %s --setup status > %s/ssa_status.log' % (ssa_tools_utils.SSA_HOME, rch_global_dict['topology'], rch_global_dict['log_dir']) ,
                '%s/maintain.py -t %s -e > %s/ssa_errors.log' % (ssa_tools_utils.SSA_HOME, rch_global_dict['topology'], rch_global_dict['log_dir']),
                '%s/logcollector.py -t %s  -o %s' % (ssa_tools_utils.SSA_HOME, rch_global_dict['topology'], rch_global_dict['log_dir']) ]:
        print cmd
        o = commands.getoutput(cmd)

#    o = commands.getoutput("cat  %s/ssa_errors.log" %  rch_global_dict['log_dir'])
#    o_status = commands.getoutput("cat %s/ssa_status.log" %  rch_global_dict['log_dir'])
#    if o.find('Found errors found on') >= 0 or o_status.find('STOP') >= 0: 
#        print 'There are errors in %s/ssa_errors.log' %  rch_global_dict['log_dir']
#        status = 1

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
        print 'PASSED %s' % __file__
    else:
        print 'FAILED %s' % __file__
    sys.exit(status)






