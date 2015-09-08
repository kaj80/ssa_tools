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
#        SSA Log Analyzer configuration module                                #
#                                                                             #
#        Author: Ilya Nelkenbaum <ilyan@mellanox.com>                         #
#                                                                             #
###############################################################################


###############################################################################
# Options (default values)                                                    #
###############################################################################
output_mode	= 'regular' # optional values: 'regular' / 'csv'
input_dir	= ''
output_dir	= '/tmp/la_out'
analysis_list	= []
node_type_list	= []
host_list	= []
event_type_list = []
time_units	= 'us'	# optional values: 'us' / 'ms' / 's' / 'm'

###############################################################################
# Constants                                                                   #
###############################################################################
LA_NODE_TYPES		= [ 'core', 'distrib', 'access', 'acm' ]

LA_ANALYSIS_TYPES	= [ 'node_info', 'thread_info', 'node_events', 'distrib_tree', 'ssa_events' ]

LA_LOGS_BY_TYPE		= { 'core' : 'ibssa.log', 'distrib' : 'ibssa.log',
			    'access' : 'ibssa.log', 'acm' : 'ibacm.log' }

LA_THREADS_BY_NODE	= { 'core' : ['core', 'ctrl', 'extract', 'upstream', 'downstream'],
			    'distrib' : ['distrib', 'ctrl', 'upstream', 'downstream'],
			    'access' : ['access', 'access_prdb', 'ctrl', 'upstream', 'downstream'],
			    'acm' : ['acm_server', 'ctrl', 'acm_comp', 'acm_query', 'acm_retry', 'upstream'],
			    'core_access' : ['core', 'ctrl', 'extract', 'access', 'access_prdb', 'upstream', 'downstream'],
			    'distrib_access' : ['distrib', 'ctrl', 'access', 'access_prdb', 'upstream', 'downstream'] }

LA_EVENTS_BY_NODE	= { 'core' : ['core_subnet_up', 'core_extract', 'core_comparison', 'core_send', 'core_tree_join', 'core_tree_leave' ],
			    'distrib' : ['distrib_receive', 'distrib_send' ],
			    'access' : ['access_receive', 'access_client_join', 'access_prdb_calc', 'access_prdb_send' ],
			    'acm' : ['acm_receive', 'acm_populate', 'acm_pr_resolve'] }

LA_LOG_TIME_FORMAT	= '%b %d %H:%M:%S %f'

###############################################################################
# SSA Log Analyzer classes                                                    #
###############################################################################

class la_node_info :

	attr_list = [ 'name', 'type', 'node_gid', 'port_gid', 'version', 'ip' ]

	def __init__(self):
		self.name = ''
		self.type = ''
		self.node_gid = ''
		self.port_gid = []
		self.version = ''
		self.ip = ''


class la_thread_info :

	attr_list = [ 'node_name', 'node_type', 'port_gid', 'thread_type', 'thread_id' ]

	def __init__(self):
		self.node_name = ''
		self.node_type = ''
		self.port_gid = ''
		self.thread_type = ''
		self.thread_id = ''


class la_event_info :

	attr_list = [ 'node_name', 'node_type', 'event_type', 'event_cnt', 'exec_time_max', 'exec_time_min', 'exec_time_avg' ]

	def __init__(self):
		self.node_name = ''
		self.node_type = ''
		self.event_type = ''
		self.event_cnt = 0
		self.exec_time_max = 0
		self.exec_time_min = 0
		self.exec_time_avg = 0


###############################################################################
# SSA Log Analyzer configurations                                             #
###############################################################################

class la_config :

	node_info_attr = {
			   'name' : 'host name (?P<name>.+)',
			   'type' : '_log_options: node type (?P<type>.+)',
			   'node_gid' : '', #TBD
			   'port_gid' : 'ssa_svc_join: (?P<port_name>.*) (?P<port_gid>.*:.*:.*:.*:.*:.*)',
			   'version' : 'ibssa version (?P<version>.+)',
			   'ip' : '' # TBD
			 }

	node_info_exceptions = {
				 'acm' : { 'type' : 'acm' }
			       }

	thread_info_shared_attr	= {
				    'node_name' : 'host name (?P<node_name>.+)',
				    'node_type' : '_log_options: node type (?P<node_type>.+)',
				    'port_gid' : 'ssa_svc_join: (?P<port_name>.*) (?P<port_gid>.*:.*:.*:.*:.*:.*)'
				  }

	thread_info_thread_id = {
				  'core' : '\[(?P<thread_id>.*)\]: core_construct',
				  'ctrl' : '\[(?P<thread_id>.*)\]: ssa_ctrl_run: $',
				  'extract' : '\[(?P<thread_id>.*)\].*Starting smdb extract thread',
				  'distrib' : '\[(?P<thread_id>.*)\]: distrib_construct',
				  'access' : '\[(?P<thread_id>.*)\]: ssa_access_handler: $',
				  'access_prdb' : '', # TBD
				  'upstream' : '\[(?P<thread_id>.*)\]: ssa_upstream_handler: .*',
				  'downstream' : '\[(?P<thread_id>.*)\]: ssa_downstream_handler: .*',
				  'acm_server' : '', # TBD
				  'acm_comp' : '', # TBD
				  'acm_query' : '', # TBD
				  'acm_retry' : '' # TBD
				}

	thread_info_exceptions = {
				   'acm' : { 'node_type' : 'acm' }
				 }

	node_event_info	= {
			    'core_subnet_up' :
				{
				  'start' : '(?P<start_time>.*) \[(?P<event_thread_id>.*)\]: core_report: Subnet up event',
				  'end' : ''
				},
			    'core_extract' :
				{
				  'start' : '(?P<start_time>.*) \[(?P<event_thread_id>.*)\]: ssa_db_extract: \[',
				  'end' : '(?P<end_time>.*) \[(?P<event_thread_id>).*\]: ssa_db_extract: \]'
				},
			    'core_comparison' :
				{
				  'start' : '(?P<start_time>.*) \[(?P<event_thread_id>.*)\]: ssa_db_compare: \[',
				  'end' : '(?P<end_time>.*) \[(?P<event_thread_id>.*)\]: ssa_db_compare: \]'
				},
			    'core_send' :
				{
				  'start' : '', # TBD
				  'end' : '' # TBD
				},
			    'core_tree_join' :
				{
				  'start' : '(?P<start_time>.*)\[(?P<event_thread_id>.*)\]: core_process_join: adding new member',
				  'end' : ''
				},
			    'core_tree_leave' :
				{
				  'start' : '', # TBD
				  'end' : '' # TBD
				},
			    'distrib_receive' :
				{
				  'start' : '(?P<start_time>.*) \[(?P<event_thread_id>.*)\]: ssa_upstream_update_conn: SSA_DB_FIELD_DEFS ssa_db allocated pp_field_tables .*',
				  'end' : '(?P<end_time>.*) \[(?P<event_thread_id>.*)\]: ssa_upstream_update_conn: ssa_db .* complete'
				},
			    'distrib_send' :
				{
				  'start' : '', # TBD
				  'end' : '' # TBD
				},
			    'access_receive' :
				{
				  'start' : '(?P<start_time>.*) \[(?P<event_thread_id>.*)\]: ssa_upstream_update_conn: SSA_DB_FIELD_DEFS ssa_db allocated pp_field_tables .*',
				  'end' : '(?P<end_time>.*) \[(?P<event_thread_id>.*)\]: ssa_upstream_update_conn: ssa_db .* complete'
				},
			    'access_client_join' :
				{
				  'start' : '', # TBD
				  'end' : '' # TBD
				},
			    'access_prdb_calc' :
				{
				  'start' : '', # TBD
				  'end' : '' # TBD
				},
			    'access_prdb_send' :
				{
				  'start' : '', # TBD
				  'end' : '' # TBD
				},
			    'acm_receive' :
				{
				  'start' : '(?P<start_time>.*) \[(?P<event_thread_id>.*)\]: ssa_upstream_update_conn: SSA_DB_FIELD_DEFS ssa_db allocated pp_field_tables .*',
				  'end' : '(?P<end_time>.*) \[(?P<event_thread_id>.*)\]: ssa_upstream_update_conn: ssa_db .* complete'
				},
			    'acm_populate' :
				{
				  'start' : '(?P<start_time>.*) \[(?P<event_thread_id>.*)\]: acm_parse_ssa_db: updating cache with new PRDB epoch 0x.*',
				  'end' : '(?P<end_time>.*) \[(?P<event_thread_id>.*)\]: acm_parse_ssa_db: cache update complete with IPDB epochs: .*'
				},
			    'acm_pr_resolve' :
				{
				  'start' : '(?P<start_time>.*) \[(?P<event_thread_id>.*)\]: acm_svr_resolve_path: client [0-9]+$',
				  'end' : '(?P<end_time>.*) \[(?P<event_thread_id>.*)\]: acm_svr_resolve_path: request satisfied from local cache$'
				}
			  }

	ssa_event_info	= {
			    'ssa_smdb_update' :
				{
				  'start' : '(?P<start_time>.*) \[(?P<event_thread_id>.*)\]: core_report: Subnet up event',
				  'start_node' : 'core',
				  'start_id' : '',
				  'end' : '',
				  'end_node' : 'access',
				  'end_id' : ''
				},
			    'ssa_prdb_update' :
				{
				  'start' : '(?P<start_time>.*) \[(?P<event_thread_id>.*)\]: ssa_db_extract: \[',
				  'start_node' : 'access',
				  'start_id' : '',
				  'end' : '(?P<end_time>.*) \[(?P<event_thread_id>).*\]: ssa_db_extract: \]',
				  'end_node' : 'acm',
				  'end_id' : ''
				}
			   }


