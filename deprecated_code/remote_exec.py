#!/usr/bin/python

import ssa_tools_utils
import sys
import time

nodes = 'ko0003,ko0004,ko0006,ko0007,ko0014,ko0015,ko0026,ko0029,ko0031,ko0034,ko0035,ko0038,ko0040,ko0043,ko0047,ko0050,ko0060,ko0065,ko0066,ko0087,ko0088,ko0090,ko0104,ko0105,ko0117,ko0120,ko0124,ko0137,ko0145,ko0155,ko0159,ko0164,ko0165,ko0168,ko0172,ko0184,ko0188,ko0190,ko0196,ko0199,ko0212,ko0219,ko0227,ko0228,ko0235,ko0236,ko0239,ko0245,ko0251,ko0255,ko0259,ko0265,ko0271,ko0277,ko0281,ko0293,ko0294,ko0300,ko0307,ko0310,ko0314,ko0318,ko0321,ko0322,ko0324,ko0329,ko0331,ko0332,ko0337,ko0340,ko0343,ko0348,ko0349,ko0360,ko0362,ko0365,ko0367,ko0373,ko0378,ko0379,ko0383,ko0389,ko0391,ko0403,ko0412,ko0426,ko0444,ko0454,ko0458,ko0462,ko0465,ko0468,ko0469,ko0473,ko0474,ko0481,ko0482,ko0483,ko0490,ko0491'.split(',')

nodes = sorted(nodes)[::-1]
errors=[]
#ssa_tools_utils.rm_exec('-- sh -c "echo `hostname` mthca0 > /sys/class/infiniband/mthca0/node_desc"',nodes)
#ssa_tools_utils.rm_exec('rm -f /usr/local/lib/*ssa* /usr/local/sbin/*', nodes)

#ssa_tools_utils.rm_exec('rm -rf /home/kodiak /home/SSA ', nodes)
#ssa_tools_utils.rm_exec('/proj/SSA/Mellanox/ssa_tools/ssa_install.sh ssa_install ', nodes)

#ssa_tools_utils.rm_exec('\cp /proj/SSA/Mellanox/etc/* /usr/local/etc/rdma', nodes)
#ssa_tools_utils.rm_exec('/usr/local/sbin/ib_acme -A ', nodes)

#ssa_tools_utils.rm_exec("ibv_devinfo|grep sm_lid|awk {'print $2}'", nodes)
#ssa_tools_utils.rm_exec('sudo su -l </dev/null', nodes)

#ssa_tools_utils.rm_exec('-- sh -c "echo \'* - memlock unlimited\'>> /etc/security/limits.conf"',nodes)
#ssa_tools_utils.rm_exec('reboot', nodes)


### Update ssabedrock nodes
#line="30 * * * * (rsync -aiz /proj/SSA/Mellanox/sources /home)\n0 * * * * (mv /tmp/core.* /proj/SSA/Mellanox/corefiles)"
line="0 * * * * (mv /tmp/core.* /proj/SSA/Mellanox/corefiles)"
ssa_tools_utils.rm_exec('echo "%s" | sudo crontab -' % line, nodes)
#ssa_tools_utils.rm_exec('echo "" | sudo -u lennyb crontab -' ,  nodes)
#ssa_tools_utils.rm_exec("sed -i 's/tcsh/bash/g' /etc/passwd", nodes)
#ssa_tools_utils.rm_exec('-- sh -c "echo kernel.core_pattern=/tmp/core.%e.%p.%h.%t >> /etc/sysctl.conf"' , nodes)
#ssa_tools_utils.rm_exec('-- sh -c "echo \'StrictHostKeyChecking no\'>> /etc/ssh/ssh_config"', nodes)
#ssa_tools_utils.rm_exec('sysctl -p /etc/sysctl.conf', nodes)
sys.exit(1)


if len(sys.argv) == 2:
    print 'Execute on parallel'
    ssa_tools_utils.rm_exec(sys.argv[1:], nodes)
else:
    for node in nodes:
        try:
            (rc, o) = ssa_tools_utils.execute_on_remote('-- sh -c "echo \'StrictHostKeyChecking no\'>> /etc/ssh/ssh_config"', node)
            #(rc, o) = ssa_tools_utils.execute_on_remote('date', node)
            #(rc, o) = ssa_tools_utils.execute_on_remote(sys.argv[1:], node)
            print '[%s] %s' % (node, o)
        except:
            print 'Failed on %s' % node
            errors.append(node)

#    (rc',' out) = ssa_tools_utils.execute_on_remote('-- sh -c "echo \'ulimit -c unlimited\'>> /root/.bashrc"', node)
#    (rc',' out) = ssa_tools_utils.execute_on_remote('-- sh -c "echo \'modprobe ib_uverbs\'>> /etc/profile"'',' node)
#    (rc',' out) = ssa_tools_utils.execute_on_remote('-- sh -c "echo \'modprobe rdma_cm\'>> /etc/profile"'',' node)
#    (rc',' out) = ssa_tools_utils.execute_on_remote('-- sh -c "echo \'modprobe ib_addr\'>> /etc/profile"'',' node)
#    (rc',' out) = ssa_tools_utils.execute_on_remote('-- sh -c "echo \'modprobe rdma_ucm\'>> /etc/profile"'',' node)
#    (rc',' out) = ssa_tools_utils.execute_on_remote('-- sh -c "echo \'modprobe ib_uverbs\'>> /etc/profile"'',' node)
#    (rc',' out) = ssa_tools_utils.execute_on_remote('-- sh -c "echo `hostname` mthca0 > /sys/class/infiniband/mthca0/node_desc"'','node)
#    (rc',' out) = ssa_tools_utils.execute_on_remote('-- sh -c "echo \'echo `hostname` mthca0 > /sys/class/infiniband/mthca0/node_desc\'>>/etc/profile "'','node)
#        (rc, out) = ssa_tools_utils.execute_on_remote('cp /proj/SSA/Mellanox/ssa_libs/* /usr/local/lib/', node)
#        (rc, out) = ssa_tools_utils.execute_on_remote('/proj/SSA/Mellanox/usr//ib_acme -A -D /proj/SSA/Mellanox/etc/', node)
#        (rc, out) = ssa_tools_utils.execute_on_remote('/proj/SSA/Mellanox/usr//ib_acme -A -D //usr/local/etc/rdma/', node)
#        for cmd in ['ko-ops.kodiak.nx:/usr/home/markus /users/markus nfs defaults 0 0',
#        'ko-ops.kodiak.nx:/usr/home/ilyan  /users/ilyan nfs defaults 0 0',
#        'ko-ops.kodiak.nx:/usr/home/halr /users/halr nfs defaults 0 0',
#        'ko-ops.kodiak.nx:/proj/SSA /proj/SSA nfs defaults 0 0',
#        'ko-ops.kodiak.nx:/usr/home/sashakot  /users/sashakot nfs defaults 0 0',
#       'ko-ops.kodiak.nx:/usr/home/lennyb  /users/lennyb nfs defaults 0 0',
#        'ko-ops.kodiak.nx:/usr/testbed/share  /share nfs defaults 0 0'] :
#            (rc, out) = ssa_tools_utils.execute_on_remote('-- sh -c "echo \'%s\' >> /etc/fstab"' % cmd , node)
#            (rc, out) = ssa_tools_utils.execute_on_remote('mount -a"', node)
#        (rc, o) = ssa_tools_utils.execute_on_remote('/sbin/modprobe ib_uverbs rdma_cm ib_addr rdma_ucm ib_uverbs', node)
#        (rc, o) = ssa_tools_utils.execute_on_remote('cp /proj/SSA/Mellanox/usr/* /usr/local/sbin/', node)
#        (rc, o) = ssa_tools_utils.execute_on_remote('cp /proj/SSA/Mellanox/etc/* /usr/local/etc/rdma/', node)
#        (rc, o) = ssa_tools_utils.execute_on_remote('/usr/local/bin/ib_acme -D /usr/local/etc/rdma/ -A', node)
#        (rc, o) = ssa_tools_utils.execute_on_remote('ibstat|grep Base', node)
#        (rc, out) = ssa_tools_utils.execute_on_remote('-- sh -c "echo \'/proj/SSA/Mellanox/corefiles/core.%e.%p.%h.%t\' > /proc/sys/kernel/core_pattern"', node)
#        (rc, out) = ssa_tools_utils.execute_on_remote('-- sh -c "echo \'kernel.core_pattern=/proj/SSA/Mellanox/corefiles/core.%e.%p.%h.%t\' >> /etc/sysctl.conf "', node)

####### Crontab for lennyb 
#        line="30 * * * * (sudo chown -R $USER /home ; rsync -az /proj/SSA/Mellanox/sources /home)"
#        (rc, o) = ssa_tools_utils.execute_on_remote('echo "%s" | crontab -' % line, node)

#ssa_tools_utils.rm_exec('/proj/SSA/Mellanox/ssa_tools/ssa_install.sh ssa_install', nodes)
if len(errors) >= 0:
    print 'Failed on ', errors

