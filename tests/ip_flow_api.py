##############################################################################
#
# Module name:         ip_flow_api
# Purpose:             SSA IP support feature verification
#
# ----------------------------------------------------------------------------
#
# Method name:         get_last_db_update_time()
#
# Return value:        dictionary with the following format:
#
#                      { 'core_nodes' : { 'gid1' : 'last_update_time',
#                                         'gid2' : 'last_update_time' },
#                        ...
#                        'acm_nodes'  : { 'gid10' : 'last_update_time' },
#                                       { 'gid11' : 'last_update_time' },
#                                       ...
#                      }
#
#                      * note: last_update_time is in micro seconds
#
# ----------------------------------------------------------------------------
#
# Method name:        get_db_epochs(epoch_type)
#
# Arguments:          'epoch_type' can get 1 of the following values:
#                     - DB_EPOCH
#                     - IPV4_EPOCH
#                     - IPV6_EPOCH
#                     - NAME_EPOCH
#
# Return value:       dictionary with the following format:
#
#                      { 'core_nodes' : { 'gid1' : 'epoch',
#                                         'gid2' : 'epoch' },
#                        ...
#                        'acm_nodes'  : { 'gid10' : 'epoch' },
#                                       { 'gid11' : 'epoch' },
#                                       ...
#                      }
#
# ----------------------------------------------------------------------------
#
# Method name:        generate_ip_update()
#
# Description:        generates ip tables update by adding or modifying an
#                     additional artificial ip record to hosts address file
#                     in core layer.
#
#                     * note: some 'sleep' should be taken after execution
#                             in order to allow SSA fabric to propagate the
#                             desired change
#
# ----------------------------------------------------------------------------
#
# Method name:        generate_pr_update()
#
# Description:        generates path record tables update by connecting /
#                     disconnecting randomly chosen ACM node port from fabric.
#
# Return value:       GID of the connected / disconnected port
#
#                     * note: some 'sleep' should be taken after execution
#                             in order to allow SSA fabric to propagate the
#                             desired change
#
# ----------------------------------------------------------------------------
#
# Method name:        generate_pr_and_ip_update()
#
# Description:        generating both IP and path record tables update.
#
# Return value:       GID of the connected / disconnected port
#
#                     * note: some 'sleep' should be taken after execution
#                             in order to allow SSA fabric to propagate the
#                             desired change
#
# ----------------------------------------------------------------------------
#
# Method name:        trigger_acm_reconnection()
#
# Description:        makes all ACM nodes reconnect to the fabric
#
#                     * note 1: some 'sleep' should be taken after execution
#                               in order to allow SSA fabric to propagate the
#                               desired change
#
#                     * note 2: currently uses ssadmin rejoin command, as
#                               the disconnect command doesn't seem to
#                               be working #FIXME FIXME
#
##############################################################################

import time
import datetime
import commands
import atexit

# wait timeout used for fabric update propagation
update_wait = 7

gid_to_type = {}

ip1 = '100.0.254.254'
ip2 = '100.0.255.254'
ip_was_set = 0

lid_disabled = 0
port_disabled = 0

SSADMIN_PREFIX = '/usr/local'
HOST_ADDR_FILE = SSADMIN_PREFIX + '/etc/rdma/ibssa_hosts.data'

LOGFILE_PREFIX = '/var/log'
LOGFILE_PATH = LOGFILE_PREFIX + '/ip_flow_api.log'

file_obj = None

cmd_map = \
	{ 'nodeinfo'    : SSADMIN_PREFIX + '/sbin/ssadmin -r nodeinfo --format=short ',
	  'db_epoch'    : SSADMIN_PREFIX + '/sbin/ssadmin -r stats ',
	  'last_update' : SSADMIN_PREFIX + '/sbin/ssadmin -r stats LAST_UPDATE_TIME ',
	  'db_query'    : SSADMIN_PREFIX + '/sbin/ssadmin -r dbquery --filter=acm ',
	  'rejoin'      : SSADMIN_PREFIX + '/sbin/ssadmin -r rejoin --filter=acm'}
	  #FIXME rejoin should be replaced with disconnect

node_type_lookup = \
	{ 'Core'         : 'core_nodes',
	  'Distribution' : 'distrib_nodes',
	  'Access'       : 'access_nodes',
	  'Consumer'     : 'acm_nodes' }


class IpException(Exception):
	pass


def _exec_cmd(cmd, err_msg, check_output = 0):

	file_obj.write('_exec_cmd : executing cmd: ' + cmd + '\n')

	(status, output) = commands.getstatusoutput(cmd)
	if status != 0:
		file_obj.write('_exec_cmd : ' + err_msg + '\n')
		raise IpException(err_msg)

	output_lines = output.split('\n')

	if check_output != 0 and len(output_lines) == 0:
		file_obj.write('_exec_cmd : ' + err_msg + '\n')
		raise IpException(err_msg)

	return output_lines

def _ip_flow_init():
	global gid_to_type
	global file_obj

	file_obj = open(LOGFILE_PATH, 'a')
	file_obj.write('opening log file\n')

	err_msg = 'ERROR: unable to get SSA fabric node info'
	fabric = _exec_cmd(cmd_map['nodeinfo'], err_msg, 1)

	for line in fabric:
		list = line.split()
		gid_to_type[list[0]] = list[2]


#
# Module cleanup callback
#
@atexit.register
def _ip_flow_destroy():

	if ip_was_set != 0:
		if ip_was_set == 1:
			cmd = 'sudo sed -i "/^' + ip1  + '/d" ' + HOST_ADDR_FILE
		elif ip_was_set == 2:
			cmd = 'sudo sed -i "/^' + ip2  + '/d" ' + HOST_ADDR_FILE

		err_msg = 'ERROR: unable to delete added IP record'
		_exec_cmd(cmd, err_msg)

	if lid_disabled != 0:
		cmd = 'ibportstate ' + str(lid_disabled) + ' ' + \
		      str(port_disabled) + ' enable'
		err_msg = 'ERROR: unable to enable disabled port'
		_exec_cmd(cmd, err_msg)

		time.sleep(update_wait)

		print_str =  'PORT ' + str(lid_disabled) + ':' + \
		      str(port_disabled) + ' was ENABLED'

		print print_str
		file_obj.write(print_str + '\n')

	file_obj.write('closing log file\n')
	file_obj.close()

#
# input --> output example:
#
# (Sep 27 10:26:01 400625) --> (23279161400625.0)
#
# * notes:
#           - by default 1900 year is taken is reference
#           - output units are [usecs]
#
def _gen_timestamp(time_str_list):
	time_str = " ".join(time_str_list)

	dt = datetime.datetime.strptime(time_str, "%b %d %H:%M:%S %f")
	tdelta = dt - datetime.datetime(1900, 1, 1)

	tdelta_secs = tdelta.days * 24 * 60 * 60 + tdelta.seconds
	tstamp = tdelta_secs * 1e6 + tdelta.microseconds

	return tstamp


def _gid_to_guid(gid):
	gid_list = gid.split(':')[-4:]
	gid_list = [e.zfill(4) for e in gid_list]
	return "".join(gid_list).lstrip('0')


def _get_master_gid():

	cmd     = 'sminfo'
	err_msg = 'ERROR: unable to get SM lid'
	sminfo  = _exec_cmd(cmd, err_msg, 1)

	sm_guid = sminfo[0].split()[6][2:-1]

	master_gid = ''
	for gid in gid_to_type.keys():
		if gid_to_type[gid] == 'Core':
			guid = _gid_to_guid(gid)
			if guid == sm_guid:
				master_gid = gid
				break

	return master_gid


def _gid_to_lid(gid):
	lid = 0

	master_sm_gid = _get_master_gid()
	if master_sm_gid == '':
		err_msg = 'ERROR: unable to get master SM GID'
		raise IpException(err_msg)

	cmd = 'saquery PR --sgid ' + master_sm_gid + \
	      ' --dgid ' + gid + ' | grep dlid'
	err_msg = 'ERROR: unable to issue SA PR query'
	pr = _exec_cmd(cmd, err_msg)

	lid = int(pr[0].split('.')[-1])

	return lid


def get_remote_lid_and_port(lid):
	cmd = 'saquery LR ' + str(lid)
	err_msg = 'ERROR: unable to issue Link Record'
	lr = _exec_cmd(cmd, err_msg)

	remote_lid = 0
	remote_port = 0
	for line in lr:
		line_list = line.split('.')
		key = line_list[0].strip()
		if key == 'ToPort':
			remote_port = int(line_list[-1])
		elif key == 'ToLID':
			remote_lid = int(line_list[-1])

	return (remote_lid, remote_port)


def get_last_db_update_time():
	res = {}

	res['core_nodes'] = {}
	res['distrib_nodes'] = {}
	res['access_nodes'] = {}
	res['acm_nodes'] = {}

	cmd = cmd_map['last_update']
	err_msg = 'ERROR: unable to get SSA nodes last update time'
	times = _exec_cmd(cmd, err_msg)

	for t in times:
		t_list = t.split()
		gid = t_list[0][:-1]
		timestamp = _gen_timestamp(t_list[2:])
		print type(tstamp)
		node_type = node_type_lookup.get(gid_to_type[gid])
		if node_type != 'None':
			res[node_type][gid] = timestamp
		else:
			print 'WARN: invalid gid type detected: (gid, type)' \
			      ' = (%s, %s)' % (gid, gid_to_type[gid])

	return res


def get_db_epochs(epoch_type):
	res = {}

	res['core_nodes'] = {}
	res['distrib_nodes'] = {}
	res['access_nodes'] = {}
	res['acm_nodes'] = {}

	cmd = cmd_map['db_epoch'] + epoch_type
	err_msg = 'ERROR: unable to get SSA nodes epochs'
	epochs = _exec_cmd(cmd, err_msg)

	for e in epochs:
		e_list = e.split()

		if e_list[0] == 'ERROR:' or e_list[0] == 'ERROR':
			continue

		gid = e_list[0][:-1]
		epoch = e_list[2]

		node_type = node_type_lookup.get(gid_to_type[gid])
		if node_type != 'None':
			res[node_type][gid] = epoch
		else:
			print 'WARN: invalid gid type detected: (gid, type) =' \
			      ' (%s, %s)' % (gid, gid_to_type[gid])

	return res


def generate_ip_update():
	global ip_was_set

	master_sm_gid = _get_master_gid()
	if master_sm_gid == '':
		err_msg = 'ERROR: unable to get master SM GID'
		raise IpException(err_msg)

	if ip_was_set == 0:
		addr_record_new = ip1 + ' ' + master_sm_gid
		cmd = 'sudo sed -i "$ a ' + addr_record_new + '" ' + HOST_ADDR_FILE
		ip_was_set = 1
	elif ip_was_set == 1:
		cmd = 'sudo sed -i "s/^' + ip1 + '/' + ip2  + '/g" ' + HOST_ADDR_FILE
		ip_was_set = 2
	elif ip_was_set == 2:
		cmd = 'sudo sed -i "s/^' + ip2 + '/' + ip1  + '/g" ' + HOST_ADDR_FILE
		ip_was_set = 1

	err_msg = 'ERROR: unable to modify hosts addr file'
	_exec_cmd(cmd, err_msg)

	cmd = 'sudo kill -s HUP `pidof opensm`'
	err_msg = 'ERROR: unable to send SIGHUP to OpenSM'
	_exec_cmd(cmd, err_msg)

	time.sleep(update_wait)

	cmd = cmd_map['db_query']
	err_msg = 'ERROR: unable to send dbquery to ACM nodes'
	_exec_cmd(cmd, err_msg)

	time.sleep(update_wait)


def generate_pr_update():
	global lid_disabled
	global port_disabled

	cmd = cmd_map['nodeinfo'] + '--filter=acm'
	err_msg = 'ERROR: unable to get list of ACMs'
	acms = _exec_cmd(cmd, err_msg, 1)

	acm_gid = ''
	for line in acms:
		line_list = line.split()
		if line_list[0] != 'ERROR':
			acm_gid = line_list[0]

	if acm_gid == '':
		print 'ERROR: unable to find any ACM client'
		return ''

	if lid_disabled == 0:
		(lid, port) = get_remote_lid_and_port(_gid_to_lid(acm_gid))
		action = 'disable'
	else:
		lid = lid_disabled
		port = port_disabled
		action = 'enable'

	cmd = 'ibportstate ' + str(lid) + ' ' + str(port) + ' ' + action
	err_msg = 'ERROR: unable to issue ibportstate'
	_exec_cmd(cmd, err_msg)

	time.sleep(update_wait)

	if lid_disabled == 0:
		lid_disabled = lid
		port_disabled = port
	else:
		lid_disabled = 0
		port_disabled = 0

	print_str = 'PORT ' + str(lid) + ':' + str(port) + \
	      ' was ' + action.upper() + 'D'
	print print_str
	file_obj.write(print_str + '\n')

	cmd = cmd_map['db_query']
	err_msg = 'ERROR: unable to send dbquery to ACM nodes'
	_exec_cmd(cmd, err_msg)

	time.sleep(update_wait)

	return acm_gid


def generate_pr_and_ip_update():

	generate_ip_update()

	gid = generate_pr_update()

	return gid

def trigger_acm_reconnection():

	cmd = cmd_map['rejoin'] #FIXME using rejoin because disconnect doesn't seem to work
	err_msg = 'ERROR: unable to send disconnect cmd to ACM nodes'
	_exec_cmd(cmd, err_msg)

	time.sleep(update_wait * 3)

	cmd = cmd_map['db_query']
	err_msg = 'ERROR: unable to send dbquery to ACM nodes'
	_exec_cmd(cmd, err_msg)

	time.sleep(update_wait)

_ip_flow_init()
