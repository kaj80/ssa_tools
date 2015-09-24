#!/usr/bin/python -tt

import sys

try:
	import ip_flow_api
except Exception as e:
	print e
	sys.exit(1)


def main(argv):
	try:
		times = ip_flow_api.get_last_db_update_time()
	except Exception as e:
		print e
		sys.exit(1)

	try:
		epochs = ip_flow_api.get_db_epochs('DB_EPOCH')
	except Exception as e:
		print e
		sys.exit(1)

	try:
		ip_flow_api.generate_ip_update()
	except Exception as e:
		print e
		sys.exit(1)

	try:
		ip_flow_api.generate_pr_update()
	except Exception as e:
		print e
		sys.exit(1)

	print 'Hello SSA IP world!!!'


if __name__ == "__main__":
        main(sys.argv[1:])
