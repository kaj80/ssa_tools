#!/usr/bin/python -tt

import sys

try:
	import ip_flow_api
except Exception as e:
	print e
	sys.exit(1)

def compare_epoch_dictionaries(old_dictionary, new_dictionary, epoch_type):

	status = 0

	for nt in old_dictionary.keys():
		for ng in old_dictionary[nt].keys():
			e_old = int(old_dictionary[nt][ng])
			e_new = int(new_dictionary[nt][ng])

			print '-I- %s / %s - %s epoch: old %d new %d' % \
			      (nt, ng, epoch_type, e_old, e_new)

			if e_new != (e_old + 1):
				print '-E- Bad %s epoch on %s node (%s)' % \
					(epoch_type, ng, nt)
				status = 1
				break
		if status != 0:
			break

	return status

def compare_timestamp_dictionaries(old_dictionary, new_dictionary, excluded_types): #FIXME

	status = 0

	for nt in old_dictionary.keys():
		for ng in old_dictionary[nt].keys():
			tstamp_old = old_dictionary[nt][ng]
			tstamp_new = new_dictionary[nt][ng]

			print '-I- %s / %s timestamp: old %ld, new %ld' % \
				(nt, ng, tstamp_old, tstamp_new)

			if (nt in excluded_types):
				if tstamp_old != tstamp_new:
					print "-E- Bad timestamp on %s node" \
					      "(%s - shouldn't update)" % (ng, nt)
					status = 1
					break
			else:
				if tstamp_old >= tstamp_new:
					print "-E- Bad timestamp on %s node (%s)" \
						% (ng, nt)
					status = 1
					break
		if status != 0:
			break
	return status

def test_ip_update():
	status = 0

	try:
		ipv4_epochs = ip_flow_api.get_db_epochs('IPV4_EPOCH')
		ipv6_epochs = ip_flow_api.get_db_epochs('IPV6_EPOCH')

		ip_flow_api.generate_ip_update()

		ipv4_epochs_new = ip_flow_api.get_db_epochs('IPV4_EPOCH')
		ipv6_epochs_new = ip_flow_api.get_db_epochs('IPV6_EPOCH')
	except Exception as e:
		print e
		return 1

	status = compare_epoch_dictionaries(ipv4_epochs, \
					    ipv4_epochs_new, 'IPv4')

	if status != 0:
		return status

	print ''
	status = compare_epoch_dictionaries(ipv6_epochs, \
					    ipv6_epochs_new, 'IPv6')

	return status

def test_pr_update(): #FIXME

	status = 0

	try:
		old_db_epochs = ip_flow_api.get_db_epochs('DB_EPOCH')

		acm_gid = ip_flow_api.generate_pr_update()

		new_db_epochs = ip_flow_api.get_db_epochs('DB_EPOCH')

		old_db_epochs['acm_nodes'].pop(str(acm_gid), None)

	except Exception as e:
		print e
		return 1

	status = compare_epoch_dictionaries(old_db_epochs, new_db_epochs, 'DB')

	return status

def test_sm_handover(): #FIXME

	status = 0

	try:
		old_update_times = ip_flow_api.get_last_db_update_time()

		ip_flow_api.bounce_sm_port()

		new_update_times = ip_flow_api.get_last_db_update_time()

	except Exception as e:
		print e
		return 1

	status = compare_timestamp_dictionaries(old_update_times, \
						new_update_times, (core_nodes))

	return status

def test_distrib_failover(): #FIXME

	status = 0

	try:
		old_db_epochs = ip_flow_api.get_db_epochs('DB_EPOCH')

		#FIXME - add code that makes distribution fail

		new_db_epochs = ip_flow_api.get_db_epochs('DB_EPOCH')

	except Exception as e:
		print e
		return 1

	status = compare_epoch_dictionaries(old_db_epochs, new_db_epochs, 'DB')

	return status

def test_access_failover(): #FIXME

	status = 0

	try:
		old_update_times = ip_flow_api.get_last_db_update_time()

		ip_flow_api.trigger_acm_reconnection()

		new_update_times = ip_flow_api.get_last_db_update_time()

	except Exception as e:
		print e
		return 1

	status = compare_timestamp_dictionaries(old_update_times, \
		new_update_times, ('core_nodes', 'distrib_nodes', 'access_nodes'))

	return status

def main(argv): #FIXME

	print '-I- IP update test START'
	res = test_ip_update()
	if res != 0:
		print '-E- IP update test FAILED'
		sys.exit(1)
	print '-I- IP update test PASSED\n'

	print '-I- PR update test START'
	res = test_pr_update()
	if res != 0:
		print '-E- PR update test FAILED'
		sys.exit(1)
	print '-I- PR update test PASSED\n'

	# to prevent ssadmin stats from returning 'error event'
	ip_flow_api.generate_pr_and_ip_update()

#	print '-I- SM handover test START'
#	res = test_sm_handover()
#	if res != 0:
#		print '-E- SM handover test FAILED'
#		sys.exit(1)
#	print '-I- SM handover test PASSED'
#
#	print '-I- Distribution failover test START'
#	res = test_distrib_failover()
#	if res != 0:
#		print '-E- Distribution failover test FAILED'
#		sys.exit(1)
#	print '-E- Distribution failover test PASSED'

	print '-I- Access failover test START'
	res = test_access_failover()
	if res != 0:
		print '-E- Access failover test FAILED'
		sys.exit(1)
	print '-I- Access failover test PASSED'

	#FIXME: add ret value?

if __name__ == "__main__":
        main(sys.argv[1:])
