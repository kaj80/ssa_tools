#!/usr/bin/python

# This script is meant to drastically increase the size
# of the ibssa_hosts.data file preloaded by the core
# it's input is the number of addresses to add
# it outputs that many IPv4 addresses and that many IPv6 addresses
# and the expected size of this addresses

import sys
import time

GID = 'fe80::2:c902:26:31d9'
QP = '0x000048'
flags = '0x80'

ipv4_arr=[2,0]
ipv6_arr=[1,0]

def inc_ipv4_arr(): # needs to be changed if we want input larger than 65023

	if ipv4_arr[1] == 255:
		ipv4_arr[0] += 1
		ipv4_arr[1] = 0
	else:
		ipv4_arr[1] +=1

def ipv6_arr_str():

	arr_len = len(ipv6_arr)
	res = ''
	for i in range(arr_len -1):
		res += format(ipv6_arr[i], '04x') + ':'
	res += format(ipv6_arr[arr_len -1], '04x')
	return res

def inc_ipv6_arr():

	arr_len = len(ipv6_arr)
	for i in reversed(range(arr_len)):
		if ipv6_arr[i] != 65535: # currently impossible because of main
			ipv6_arr[i] += 1
			return
		ipv6_arr[i]=0
		if i == 0:
			ipv6_arr.insert(0,1)

def main (argv):

	time_str = time.strftime("%H:%M:%S %d %b %Y")

	num = int(argv[0])
	if num > 65024:
		print 'ERROR: size is to large.\ninput must be smaller than 65025\n'
		return
	size = (float(num * 72)) / 1024
	print ('# %d additional lines added by preload_file_padder.py on ' \
		% num + time_str)
	print '# The size of an IPv4 record is 32 bytes'
	print '# The size of an IPv6 record is 40 bytes'
	print '# Expected total size of additional addresses is %.3fKB' % size

	for i in range(num):
		ipv4_addr = '100.0.' + str(ipv4_arr[0]) + '.' + str(ipv4_arr[1])
		print '%-30s %s\t\t%s\t%s' % (ipv4_addr, GID, QP, flags)
		inc_ipv4_arr()

		ipv6_addr = 'fec0::' + ipv6_arr_str()
		print '%-30s %s\t\t%s\t%s' % (ipv6_addr, GID, QP, flags)
		inc_ipv6_arr()
	print ('# end of additional lines added by preload_file_padder.py on ' \
		+ time_str)
	return

if __name__ == "__main__":
        main(sys.argv[1:])
