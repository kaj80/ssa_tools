#!/usr/bin/python


# This test check SSA Distribution tree consistency after SM changing
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
    phase = 'Start Second SM with higher priority'
    rch_global_dict['test_description'][test_header] = phase
    status = 0

    #Start OpenSM    
    print 'Start Opensm with lower priority'
    ib_network = {'core':[], 'distrib':[], 'access':[], 'acm':[]}    
    ib_network['core'].append(ssa_tools_utils.core(rch_global_dict['core_nodes'][0]))
    ib_network['core'].append(ssa_tools_utils.core(rch_global_dict['core_nodes'][1]))
    
    ib_network['core'][1].start()        
    
    for node in rch_global_dict['distrib_nodes']:
        print 'Start Distrib on %s' % node
        d1 = ssa_tools_utils.distrib(node)                 
        d1.start()
        ib_network['distrib'].append(d1)
    
    for node in rch_global_dict['access_nodes']:
        print 'Start Access on %s' % node
        a1 = ssa_tools_utils.access(node)                 
        a1.start()
        ib_network['access'].append(a1)
    
    for node in rch_global_dict['acm_nodes']:
        print 'Start Distrib on %s' % node
        acm = ssa_tools_utils.acm(node)                 
        acm.start()
        ib_network['acm'].append(acm)
    
        
    distrib_tree_1 = ssa_utils.get_distribution_tree(rch_global_dict['core_nodes'][1])
    print 'Start Opensm with higher priority'
    ib_network['core'][0].start()        
    distrib_tree_0 = ssa_utils.get_distribution_tree(rch_global_dict['core_nodes'][0])
    
    print 'First_SM_D_Tree\n*********************************\n%s\n***************' % distrib_tree_1
    print 'Second_SM_D_Tree\n*********************************\n%s\n**************' % distrib_tree_0
    i = 0
    if distrib_tree_1 != distrib_tree_0:
        print 'Distribution Trees are different'
        for _ in distrib_tree_0:
            if distrib_tree_0[i] != distrib_tree_1[i]:
                print '[%d] ERROR \n %s \n %s' % ( i, distrib_tree_0[i], distrib_tree_1[i] )
                i = i + 1

        status = 1
    else:
        print 'Distribution Trees are equal'
    
    
    for k,v in ib_network.iteritems():
        for n in v:
            try:
                n.stop()
            except:
                print 'Error.'
                pprint(ib_network)
                status = 1
    return status



def test_0_0_1(ibmsnet):
    test_header = inspect.getframeinfo(inspect.currentframe()).function    
    phase = 'Stop SM with higher priority'
    rch_global_dict['test_description'][test_header] = phase
    status = 0

    #Start OpenSM    
    print 'Start Opensm with lower priority'
    ib_network = {'core':[], 'distrib':[], 'access':[], 'acm':[]}    
    ib_network['core'].append(ssa_tools_utils.core(rch_global_dict['core_nodes'][0]))
    ib_network['core'].append(ssa_tools_utils.core(rch_global_dict['core_nodes'][1]))
    
    ib_network['core'][0].start()        
    ib_network['core'][1].start()
    
    for node in rch_global_dict['distrib_nodes']:
        print 'Start Distrib on %s' % node
        d1 = ssa_tools_utils.distrib(node)                 
        d1.start()
        ib_network['distrib'].append(d1)
    
    for node in rch_global_dict['access_nodes']:
        print 'Start Access on %s' % node
        a1 = ssa_tools_utils.access(node)                 
        a1.start()
        ib_network['access'].append(a1)
    
    for node in rch_global_dict['acm_nodes']:
        print 'Start Distrib on %s' % node
        acm = ssa_tools_utils.acm(node)                 
        acm.start()
        ib_network['acm'].append(acm)
    
        
    distrib_tree_0 = ssa_utils.get_distribution_tree(rch_global_dict['core_nodes'][0])
    
    print 'Stop Opensm with higher priority'
    ib_network['core'][0].stop()        
    time.sleep(20)
    distrib_tree_1 = ssa_utils.get_distribution_tree(rch_global_dict['core_nodes'][1])
    
    print 'First SM D_Tree\n%s' % distrib_tree_0
    print 'Second SM D_Tree\n%s' % distrib_tree_1
    if distrib_tree_1 != distrib_tree_0:
        print 'Distribution Trees are different'
        status = 1
    else:
        print 'Distribution Trees are equal'
 
    for k,v in ib_network.iteritems():
        for n in v:
            try:
                n.stop()
            except:
                print 'Error.' 
                pprint(ib_network)
                status = 1
    
    return status


def test_0_0_2(ibmsnet):
    test_header = inspect.getframeinfo(inspect.currentframe()).function    
    phase = 'Restart SM'
    rch_global_dict['test_description'][test_header] = phase
    status = 0

    #Start OpenSM    
    print 'Restart OpenSM'
    ib_network = {'core':[], 'distrib':[], 'access':[], 'acm':[]}    
    ib_network['core'].append(ssa_tools_utils.core(rch_global_dict['core_nodes'][0]))   
    ib_network['core'][0].start()        
    
    for node in rch_global_dict['distrib_nodes']:
        print 'Start Distrib on %s' % node
        d1 = ssa_tools_utils.distrib(node)                 
        d1.start()
        ib_network['distrib'].append(d1)
    
    for node in rch_global_dict['access_nodes']:
        print 'Start Access on %s' % node
        a1 = ssa_tools_utils.access(node)                 
        a1.start()
        ib_network['access'].append(a1)
    
    for node in rch_global_dict['acm_nodes']:
        print 'Start Distrib on %s' % node
        acm = ssa_tools_utils.acm(node)                 
        acm.start()
        ib_network['acm'].append(acm)
    
        
    distrib_tree_0 = ssa_utils.get_distribution_tree(rch_global_dict['core_nodes'][0])
    
    print 'Restart Opensm with higher priority'
    ib_network['core'][0].restart()        
    time.sleep(30)
    distrib_tree_1 = ssa_utils.get_distribution_tree(rch_global_dict['core_nodes'][0])
    
    print 'First SM D_Tree\n%s' % distrib_tree_0
    print 'After Restart SM D_Tree\n%s' % distrib_tree_1
    if distrib_tree_1 != distrib_tree_0:
        print 'Distribution Trees are different'
        status = 1
    else:
        print 'Distribution Trees are equal'
    
    
    for k,v in ib_network.iteritems():
        for n in v:
            try:
                n.stop()
            except:
                print 'Error.'
                pprint(ib_network)
                status = 1

    return status

def test_0_0_3(ibmsnet):
    test_header = inspect.getframeinfo(inspect.currentframe()).function    
    phase = 'Kill SM with higher priority'
    rch_global_dict['test_description'][test_header] = phase
    status = 0

    #Start OpenSM    
    print 'Start Opensm with lower priority'
    ib_network = {'core':[], 'distrib':[], 'access':[], 'acm':[]}    
    ib_network['core'].append(ssa_tools_utils.core(rch_global_dict['core_nodes'][0]))
    ib_network['core'].append(ssa_tools_utils.core(rch_global_dict['core_nodes'][1]))
    
    ib_network['core'][0].start()        
    ib_network['core'][1].start()
    
    for node in rch_global_dict['distrib_nodes']:
        print 'Start Distrib on %s' % node
        d1 = ssa_tools_utils.distrib(node)                 
        d1.start()
        ib_network['distrib'].append(d1)
    
    for node in rch_global_dict['access_nodes']:
        print 'Start Access on %s' % node
        a1 = ssa_tools_utils.access(node)                 
        a1.start()
        ib_network['access'].append(a1)
    
    for node in rch_global_dict['acm_nodes']:
        print 'Start Distrib on %s' % node
        acm = ssa_tools_utils.acm(node)                 
        acm.start()
        ib_network['acm'].append(acm)
    
        
    distrib_tree_0 = ssa_utils.get_distribution_tree(rch_global_dict['core_nodes'][0])
    
    print 'Kill Opensm with higher priority'
    ib_network['core'][0].kill()   
    time.sleep(20)
    distrib_tree_1 = ssa_utils.get_distribution_tree(rch_global_dict['core_nodes'][1])
    
    print 'First SM D_Tree\n%s' % distrib_tree_0
    print 'Second SM D_Tree\n%s' % distrib_tree_1
    if distrib_tree_1 != distrib_tree_0:
        print 'Distribution Trees are different'
        status = 1
    else:
        print 'Distribution Trees are equal'
    
    for k,v in ib_network.iteritems():
        for n in v:
             try:
                 n.stop()
             except:
                 print 'Error.'
                 pprint(ib_network)
                 status = 1
    
    return status


def test_0_0_4(ibmsnet):
    test_header = inspect.getframeinfo(inspect.currentframe()).function    
    phase = 'PortBounce of SM with higher priority'
    rch_global_dict['test_description'][test_header] = phase
    status = 0

    #Start OpenSM    
    print 'Start Opensm with lower priority'
    ib_network = {'core':[], 'distrib':[], 'access':[], 'acm':[]}    
    ib_network['core'].append(ssa_tools_utils.core(rch_global_dict['core_nodes'][0]))
    ib_network['core'].append(ssa_tools_utils.core(rch_global_dict['core_nodes'][1]))
    
    ib_network['core'][0].start()        
    ib_network['core'][1].start()
    
    for node in rch_global_dict['distrib_nodes']:
        print 'Start Distrib on %s' % node
        d1 = ssa_tools_utils.distrib(node)                 
        d1.start()
        ib_network['distrib'].append(d1)
    
    for node in rch_global_dict['access_nodes']:
        print 'Start Access on %s' % node
        a1 = ssa_tools_utils.access(node)                 
        a1.start()
        ib_network['access'].append(a1)
    
    for node in rch_global_dict['acm_nodes']:
        print 'Start Distrib on %s' % node
        acm = ssa_tools_utils.acm(node)                 
        acm.start()
        ib_network['acm'].append(acm)
    
        
    distrib_tree_0 = ssa_utils.get_distribution_tree(rch_global_dict['core_nodes'][0])
    
    ssa_utils.node_port_bounce(rch_global_dict['core_nodes'][0])
        
    time.sleep(20)
    distrib_tree_1 = ssa_utils.get_distribution_tree(rch_global_dict['core_nodes'][1])
    
    print 'First SM D_Tree\n%s' % distrib_tree_0
    print 'Second SM D_Tree\n%s' % distrib_tree_1
    if distrib_tree_1 != distrib_tree_0:
        print 'Distribution Trees are different'
        status = 1
    else:
        print 'Distribution Trees are equal'
    
    for k,v in ib_network.iteritems():
        for n in v:
            try:
              n.stop()
            except:
                print 'Error.'
                pprint(ib_network)
                status = 1
    
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
        ssa_tools_utils.ssa_clean_setup(rch_global_dict)
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





