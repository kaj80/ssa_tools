#!/usr/bin/python

import os
import sys
import datetime
import random
import commands
import inspect
from pprint import pprint
import time

import urllib2
import json
from pprint import pprint

sys.path.append('%s/../' % os.path.dirname(os.path.abspath( __file__ )))
import ssa_tools_utils

random.seed(os.environ.get('SEED',0))
DEBUG = False

import ssa_utils



rch_global_dict = {}
rch_global_dict['test_description'] = {}
rch_global_dict['email_sender'] = 'lennyb'
rch_global_dict['email_recv'] = 'null@mellanox.com'
rch_global_dict['coverage_exclude'] = '%s/BullseyeCoverageExclusionsSSA_20150119' % os.path.dirname(os.path.abspath( __file__ ))
rch_global_dict['scretch_folder'] = '/tmp/ssa_upstream'

rch_global_dict['exclude_tests'] = []#'sm_cnahge.py', 'sm_resilience_01.py']

rch_global_dict['timeout'] = 300
rch_global_dict['exclude_nodes'] = []
rch_global_dict['nodes'] = []
rch_global_dict['covfile'] = None
rch_global_dict['attachments'] = []
rch_global_dict['check_coverage'] = False
rch_global_dict['coverage_output'] = 'NA'
rch_global_dict['hostname'] = commands.getoutput('hostname')
rch_global_dict['run_cli'] = ' '.join([os.path.abspath(sys.argv[0])] + sys.argv[1:])
test_status = ['PASSED', 'FAILED', 'WARN']

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-t', dest = 'topology', help = 'Provide file with SSA setup topology', metavar = 'setup_example.ini')
parser.add_option('-w', '--weekend', dest = 'weekend', help = 'Run all tests until ctrl-c is pressed', action = 'store_true')
parser.add_option('-o', '--output', dest = 'output_folder', help = 'Output folder for logs')
parser.add_option('-r', '--restart', dest = 'restart', help = 'Restart all SSA components between tests', action = 'store_true')
parser.add_option('-e', '--exclude', dest = 'exclude', help = 'Exclude tests',  metavar = 'mpi_test.py,unstable_test.py')
parser.add_option('-i', '--include', dest = 'include', help = 'Include tests',  metavar = 'mpi_test.py,unstable_test.py')
parser.add_option('-c', '--coverage', dest = 'coverage', help = 'Check coverage', action = 'store_true')
parser.add_option('-n', '--reinstall', dest = 'reinstall', help = 'Reinstall', action = 'store_true')
parser.add_option('-m', '--mailto', dest = 'email', help = 'A list of emails')
parser.add_option('-s', '--sources', dest = 'ssa_sources', help = 'Folder with SSA sources', metavar = 'default is upstream')
parser.add_option('-g', '--mem_check', dest = 'mem_check_methode', help = 'Run with valgrind or helgrind', metavar = 'valgrind|helgrind|leakcheck')

status = 0
(options, _) = parser.parse_args()
if not options.topology:
    parser.print_help()
    sys.exit(1)
else:
    rch_global_dict['topology'] = options.topology
    for line in open(rch_global_dict['topology'], 'r'):
        if line.startswith('#'):
            continue
        try:
            rch_global_dict['nodes'] = rch_global_dict['nodes'] + line.split()[1].split(',')
        except:
            pass
    rch_global_dict['nodes'] = ','.join(rch_global_dict['nodes'])
 

if not options.output_folder:
    rch_global_dict['output_folder'] = "%s/%s" % (ssa_tools_utils.NFS_LOGS_DIR, time.strftime("%Y%m%d_%H%M"))
else:
    rch_global_dict['output_folder'] = options.output_folder

try:
    os.mkdir(rch_global_dict['output_folder'])
except Exception as e:
    print e
    print '!!! %s folder will be deleted on successful run' % rch_global_dict['output_folder']
    sys.exit(1)

if options.mem_check_methode:
    #ugly workaround
    os.system("sed -i 's/MEMCHECK = None/MEMCHECK = \"%s\"/g' %s" % (options.mem_check_methode.upper(), '%s/ssa_tools_utils.py' % ssa_tools_utils.SSA_HOME)) 
    rch_global_dict['memcheck_folder'] = '%s/%s' % (rch_global_dict['output_folder'], options.mem_check_methode)
    os.mkdir(rch_global_dict['memcheck_folder'])

if options.mem_check_methode and options.coverage:
    print 'Cannot run mem check and coverage at the same time'
    sys.exit(1)


def setup(topology, action = 'status'):
    log_file = '%s/maintain_%s.log' % (rch_global_dict['output_folder'], time.strftime("%Y%m%d_%H%M"))
    print '%s/maintain.py -t %s --setup %s > %s' % (ssa_tools_utils.SSA_HOME, topology, action, log_file)
    os.system('%s/maintain.py -t %s --setup %s > %s' % (ssa_tools_utils.SSA_HOME, topology, action, log_file))
    return log_file




def send_email(status, mails = rch_global_dict['email_recv']):
    email_body = '/tmp/domovoi_email.txt'
    subject = "'SSA Report %s %s regression results'" % (time.strftime("%Y%m%d_%H%M"), test_status[status]) 
    f = open(email_body, 'w')

    f.write('\n\n  O my Dear Lord,\n  I hope you are having a good time, while I am running some SSA tests for you.\n')

    if status > 0:
        f.write('  Unfortunatly, they are not all passed this time. So you have some work to do :(\n\n')
    else:
        f.write('  Fortunatly, they are all passed this time, so you will need to find something else to do.\n\n')

    f.write('\n\n\tCLI:   \t  %s# %s\n\n' % (rch_global_dict['hostname'], rch_global_dict['run_cli']))
    f.write('\n\tSETUP: \t%s\n%s\n\n' % ( os.path.abspath(rch_global_dict['topology']), rch_global_dict['ssa_setup'] ))
    f.write('\n\tREPORT:\n\n')
    for k,v in gDictParams.iteritems():
        f.write("\t%s\t\t%s\n" % (k.ljust(20), '\t\t'.join(v)))

    if rch_global_dict['check_coverage']:
        f.write('\t%s\t\t%s\t%s\n' % ('coverage report'.ljust(20), rch_global_dict['coverage_output'].ljust(20),
            '/.autodirect/app/bullseye/bin/CoverageBrowser %s' % rch_global_dict['covfile']))

    f.write('\n\n\tAll files are zipped under %s.zip' %  rch_global_dict['output_folder'])
    f.write('\n\tSee my work plan for this week at root@%s# crontab -l\n' % rch_global_dict['hostname'])

    #Get random Joke
    req = urllib2.Request("http://api.icndb.com/jokes/random")
    full_json = urllib2.urlopen(req).read()
    full = json.loads(full_json)

    f.write('\n\n\n    Sincerely, yours\n    Domovoi of %s\n' % rch_global_dict['hostname'])
    f.write('\n   "%s"\n\n' % full['value']['joke'])
    f.close()

    attach = " "
    if len(rch_global_dict['attachments']) > 0:
        attach = '-a %s' % ' -a '.join(rch_global_dict['attachments'])
    cmd = 'sudo -u %s mutt -s %s -c %s %s < %s' % ( rch_global_dict['email_sender'], subject, mails, attach, email_body)
    print cmd
    commands.getoutput(cmd) 
    time.sleep(10)
    os.remove(email_body)
    return 0




#Update test list
tests = []
if not options.include:
    for t in os.listdir(os.path.dirname(os.path.abspath( __file__ ))):
        if t.endswith('_test.py'):
            tests.append(t)
    #Exclude tests
    if options.exclude:
        rch_global_dict['exclude_tests'].append(options.exclude.split(','))
else:
    tests = options.include.split(',')


if options.reinstall:
    sources = " "
    if options.ssa_sources:
        sources = "%s %s" % (options.ssa_sources, rch_global_dict['scretch_folder'])
    coverage = " "
    if options.coverage:
        coverage = "export COVERAGE=1"
    else:
        coverage = "export COVERAGE=0"
    print "%s; sudo -E %s/ssa_install.sh %s" % (coverage, ssa_tools_utils.SSA_HOME, sources)
    ssa_tools_utils.pdsh_run(rch_global_dict['nodes'], '%s; sudo -E %s/ssa_install.sh %s' % (coverage, ssa_tools_utils.SSA_HOME, sources))
    setup(rch_global_dict['topology'], 'start')

gDictParams = {}

#Check and save setup
ssa_setup = open(setup(rch_global_dict['topology'], 'status'), 'r').readlines()
#get everything from check_setup
rch_global_dict['ssa_setup'] = ''.join(ssa_setup[ssa_setup.index('*************  check_setup ********************\n'):])
if not options.restart:
    for i in ssa_setup:
        if i.find('STOPPED') >= 0:
            print i.rstrip('\n')
            status = 1
    if status:
        print 'Not all nodes are running'
        sys.exit(1)


#run static code analizer
if options.coverage:
    test = 'static_code_test.sh'
    logfile = '%s/%s_%s.log' % ( rch_global_dict['output_folder'],  time.strftime("%Y%m%d_%H%M"), test.rstrip('.sh'))
    cmd = "%s/%s 2>&1|tee > %s;sync" % ( os.path.dirname(os.path.abspath( __file__ )), test, logfile)
    print 'Running %s#%s' % (cmd, os.getcwd())
    gDictParams[test] = ['WARN']
    gDictParams[test].append(logfile)


while ( 1 ):
    print 'About to run following tests:\n%s' % tests
    for test in tests:
        test_name = test.rstrip('.py')
        if options.restart:
            print 'Restarting SSA components'
            setup(rch_global_dict['topology'], 'clean')
            setup(rch_global_dict['topology'], 'start')

        print "Starting %s" % test
        logfile = '%s/%s_%s.log' % ( rch_global_dict['output_folder'],  time.strftime("%Y%m%d_%H%M"), test_name)
        cmd = "%s/%s -t %s 2>&1|tee > %s;sync" % ( os.path.dirname(os.path.abspath( __file__ )), test, rch_global_dict['topology'], logfile)
        print 'Running test:%s' % cmd
        o = commands.getoutput(cmd)
        time.sleep(30)
        lines = open(logfile, 'r').readlines()[-1]
        if lines.find('PASSED') >= 0:
            gDictParams[test] = ['PASSED']
        else:
            gDictParams[test] = ['FAILED']
            status = 1
            if DEBUG:
                gDictParams[test].append(logfile)
                break

        if options.mem_check_methode:
            valg_dir = '%s/%s_%s' % (rch_global_dict['memcheck_folder'], time.strftime("%Y%m%d_%H%M"), test_name)
            os.mkdir(valg_dir)
            ssa_tools_utils.pdsh_run(rch_global_dict['nodes'],'cd /var/log/; s=`ls *.log.valgrind`; n=`basename ${s}`_`hostname`;cp $s %s/$n' % valg_dir)
            print 'cd /var/log/; s=`ls *.log.valgrind`; n=`basename ${s}`_`hostname`;cp $s %s/$n' % valg_dir
            gDictParams['%s test' % options.mem_check_methode] = ['WARN', valg_dir]

        gDictParams[test].append(logfile)
        print "Finished %s. See %s" % ( test, logfile)
        
    if options.weekend:
        print "Press ctrl-c to stop"
        try:
            time.sleep(10)
            
        except KeyboardInterrupt:
            print "Finished weekend run"                   
            break
    else:
        break


if options.coverage:
    rch_global_dict['check_coverage'] = True
    coverage_dir = '%s/coverage' % rch_global_dict['output_folder']
    os.mkdir(coverage_dir)
    os.system('chmod 777 %s' % coverage_dir)
    rch_global_dict['covfile'] = '%s/merged_coverage.cov' % coverage_dir
    ssa_tools_utils.pdsh_run(rch_global_dict['nodes'], 'cp /tmp/*.cov %s' % coverage_dir)
    o = commands.getoutput('mv `find %s -name \*.cov` %s' % ( rch_global_dict['output_folder'], coverage_dir))
    if o.find('missing destination') >= 0:
        print 'ERROR: %s' % o
        status = 1
    else:
        o1 = commands.getoutput('/.autodirect/app/bullseye/bin/covmerge -c -f%s %s/*' % (rch_global_dict['covfile'], coverage_dir))
        commands.getoutput('/.autodirect/app/bullseye/bin/covselect -i %s %s' % (rch_global_dict['coverage_exclude'], rch_global_dict['covfile']))
        print 'See coverage report by /.autodirect/app/bullseye/bin/CoverageBrowser %s' % rch_global_dict['covfile']
        cwd = os.getcwd()
        os.chdir(coverage_dir)
        cmd = "/.autodirect/app/bullseye/bin/covdir -f %s 2>&1|tee|grep Total |awk '{print $6}'" % rch_global_dict['covfile']
        print 'Checking coverage report %s' % cmd
        rch_global_dict['coverage_output'] = commands.getoutput(cmd)
        print 'Checking Coverage:\n%s' % "/.autodirect/app/bullseye/bin/covdir -f %s" % rch_global_dict['covfile']
        os.chdir(cwd)

#ugly workaround
if options.mem_check_methode:
    os.system("sed -i 's/MEMCHECK = \"%s\"/MEMCHECK = None/g' %s" % (options.mem_check_methode.upper(), '%s/ssa_tools_utils.py' % ssa_tools_utils.SSA_HOME))
   

commands.getoutput('sudo -u %s zip %s.zip -r %s >/dev/null' % (rch_global_dict['email_sender'], 
                    rch_global_dict['output_folder'], rch_global_dict['output_folder']))

if options.email:
    send_email(status, options.email)
else:
    send_email(status)

pprint(gDictParams)

if status == 0:
    print 'All Tests logs saved under %s.zip' %  rch_global_dict['output_folder']
    commands.getoutput('rm -rf %s' % rch_global_dict['output_folder'])
else:
    print 'All Tests logs saved under %s' %  rch_global_dict['output_folder']
sys.exit(status)

