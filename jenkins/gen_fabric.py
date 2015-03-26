#!/usr/bin/python -tt
# Copyright (C) Mellanox Technologies Ltd. 2015.  ALL RIGHTS RESERVED.
# This software product is a proprietary product of Mellanox Technologies Ltd.
# (the "Company") and all right, title, and interest in and to the
# software product, including all associated intellectual property rights,
# are and shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.

###############################################################################
#                                                                             #
#        SSA fabric generating script	                                      #
#                                                                             #
#        Author: Ilya Nelkenbaum <ilyan@mellanox.com>                         #
#                                                                             #
###############################################################################

import os
import sys
import random
import optparse

input_file	= ''
output_file	= ''
output_dir	= './'

nodes		= 0
core_num	= 1
distrib_num	= 1
access_num	= 1
acm_num		= 0

core_label	= 'core_nodes'
distrib_label	= 'distrib_nodes'
access_label	= 'access_nodes'
acm_label	= 'acm_nodes'

def save_dict (dict, file):

	f = open(file, 'w')
	f.write(core_label	+ ' ' + dict[core_label] + '\n')
	f.write(distrib_label	+ ' ' + dict[distrib_label] + '\n')
	f.write(access_label	+ ' ' + dict[access_label] + '\n')
	f.write(acm_label	+ ' ' + dict[acm_label] + '\n')
	f.close()

def generate_ini_line (dict, label, node_list):
	line_str = ''

	for elem in node_list[:-1]:
		line_str = line_str + elem + ','
	line_str = line_str + node_list[-1]

	dict[label] = line_str


def generate_fabric_dict (core_list, distrib_list, access_list, acm_list):
	ssa_fabric_dict = {}

	generate_ini_line(ssa_fabric_dict, core_label,	core_list)
	generate_ini_line(ssa_fabric_dict, distrib_label, distrib_list)
	generate_ini_line(ssa_fabric_dict, access_label, access_list)
	generate_ini_line(ssa_fabric_dict, acm_label, acm_list)

	return ssa_fabric_dict


def print_options():

	print '------------- SSA FABRIC GENERATOR OPTIONS ------------------'
	print '%-30s %s' % ('| Input file: ', input_file)
	print '%-30s %s' % ('| Output file: ', output_dir + output_file)
	print '%-30s %s' % ('| Core nodes: ', str(core_num))
	print '%-30s %s' % ('| Distribution nodes: ', str(distrib_num))
	print '%-30s %s' % ('| Access nodes: ', str(access_num))
	print '%-30s %s' % ('| ACM nodes: ', str(acm_num))
	print '%-30s %s' % ('| Total number of nodes: ', str(nodes))
	print '-------------------------------------------------------------'


def validate_options(opts, args):

	if len(args) == 0 :
		print '-E- No input file specified.',
		return 1
	elif len(args) != 1 :
		print '-E- Wrong number of arguments specified.',
		return 1
	else :
		if not os.path.isfile(args[0]) :
			print '-E- Input file specified doesn\'t exist.',
			return 1

	if (opts.output_dir) :
		if not os.path.isdir(opts.output_dir) :
			print '-E- Output directory specified doesn\'t exist.',
			return 1

	return 0

def handle_options(parser):

	global input_file
	global output_dir
	global core_num
	global distrib_num
	global access_num

	(opts, args) = parser.parse_args()

	if validate_options(opts, args) :
		parser.print_help()
		sys.exit(1)

	if (opts.core_num) :
		core_num = int(opts.core_num)

	if (opts.distrib_num) :
		distrib_num = int(opts.distrib_num)

	if (opts.access_num) :
		access_num = int(opts.access_num)

	if (opts.output_dir) :
		output_dir = opts.output_dir + '/'

	input_file = args[0]


def set_options():

	parser = optparse.OptionParser(usage = 'Usage: ./gen_fabric.py [options] input_nodes_file')

	parser.add_option('-o', '--output-dir',
		dest = 'output_dir', metavar = 'output directory', action = 'store',
		help = 'directory for output ini file in the following format: ssa_fabric_xxCR_xxDL_xxAL_xxACM.ini')

	parser.add_option('-c', '--core-num',
		dest = 'core_num', metavar = 'cores', action = 'store',
		help = 'number of core nodes')

	parser.add_option('-d', '--distrib-num',
		dest = 'distrib_num', metavar = 'distribs ', action = 'store',
		help = 'number of distribution nodes')

	parser.add_option('-a', '--access-num',
		dest = 'access_num', metavar = 'access nodes', action = 'store',
		help = 'number of access nodes')

	handle_options(parser)


def get_random_nodes(node_list, node_num) :
	rand_list = []

	for i in range(0, node_num) :
		elem = random.choice(node_list)
		rand_list.append(elem[:-1]) # remove EOL character
		node_list.remove(elem)

	return rand_list


def main(args):

	global output_file
	global nodes
	global acm_num

	node_list	= []
	core_list	= []
	distrib_list	= []
	access_list	= []

	set_options()
	fin = open(input_file, 'rU')
	lines = fin.readlines()
	fin.close()

	for line in lines:
		node_list.append(line)

	nodes = int(len(node_list))

	if nodes == 0 or (core_num + distrib_num + access_num) > nodes :
		print '-E- Wrong number of nodes specified (' + \
		      'core: ' + str(core_num) + \
		      ', distrib: ' + str(distrib_num) + \
		      ', access: ' + str(access_num) + ').' + \
		      ' Total number of nodes: ' + str(nodes) + '.',
		sys.exit(1)

	acm_num = nodes - (core_num + distrib_num + access_num)

	output_file = 'ssa_fabric_' + \
		       str(core_num) + 'CR_' + \
		       str(distrib_num) + 'DL_' + \
		       str(access_num) + 'AL_' + \
		       str(acm_num) + 'ACM.ini'

	print_options()

	node_list_copy	= list(node_list)

	core_list	= get_random_nodes(node_list_copy, core_num)
	distrib_list	= get_random_nodes(node_list_copy, distrib_num)
	access_list	= get_random_nodes(node_list_copy, access_num)
	acm_list	= get_random_nodes(node_list_copy, acm_num)

	fabric_dict = generate_fabric_dict(core_list, distrib_list, access_list, acm_list)
	save_dict(fabric_dict, output_dir + output_file)


# This is the standard boilerplate that calls the main() function
if __name__ == '__main__':
	main(sys.argv[1:])
