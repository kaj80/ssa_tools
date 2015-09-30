#!/usr/bin/python -tt

import sys

try:
	import ip_flow_api
except Exception as e:
	print e
	sys.exit(1)

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
		status = 1

	for nt in ipv4_epochs.keys():
		for ng in ipv4_epochs[nt].keys():
			e_prev = int(ipv4_epochs[nt][ng])
			e_curr = int(ipv4_epochs_new[nt][ng])

			print '-I- %s / %s - IPv4 epoch: old %d new %d' % \
			      (nt, ng, e_prev, e_curr)

			if e_curr != (e_prev + 1):
				status = 1
				break

	if status != 0:
		print '-E- Bad IPv4 epoch on %s node (%s)' % (ng, nt)
		return status

	for nt in ipv6_epochs.keys():
		for ng in ipv6_epochs[nt].keys():
			e_prev = int(ipv6_epochs[nt][ng])
			e_curr = int(ipv6_epochs_new[nt][ng])

			print '-I- %s / %s - IPv6 epoch: old %d new %d' % \
			      (nt, ng, e_prev, e_curr)

			if e_curr != (e_prev + 1):
				status = 1
				break

	if status != 0:
		print '-E- Bad IPv6 epoch on %s node (%s)' % (ng, nt)
		return status

	return 0

def main(argv):

	print '-I- IP update test START'

	res = test_ip_update()
	if res != 0:
		print '-E- IP update test FAILED'
		sys.exit(1)

	print '-I- IP update test PASSED'


if __name__ == "__main__":
        main(sys.argv[1:])
