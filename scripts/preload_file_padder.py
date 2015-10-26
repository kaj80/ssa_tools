#!/usr/bin/python

# This script is meant to increase the size
# of the ibssa_hosts.data file preloaded by the core
# it outputs an equal amount IPv4 addresses and IPv6 addresses
# and the expected size of this addresses

import sys
import time
from optparse import OptionParser

GID = 'fe80::2:c902:26:31d9'
QP = '0x000048'
flags = '0x80'
ipv4_prefix = '100.'
ipv6_prefix_num = 65216 # 'fec0' in decimal
print_msg = '# The size of an IPv4 record is 32 bytes\n# The size of an IPv6 record is 40 bytes'
amount = None

ipv4_arr=[0,2,0]
ipv6_arr=[1,0]

def parse_opts():

	global GID
	global QP
	global flags
	global ipv4_prefix
	global ipv6_prefix_num
	global amount

	parser = OptionParser()

	parser.add_option('-g','--gid', dest ='GID', \
			  help = ('Provide GID to be used for output ' \
				+ 'preload file entries'))

	parser.add_option('--qp', dest = 'QP', \
			  help = ('provide QP to be used for '\
				 + 'output preload file entries'))

	parser.add_option('-f', '--flags', dest = 'flags', \
			 help = ('provide flags to be used ' \
				+ 'for output preload file entries'))

	parser.add_option('--ipv4_prefix', dest = 'ipv4_prefix', \
			  help = ('provide a prefix for the ouput IPv4 addresses.\n' + \
				'must be of the format \'x.\' where 0 <= x <= 255'))

	parser.add_option('--ipv6_prefix', dest = 'ipv6_prefix', \
			  help = ('provide a prefix for the output IPv6 addresses.\n' + \
				'must be an INTEGER 0 <= <input> <= 65535 representing' + \
				'first 4 hexadecimal digits of the addressed'))

	parser.add_option('-a', '--amount', type = 'int', dest = 'amount', \
			  help = 'provide desired amount of IPv4 and IPv6 addresses')

	(options, _) = parser.parse_args()

	if options.amount == None:
		print 'ERROR: desired amount of addresses must be given.' \
			+ ' use \'-a <desired amount>\''
		return False
	amount = options.amount
	if amount > 16776704:
		print 'ERROR: size is to large.\ninput must be smaller than 16776705\n'
		return False


	if options.ipv4_prefix != None:
		if check_ipv4_prefix(options.ipv4_prefix):
			ipv4_prefix = options.ipv4_prefix
		else:
			print 'ERROR: IPv4 prefix must be of the format' \
				+ ' \'x.\' where 0 <= x <= 255'
			return False

	if options.ipv6_prefix != None:
		if check_ipv6_prefix(options.ipv6_prefix):
			ipv6_prefix_num = int(options.ipv6_prefix)
		else:
			print 'ERROR: IPv6 prefix must be an INTEGER' + \
				'0 <= <input> <= 65535'
			return False

	if options.GID != None:
		GID = options.GID
	if options.QP != None:
		QP = options.QP
	if options.flags != None:
		flags = options.flags

	return True

def check_ipv4_prefix(prefix):

	lst = prefix.split('.')
	if len(lst) != 2:
		return False
	if lst[1] != '':
		return False
	try:
		num = int(lst[0])
	except:
		return False
	if num > 255 or num < 0:
		return False
	return True

def check_ipv6_prefix(prefix):

	try:
		num = int(prefix)
		if num > 65535 or num < 0:
			return False
		return True
	except:
		return False

def inc_ipv4_arr():

	arr_len = len(ipv4_arr)
	for i in reversed(range(arr_len)):
		if ipv4_arr[i] != 255:
			ipv4_arr[i] += 1
			break
		ipv4_arr[i] = 0

def ipv6_str():

	arr_len = len(ipv6_arr)
	res = format(ipv6_prefix_num, '04x') + '::'
	for i in range(arr_len -1):
		res += format(ipv6_arr[i], '04x') + ':'
	res += format(ipv6_arr[arr_len -1], '04x')
	return res

def inc_ipv6_arr():

	arr_len = len(ipv6_arr)
	for i in reversed(range(arr_len)):
		if ipv6_arr[i] != 65535:
			ipv6_arr[i] += 1
			return
		ipv6_arr[i] = 0
		if i == 0:
			ipv6_arr.insert(0,1)

def main (argv):

	time_str = time.strftime("%H:%M:%S %d %b %Y")

	if not parse_opts():
		return

	size = (float(amount * 72)) / 1024
	print ('# %d additional lines added by preload_file_padder.py on ' \
		% amount + time_str)
	print print_msg
	print '# Expected total size of additional addresses is %.3fKB' % size

	for i in range(amount):
		ipv4_addr = ipv4_prefix + str(ipv4_arr[0]) + '.' \
			    + str(ipv4_arr[1]) + '.' + str(ipv4_arr[2])
		print '%-30s %s\t\t%s\t%s' % (ipv4_addr, GID, QP, flags)
		inc_ipv4_arr()

		ipv6_addr = ipv6_str()
		print '%-30s %s\t\t%s\t%s' % (ipv6_addr, GID, QP, flags)
		inc_ipv6_arr()
	print ('# end of additional lines added by preload_file_padder.py on ' \
		+ time_str)
	return

if __name__ == "__main__":
	main(sys.argv[1:])
