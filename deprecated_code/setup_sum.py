#!/usr/bin/python

import ssa_tools_utils
import sys
import time
import commands
from pprint import pprint

nodes = ['ko0003','ko0006','ko0011','ko0013','ko0018','ko0026','ko0027','ko0028','ko0031','ko0033','ko0034','ko0036','ko0040','ko0043','ko0048','ko0050','ko0051','ko0053','ko0055','ko0057','ko0059','ko0060','ko0061','ko0063','ko0067','ko0069','ko0070','ko0074','ko0076','ko0079','ko0080','ko0082','ko0085','ko0087','ko0088','ko0090','ko0096','ko0098','ko0099','ko0101','ko0103','ko0107','ko0111','ko0114','ko0116','ko0125','ko0128','ko0129','ko0134','ko0141','ko0144','ko0145','ko0148','ko0149','ko0150','ko0152','ko0154','ko0156','ko0157','ko0158','ko0162','ko0164','ko0166','ko0168','ko0170','ko0174','ko0178','ko0181','ko0185','ko0190','ko0192','ko0195','ko0197','ko0200','ko0203','ko0205','ko0207','ko0209','ko0210','ko0211','ko0213','ko0214','ko0217','ko0218','ko0223','ko0228','ko0229','ko0231','ko0235','ko0237','ko0239','ko0242','ko0249','ko0250','ko0252','ko0253','ko0255','ko0258','ko0261','ko0265','ko0268','ko0272','ko0274','ko0275','ko0277','ko0278','ko0281','ko0282','ko0283','ko0285','ko0286','ko0288','ko0289','ko0291','ko0294','ko0295','ko0297','ko0298','ko0300','ko0302','ko0304','ko0305','ko0306','ko0307','ko0309','ko0315','ko0319','ko0320','ko0322','ko0323','ko0324','ko0327','ko0328','ko0331','ko0332','ko0333','ko0335','ko0337','ko0339','ko0347','ko0351','ko0355','ko0357','ko0358','ko0359','ko0362','ko0364','ko0365','ko0366','ko0367','ko0368','ko0369','ko0370','ko0371','ko0373','ko0379','ko0380','ko0382','ko0383','ko0387','ko0392','ko0395','ko0397','ko0399','ko0402','ko0406','ko0411','ko0413','ko0419','ko0422','ko0425','ko0430','ko0436','ko0440','ko0442','ko0443','ko0444','ko0445','ko0449','ko0451','ko0454','ko0458','ko0462','ko0470','ko0471','ko0474','ko0475','ko0478','ko0479','ko0482','ko0483','ko0485','ko0487','ko0489','ko0490','ko0492']

errors=[]
sum={'ko000000' : ['virtual_name', 'node_guid','sys_image_guid' ,'port_lid'] }

o = commands.getoutput('ssh lennyb@ko-ops "/proj/SSA/Mellanox/scripts/node_list -P -e ssa,ssauniversal"')
for n in o.split('\n'):
    l = n.split()
    if len(l) == 0:
        continue
    sum[l[0]] = []
    sum[l[0]].append(l[1])

for node in nodes:
    try:
            (_, o) = ssa_tools_utils.execute_on_remote("ibv_devinfo | egrep \"node_guid|sys_image_guid|port_lid\"|awk '{print $2}'", node)
            o = o.encode('ascii','ignore').rstrip('\n')
            if len(o) == 0:
                errors.append(node)
            else:
                sum[node].append(o.split('\n'))
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
#        line="30 * * * * rsync -az /proj/SSA/Mellanox/sources /home"
#        (rc, o) = ssa_tools_utils.execute_on_remote('echo "%s" | crontab -' % line, node)

#ssa_tools_utils.rm_exec('/proj/SSA/Mellanox/ssa_tools/ssa_install.sh ssa_install', nodes)


pprint(sum)
if len(errors) >= 0:
    print 'Failed on ', errors

