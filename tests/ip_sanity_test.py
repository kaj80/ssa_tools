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

			if e_new != (e_old + 1):
				print '-E- Bad %s epoch on %s node (%s): \
					old = %d, new = %d' % \
					(epoch_type, ng, nt, e_old, e_new)
				status = 1
				break
		if status != 0:
			break

	return status

def print_epoch_dictionary(dictionary, dictionary_content, epoch_type):

	print 'printing ' + dictionary_content + ':'
	for nt in dictionary.keys():
		for ng in dictionary[nt].keys():
			epoch = dictionary[nt][ng]
			print '-I- %s / %s  %s epoch: %s' % \
				(nt, ng, epoch_type, epoch)

def compare_timestamp_dictionaries(old_dictionary, new_dictionary, excluded_types):

	status = 0

	for nt in old_dictionary.keys():
		for ng in old_dictionary[nt].keys():
			tstamp_old = old_dictionary[nt][ng]
			tstamp_new = new_dictionary[nt][ng]

			if nt in excluded_types:
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

def print_timestamp_dictionary(dictionary, dictionary_content):

	print 'printing ' + dictionary_content +'dictionary:'
	for nt in dictionary.keys():
		for ng in dictionary[nt].keys():
			tstamp = dictionary[nt][ng]
			print '-I- %s / %s timestamp: %ld' % \
				(nt, ng, tstamp)

def test_ip_update():
	status = 0

	try:
		print 'getting IPv4 epochs'
		ipv4_epochs = ip_flow_api.get_db_epochs('IPV4_EPOCH')
		print_epoch_dictionary(ipv4_epochs, 'old IPv4 epochs', 'IPv4')

		print 'getting IPv6 epochs'
		ipv6_epochs = ip_flow_api.get_db_epochs('IPV6_EPOCH')
		print_epoch_dictionary(ipv6_epochs, 'old IPv6 epochs', 'IPv6')

		print 'Generating IP update'
		ip_flow_api.generate_ip_update()

		print 'getting IPv4 epochs'
		ipv4_epochs_new = ip_flow_api.get_db_epochs('IPV4_EPOCH')
		print_epoch_dictionary(ipv4_epochs_new, 'new IPv4 epochs', 'IPv4')

		print 'getting IPv6 epochs'
		ipv6_epochs_new = ip_flow_api.get_db_epochs('IPV6_EPOCH')
		print_epoch_dictionary(ipv6_epochs_new, 'new IPv6 epochs', 'IPv4')

	except Exception as e:
		print e
		return 1
	print 'comparing IPv4 epochs'
	status = compare_epoch_dictionaries(ipv4_epochs, \
					    ipv4_epochs_new, 'IPv4')

	if status != 0:
		return status

	print ''
	print 'comparing IPv6 epochs'
	status = compare_epoch_dictionaries(ipv6_epochs, \
					    ipv6_epochs_new, 'IPv6')

	return status

def test_pr_update():

	status = 0

	try:
		print 'getting DB epochs'
		old_db_epochs = ip_flow_api.get_db_epochs('DB_EPOCH')
		print_epoch_dictionary(old_db_epochs, 'old DB epochs', 'DB')

		print 'generating PR update'
		acm_gid = ip_flow_api.generate_pr_update()

		print 'getting DB epochs'
		new_db_epochs = ip_flow_api.get_db_epochs('DB_EPOCH')
		print_epoch_dictionary(new_db_epochs, 'new IPv4 epochs', 'DB')

		print 'popping %s gid from old epochs' % acm_gid
		old_db_epochs['acm_nodes'].pop(str(acm_gid), None)

	except Exception as e:
		print e
		return 1

	print 'comparing DB epochs'
	status = compare_epoch_dictionaries(old_db_epochs, new_db_epochs, 'DB')

	return status

def test_access_failover():

	status = 0

	try:
		print 'getting LAST_UPDATE_TIME timestamps'
		old_update_times = ip_flow_api.get_last_db_update_time()
		print_timestamp_dictionary(old_update_times, 'old update times')

		print 'triggering ACM reconnection'
		ip_flow_api.trigger_acm_reconnection()

		print 'getting LAST_UPDATE_TIME timestamps'
		new_update_times = ip_flow_api.get_last_db_update_time()
		print_timestamp_dictionary(new_update_times, 'new update times')

	except Exception as e:
		print e
		return 1
	print 'comparing timestamp dictionaries'
	status = compare_timestamp_dictionaries(old_update_times, \
		new_update_times, ('core_nodes', 'distrib_nodes', 'access_nodes'))

	return status

def main(argv):

	print 'Starting IP sanity test\n'

	print 'performing initial DB query'
	ip_flow_api.acm_db_query()

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
	print 'generating PR and IP updates'
	ip_flow_api.generate_pr_and_ip_update()

	print '-I- Access failover test START'
	res = test_access_failover()
	if res != 0:
		print '-E- Access failover test FAILED'
		sys.exit(1)
	print '-I- Access failover test PASSED'

	sys.exit(0)

if __name__ == "__main__":
        main(sys.argv[1:])
