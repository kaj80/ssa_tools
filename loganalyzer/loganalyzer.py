#!/usr/bin/python -tt
# Copyright (C) Mellanox Technologies Ltd. 2014.  ALL RIGHTS RESERVED.
# This software product is a proprietary product of Mellanox Technologies Ltd.
# (the "Company") and all right, title, and interest in and to the
# software product, including all associated intellectual property rights,
# are and shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.

###############################################################################
#                                                                             #
#        SSA Log Analyzer processing script                                   #
#                                                                             #
#        Author: Ilya Nelkenbaum <ilyan@mellanox.com>                         #
#                                                                             #
###############################################################################

import os
import re
import sys
import config
import output
import optparse

from datetime import datetime

###############################################################################
# Constants                                                                   #
###############################################################################

###############################################################################
# Initializations                                                             #
###############################################################################
nlist = []
tlist = []
nelist = []

###############################################################################
# SSA Log Analyzer options parser                                             #
###############################################################################


###############################################################################
# SSA Log Analyzer processing script calls                                    #
###############################################################################

def search_and_update(rexp, str, info_obj, attr):

	res = re.search(rexp, str)
	if res:
		try:
			if type(getattr(info_obj, attr)) is list:
				if not res.group(attr) in getattr(info_obj, attr):
					getattr(info_obj, attr).append(res.group(attr))
			else:
				setattr(info_obj, attr, res.group(attr))
		except:
			print '-E search and update: ' + info_obj.__name__+ ' : ' + attr + ' doesn\'t exist'


def info_fix(info_class, ntype, ex_dict):

	for ex in ex_dict.keys():
		if ex != ntype:
			continue

		for attr in ex_dict[ex].keys():
			try:
				setattr(info_class, attr, ex_dict[ex][attr])
			except:
				print '-E info fix: ' + attr + ' doesn\'t exist'


def get_node_info(llist, ntype):

	node_info = config.la_node_info()

	for line in llist:
		for attr in config.la_node_info.attr_list:

			if config.la_config.node_info_attr[attr] == '':
				continue

			if not type(getattr(node_info, attr)) is list and getattr(node_info, attr) != '':
				continue

			search_and_update(config.la_config.node_info_attr[attr], line, node_info, attr)

	info_fix(node_info, ntype, config.la_config.node_info_exceptions)

	nlist.append(node_info)


def get_thread_info(llist, ntype):

	for thread in config.LA_THREADS_BY_NODE[ntype]:

		thread_info = config.la_thread_info()
		for line in llist:

			for attr in config.la_thread_info.attr_list:

				if attr in config.la_config.thread_info_shared_attr.keys() :

					if config.la_config.thread_info_shared_attr[attr] == '':
						continue

					reg_exp = config.la_config.thread_info_shared_attr[attr]

				elif attr == 'thread_id':

					if config.la_config.thread_info_thread_id[thread] == '':
						continue

					reg_exp = config.la_config.thread_info_thread_id[thread]

				elif attr == 'thread_type':

					thread_info.thread_type = thread
					continue

				else:

					continue

				search_and_update(reg_exp, line, thread_info, attr)

		info_fix(thread_info, ntype, config.la_config.thread_info_exceptions)

		tlist.append(thread_info)


def get_time_delta(end_time_str, start_time_str):

	start_time = datetime.strptime(start_time_str, config.LA_LOG_TIME_FORMAT)
	end_time = datetime.strptime(end_time_str, config.LA_LOG_TIME_FORMAT)

	delta_time = end_time - start_time
	delta_us = delta_time.microseconds + delta_time.seconds * 1000000

	units = config.time_units

	if units == 'us':
		delta = delta_us
	elif units == 'ms':
		delta = delta_us / 1000
	elif units == 's':
		delta = delta_us / 1000000
	elif units == 'm':
		delta = delta_us / 60000000
	else:
		delta = delta_us
		config.time_units = 'us'
		print '-W- Unknow format for time units: ' + units + ' (microsecond units will be used)'

	return delta


def get_node_event_info(llist, node, ntype):

	print '-TODO- add some ID for correlation between Start and End of the same event'

	for event in config.LA_EVENTS_BY_NODE[ntype]:

		# check if some event types were specified and perform analysis only for them
		if config.event_type_list and not event in config.event_type_list:
			continue

		rexp_start_str = config.la_config.node_event_info[event]['start']
		if rexp_start_str == '':
			continue

		rexp_end_str = config.la_config.node_event_info[event]['end']

		event_info = config.la_event_info()
		start_time = 0
		end_time = 0

		for line in llist:

			res = re.search(rexp_start_str, line)
			if res:
				start_time = res.group('start_time')
				event_info.event_cnt += 1
				continue

			if rexp_end_str == '':
				continue

			res = re.search(rexp_end_str, line)
			if res:
				end_time = res.group('end_time')
				delta = get_time_delta(end_time, start_time)
				start_time = 0

				if event_info.exec_time_max < delta:
					event_info.exec_time_max = delta

				if event_info.exec_time_min == 0 or event_info.exec_time_min > delta:
					event_info.exec_time_min = delta

				if event_info.event_cnt == 0:
					print '-E- ' + event + ' event counter is zero'
					break
				else:
					event_info.exec_time_avg = \
						(event_info.exec_time_avg * (event_info.event_cnt - 1) + delta) / event_info.event_cnt

		event_info.node_name = node
		event_info.node_type = ntype
		event_info.event_type = event
		event_info.event_cnt = str(event_info.event_cnt)
		event_info.exec_time_max = str(event_info.exec_time_max) + ' [' + config.time_units + ']'
		event_info.exec_time_min = str(event_info.exec_time_min) + ' [' + config.time_units + ']'
		event_info.exec_time_avg = str(event_info.exec_time_avg) + ' [' + config.time_units + ']'

		nelist.append(event_info)


def run_node_analyzer(in_dir):

	for ntype in config.LA_NODE_TYPES:

		# check if some node types were specified and perform analysis only for them
		if config.node_type_list and not ntype in config.node_type_list:
			continue

		ntype_dir = os.path.join(in_dir, ntype)
		if not os.path.exists(ntype_dir):
			print '-W- No log files for ' + ntype + ' nodes'
			continue

		print '-I- Analysing ' + ntype.ljust(10) + ' nodes'

		for node in os.listdir(ntype_dir):

			# check if some hosts were specified and perform analysis only for them
			if config.host_list and not node in config.host_list:
				continue

			nlog = os.path.join(ntype_dir + '/' + node, config.LA_LOGS_BY_TYPE[ntype]);
			if not os.path.exists(nlog):
				print '-E- Log file doesn\'t exist for ' + node + ' node'
				continue

			fin = open(nlog, 'rU')
			lines = fin.readlines()
			fin.close()

			# check if some analysis types were specified and perform only those types
			if not config.analysis_list:
				get_node_info(lines, ntype)
				get_thread_info(lines, ntype)
				get_node_event_info(lines, node, ntype)
			else:
				if 'node_info' in config.analysis_list:
					get_node_info(lines, ntype)
				if 'thread_info' in config.analysis_list:
					get_thread_info(lines, ntype)
				if 'node_events' in config.analysis_list:
					get_node_event_info(lines, node, ntype)


def print_options():

	print '################# SSA LOG ANALYZER OPTIONS ##################'
	print '%-30s %s' % ('# Input directory: ', config.input_dir)
	print '%-30s %s' % ('# Output directory: ', config.output_dir)
	print '%-30s %s' % ('# Analysis list: ', str(config.analysis_list))
	print '%-30s %s' % ('# Node types list: ', str(config.node_type_list))
	print '%-30s %s' % ('# Host list: ', str(config.host_list))
	print '%-30s %s' % ('# Event types list: ', str(config.event_type_list))
	print '%-30s %s' % ('# Time units: ', config.time_units)
	print '#############################################################'


def validate_options(opts, args):

	if len(args) == 1 :
		if not os.path.exists(args[0]) :
			print '-E- Input directory specified doesn\'t exist.'
			return 1
	elif len(args) > 1 :
		print '-E- Too much arguments specified'
		return 1

	if (opts.output_mode) :
		if not opts.output_mode in [ 'regular', 'csv' ] :
			print '-E- invalid output mode'
			return 1

	if (opts.atype_list) :
		for atype in opts.atype_list:
			if not atype in config.LA_ANALYSIS_TYPES :
				print '-E- invalid analysis type: ' + atype
				return 1

	if (opts.ntype_list) :
		for ntype in opts.ntype_list:
			if not ntype in config.LA_NODE_TYPES :
				print '-E- invalid node type: ' + ntype
				return 1

	print '-TODO- Add check if event is not in SSA events list as well'

	if (opts.etype_list) :
		for etype in opts.etype_list:
			if not etype in config.la_config.node_event_info.keys() :
				print '-E- invalid event type: ' + etype
				return 1

	if (opts.time_units) :
		if not opts.time_units in [ 'us', 'ms', 's', 'm' ] :
			print '-E- invalid time units'
			return 1

	return 0

def handle_options(parser):

	(opts, args) = parser.parse_args()

	if validate_options(opts, args) :
		parser.print_help()
		sys.exit(1)

	if (opts.output_mode) :
		config.output_mode = opts.output_mode

	if (opts.output_dir) :
		config.output_dir = opts.output_dir

	if (opts.atype_list) :
		config.analysis_list = opts.atype_list

	if (opts.ntype_list) :
		config.node_type_list = opts.ntype_list

	if (opts.hname_list) :
		config.host_list = opts.hname_list

	if (opts.etype_list) :
		config.event_type_list = opts.etype_list

	if (opts.time_units) :
		config.time_units = opts.time_units


def set_options():

	parser = optparse.OptionParser(usage = 'Usage: ./loganalyzer [options] input_directory')

	parser.add_option('-m', '--run-mode',
		dest = 'output_mode', metavar = '< regular | csv >', action = 'store',
		help = 'output format mode')

	parser.add_option('-o', '--output-path',
		dest = 'output_dir', metavar = '<output dir>', action = 'store',
		help = 'output directory path')

	parser.add_option('-a', '--analysis-type',
		dest = 'atype_list', metavar = '<analysis type>', action = 'append',
		help = 'analysis types to perform (' + str(config.LA_ANALYSIS_TYPES) + ')')

	parser.add_option('-t', '--node-type',
		dest = 'ntype_list', metavar = '<node type>', action = 'append',
		help = 'node types for analysis (' + str(config.LA_NODE_TYPES)  + ')')

	parser.add_option('-n', '--host-name',
		dest = 'hname_list', metavar = '<host name>', action = 'append',
		help = 'host names for analysis (multiple host names may be specified)')

	parser.add_option('-e', '--event-type',
		dest = 'etype_list', metavar = '<event type>', action = 'append',
		help = 'event types for analysis (' + str(config.la_config.node_event_info.keys())  + ')')

	parser.add_option('-u', '--time-units',
		dest = 'time_units', metavar = '<time units>', action = 'store',
		help = 'time units ([\'us\', \'ms\', \'s\', \'m\']')

	handle_options(parser)


def main(args):

	print '-TODO- add efficient reading for large logs'
	print '-TODO- add precompiled reg exps'

	set_options()

	print_options()

	run_node_analyzer(config.input_dir)

	if not os.path.exists(config.output_dir):
		print '-I- Creating new output directory: ' + config.output_dir
		os.makedirs(config.output_dir)

	output.info_dump(config.output_dir + '/node_info.txt', nlist, 'NODE INFO', config.la_node_info.attr_list)
	output.info_dump(config.output_dir + '/thread_info.txt', tlist, 'THREAD INFO', config.la_thread_info.attr_list)
	output.info_dump(config.output_dir + '/node_event_info.txt', nelist, 'NODE EVENT INFO', config.la_event_info.attr_list)

# This is the standard boilerplate that calls the main() function
if __name__ == '__main__':
	main(sys.argv[1:])

