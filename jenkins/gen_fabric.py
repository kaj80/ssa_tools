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

type_list	= [ 'CORE', 'DISTRIB', 'ACCESS', 'ACM' ]

label_dict	= {
		    'CORE' : 'core_nodes',
		    'DISTRIB' : 'distrib_nodes',
		    'ACCESS' : 'access_nodes',
		    'ACM' : 'acm_nodes'
		  }

label_list	= [ 'SSA', 'UPSTR', 'MOFED' ]
label		= 'SSA'

def print_options():

	print '------------- SSA FABRIC GENERATOR OPTIONS ------------------'
	print '%-30s %s' % ('| Input file: ', input_file)
	print '%-30s %s' % ('| Output file: ', output_dir + output_file)
	print '%-30s %s' % ('| Nodes label: ', label)
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

	if (opts.label) :
		if not opts.label in label_list :
			print '-E- Wrong node label specified.'
			print '-E- It should be one of the following: ' + str(label_list) + '\n'
			return 1

	return 0

def handle_options(parser):

	global input_file
	global output_dir
	global label
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

	if (opts.label) :
		label = opts.label

	input_file = args[0]


def set_options():

	parser = optparse.OptionParser(usage = 'Usage: ./gen_fabric.py [options] input_nodes_file')

	parser.add_option('-o', '--output-dir',
		dest = 'output_dir', metavar = 'output directory', action = 'store',
		help = 'directory for output ini file in the following format: ssa_fabric_xxCR_xxDL_xxAL_xxACM.ini')

	parser.add_option('-l', '--label',
		dest = 'label', metavar = 'nodes label', action = 'store',
		help = 'label of the nodes that should be used (SSA [default] / UPSTR / MOFED)')

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


def generate_ini_line (dict, type, label, node_list):
	line_str = ''

	for elem in node_list[:-1]:
		line_str = line_str + elem + ','
	line_str = line_str + node_list[-1]

	dict[type] = line_str


def fabric_to_ini (fabric_dict):
	fabric_ini = {}

	for type in type_list :
		generate_ini_line(fabric_ini, type, label_dict[type], fabric_dict[type])

	return fabric_ini


def save_dict (dict, file):
	fabric_ini_dict = fabric_to_ini(dict)

	f = open(file, 'w')
	for type in type_list :
		f.write(label_dict[type] + ' ' + fabric_ini_dict[type] + '\n')
	f.close()

	print file


def get_random_dict(node_by_type_dict, node_list, num_dict) :
	fabric_dict	= {}

	for type in type_list :
		fabric_dict[type] = []

		for i in range(0, num_dict[type]) :

			if node_by_type_dict[type] :
				elem = random.choice(node_by_type_dict[type])
			else :
				node_specific_type_set = set()
				for type_tmp in type_list :
					node_specific_type_set.update(node_by_type_dict[type_tmp])

				opt_nodes_list = list(node_specific_type_set ^ set(node_list))
				if opt_nodes_list :
					elem = random.choice(opt_nodes_list)
				else :
					elem = random.choice(list(node_specific_type_set))

			fabric_dict[type].append(elem)

			# remove element from global nodes list
			node_list.remove(elem)

			# remove element from all type specific lists
			for type_tmp in type_list :
				if elem in node_by_type_dict[type_tmp] :
					node_by_type_dict[type_tmp].remove(elem)

	return fabric_dict


def main(args):

	global output_file
	global nodes
	global acm_num

	node_by_type_dict	= {}
	num_dict		= {}
	fabric_dict		= {}
	node_list		= []

	for type in type_list :
		node_by_type_dict[type]		= []
		fabric_dict[type]		= []
		num_dict[type]			= 0

	set_options()
	fin = open(input_file, 'rU')
	lines = fin.readlines()
	fin.close()

	for line in lines:
		node_name	= ''
		llist		= []
		tlist		= []

		str_list	= line.split()
		node_name	= str_list[0]

		for str_tmp in str_list[1:] :
			if str_tmp in label_list :
				llist.append(str_tmp)

		for str_tmp in str_list[1:] :
			if str_tmp in type_list :
				tlist.append(str_tmp)

		if llist and not label in llist :
			continue

		node_name = str_list[0]

		node_list.append(node_name)
		for type in tlist :
			node_by_type_dict[type].append(node_name)

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

	#print_options()

	node_list_copy		= list(node_list)

	num_dict['CORE']	= core_num
	num_dict['DISTRIB']	= distrib_num
	num_dict['ACCESS']	= access_num
	num_dict['ACM']		= acm_num

	fabric_dict	= get_random_dict(node_by_type_dict, node_list_copy, num_dict)

	save_dict(fabric_dict, output_dir + output_file)


# This is the standard boilerplate that calls the main() function
if __name__ == '__main__':
	main(sys.argv[1:])
