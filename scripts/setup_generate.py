#!/usr/local/bin/python
import sys
import commands

project_name = 'ssauniversal'
core_node = 'ko0003'
DL_nodes_num = 2 
AL_nodes_num = 4 
ACM_nodes_num = None
'''
o = commands.getoutput('hostname')
if o != 'ko-ops.nmc-probe.org':
    print 'Please run this script from the headnode ko-ops.nmc-probe.org only'
    sys.exit(1)

print 'Please wait for getting %s nodes' % project_name

o = commands.getoutput('node_list -e ssa,ssauniversal')

nodes = sorted(o.split())
'''

nodes = 'ko0003,ko0004,ko0006,ko0007,ko0014,ko0015,ko0026,ko0029,ko0031,ko0034,ko0035,ko0038,ko0040,ko0043,ko0047,ko0050,ko0060,ko0065,ko0066,ko0087,ko0088,ko0090,ko0104,ko0105,ko0117,ko0120,ko0124,ko0137,ko0145,ko0155,ko0159,ko0164,ko0165,ko0168,ko0172,ko0184,ko0188,ko0190,ko0196,ko0199,ko0212,ko0219,ko0227,ko0228,ko0235,ko0236,ko0239,ko0245,ko0251,ko0255,ko0259,ko0265,ko0271,ko0277,ko0281,ko0293,ko0294,ko0300,ko0307,ko0310,ko0314,ko0318,ko0321,ko0322,ko0324,ko0329,ko0331,ko0332,ko0337,ko0340,ko0343,ko0348,ko0349,ko0360,ko0362,ko0365,ko0367,ko0373,ko0378,ko0379,ko0383,ko0389,ko0391,ko0403,ko0412,ko0426,ko0444,ko0454,ko0458,ko0462,ko0465,ko0468,ko0469,ko0473,ko0474,ko0481,ko0482,ko0483,ko0490,ko0491'.split(',')

nodes.remove(core_node)

if not ACM_nodes_num:
    ACM_nodes_num = len(nodes) - AL_nodes_num - DL_nodes_num - 1
elif not AL_nodes_num:   
    AL_nodes_num = len(nodes) - DL_nodes_num - ACM_nodes_num - 1
elif not DL_nodes_num:
    DL_nodes_num = len(nodes) - AL_nodes_num - ACM_nodes_num - 1

ini = '/proj/SSA/Mellanox/setups/DL%d_AL%d_ACM%d.ini' % ( DL_nodes_num,AL_nodes_num,ACM_nodes_num)
f = open(ini, 'w')
f.write('core_nodes %s\n' % core_node)
f.write('distrib_nodes %s\n' % ','.join(nodes[0:DL_nodes_num]))
f.write('access_nodes %s\n' % ','.join(nodes[DL_nodes_num:(DL_nodes_num+AL_nodes_num)]))
f.write('acm_nodes %s\n' %  ','.join(nodes[(DL_nodes_num + AL_nodes_num):-1]))
f.close()
print '%s is generated' % ini
print '#/proj/SSA/Mellanox/ssa_tools/maintain.py -t %s --setup start' % ini
