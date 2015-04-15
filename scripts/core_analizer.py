#!/usr/local/bin/python
import commands
import sys
import time
import os
import commands
import datetime
from optparse import OptionParser

MAILTO = 'null@mellanox.com'
TOPO = None
ARCHIVE = '/proj/SSA/Mellanox/logs'
NFS_TMP = '%s/../tmp/' % ARCHIVE
OPENSMNODE = 'ko0003'

def send_mail(subject = 'SSA Report', mailto = MAILTO, body = '/dev/null'):
#    sendmail -v lennyb@mellanox.com < update_sources.sh
    cmd = '/usr/sbin/sendmail -v %s < %s' % ( mailto, body)
    o = commands.getoutput(cmd)   
    print "%s\n%s" % (cmd, o)
    return 0


def main():
    try:
        core_pattern = commands.getoutput('cat /etc/sysctl.conf|grep kernel.core_pattern').split('=')[1].split('.')
    except:
        core_pattern = 'kernel.core_pattern=/proj/SSA/Mellanox/corefiles/core.%e.%p.%h.%t'.split('=')[1].split('.')
    cores = commands.getoutput('ls %s*|grep -v tgz' % core_pattern[0])
    
    parser = OptionParser()
    parser.add_option('-t', dest = 'topology', help = 'Provide file with SSA setup topology', metavar = 'setup_example.ini')    
    (options, _) = parser.parse_args()
    
    if not options.topology:
        print 'Please provide topo file'
        return 1
    TOPO = options.topology
    print cores 
    for core in cores.split():
        l = core.split('.')[1:-1]
        if len(l) == 0:
            break
        proc = l[0]
        host = '.'.join(l[2:])
        short_hostname = l[2]

        (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime) = os.stat(core)
        core_date = str(datetime.datetime.strptime(time.ctime(mtime), "%a %b %d %H:%M:%S %Y")).replace(' ','_').replace('-','').replace(':','')
        if time.time() - mtime < 120:
            return 0
        cdir = '%s/SEGV_%s_%s_%s' % ( NFS_TMP, core_date, short_hostname, proc)
        for cmd in ['mkdir %s' % cdir, 'scp %s:/usr/local/sbin/%s %s' % ( host, proc, cdir)]:
            o = commands.getoutput(cmd)
#            print '%s\n%s' % ( cmd, o)

        tmp_cdir = '%s/%s' % ( NFS_TMP, os.path.basename(cdir))
        _ = commands.getoutput('mkdir %s' % tmp_cdir)
 
        #Get BT
        f = open('%s/bt.log' % cdir, 'w')
        bts = commands.getoutput("ssh %s 'sudo gdb --batch --quiet -ex \"bt\" -ex \"quit\" %s %s |grep -v New'" % ( host, proc, core))
        print "ssh %s 'sudo gdb --batch --quiet -ex \"bt\" -ex \"quit\" %s %s |grep -v New'" % ( host, proc, core)
        f.write('\n\n****************** Short back trace ********************\n\n\n')
        f.write(bts)
        f.write('\n\n****************** Short back trace ********************\n\n\n')
        btf = commands.getoutput("ssh %s 'sudo gdb --batch --quiet -ex \"thread apply all bt full\" -ex \"quit\" %s %s '" % ( host, proc, core))
        print "ssh %s 'sudo gdb --batch --quiet -ex \"thread apply all bt full\" -ex \"quit\" %s %s '" % ( host, proc, core)
        f.write(btf)
        f.write('\n\n*****************************************\n\n\n')
        f.close()

        #Get logs
        o = commands.getoutput('ssh %s "python %s/logcollector.py -t %s -c -o %s > %s/logcollector.log"' % (OPENSMNODE, os.path.dirname(os.path.abspath( __file__ )), TOPO, tmp_cdir, tmp_cdir))
#        os.system('cp -r %s %s' % (tmp_cdir, cdir))
        print 'ssh %s "python %s/logcollector.py -t %s -c -o %s > %s/logcollector.log"' % (OPENSMNODE, os.path.dirname(os.path.abspath( __file__ )), TOPO, tmp_cdir, tmp_cdir)
        o = commands.getoutput('mv %s %s' % (core, cdir))
        archive_name = '%s/%s.tgz' % ( ARCHIVE, os.path.basename(cdir))

        #Prepare email
        mailbody = '%s/mail.txt' % cdir
        f = open(mailbody, 'w')
        f.write('Hi, unfortunately I\'ve noticed a new failure on %s machine,\n please take a look.\n\n' % host)
        f.write('Date:%s\n\n' % core_date)
        f.write('Host: %s\n\n' % host)
        f.write('Proc: %s\n\n' % proc)
        f.write('Logs: %s\n\n' % archive_name )
        f.write("BT:\n****************** Short back trace ********************\n\n\n")
        f.write(bts)
        f.write("\n\n\n****************** Full back trace ********************\n\n\n")
        f.write(btf)
        f.write('\n\n*****************************************\n')
        f.write('\n\n*****************************************\n')
        f.write('\n\n*****************************************\n')
        f.write("\n\n\n****************** RM issue template********************\n\n\n")
        f.write('Description:\n<pre>\n\n\n</pre>\n')
        f.write('Date:\n<pre>\n%s\n</pre>\n' % core_date)
        f.write('Host:\n<pre>\n%s\n</pre>\n' % host)
        f.write('Topology:\n<pre>\n%s\n</pre>\n' % TOPO)
        f.write('Proc:\n<pre>\n%s\n</pre>\n' % proc)
        f.write('Logs:\n<pre>\n%s\n</pre>\n' % archive_name )
        f.write('BT:\n<pre>\n%s\n</pre>\n' % bts)
        f.write('\n\n*****************************************\n')
        f.close()

        #Archive
        pwd = os.getcwd()
        os.chdir(cdir)
        #o = commands.getoutput('zip -r %s * > /dev/null' % archive_name)
        o = commands.getoutput('tar -zcf %s * > /dev/null' % archive_name)
        print '%s#tar -zcf %s *\n%s' % (pwd, archive_name, o)
        os.chdir(pwd)
        subject = 'SSA[%s]: Failed %s ' % (core_date, proc)
        
        send_mail(subject = subject, body = mailbody)
        commands.getoutput('rm -rf %s %s ' % (cdir, tmp_cdir))
        commands.getoutput('mv %s %s' % (core, NFS_TMP))
        print 'Archive saved in %s' % archive_name
        return 0
    return 0 




if __name__ == '__main__':
    sys.exit(main())



