#!/usr/bin/python
import sys
import commands
#This script finds Ib Switch and re-enables it's ports'
#should be run after reinit_test.py

o = commands.getoutput ('/usr/sbin/ibnetdiscover | egrep switchguid')
print o
print o.split('=')[1].split('(')[0]
for sw in [o.split('=')[1].split('(')[0],]:
   for p in xrange(1,40):
       cmd = 'ibportstate -G %s %d enable' % ( sw, p)
       o = commands.getoutput(cmd)
       print '%s\n%s' % ( cmd, o)

