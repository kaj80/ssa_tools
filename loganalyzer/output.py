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
#        SSA Log Analyzer output module                                       #
#                                                                             #
#        Author: Ilya Nelkenbaum <ilyan@mellanox.com>                         #
#                                                                             #
###############################################################################

import config

###############################################################################
# Constants                                                                   #
###############################################################################
LA_ATTR_MAX_LEN		= 27


###############################################################################
# SSA Log Analyzer output module internal calls                               #
###############################################################################

def print_line(f, attr_list, mode):

	for i in range(0, len(attr_list)):

		attr = attr_list[i]
		if mode == 'regular' :
			f.write(' ' + attr.ljust(LA_ATTR_MAX_LEN) +  '|')

		elif mode == 'csv' :
			if i == (len(attr_list) - 1) :
				f.write(str(attr))
			else:
				f.write(str(attr) + ',')

	f.write('\n')

def print_line_with_dash(f, attr_list, mode):

	print_line(f, attr_list, mode)

	f.write('-' * len(attr_list) * (LA_ATTR_MAX_LEN + 2) + '\n')

# complex line is a line where one or more
# attributes might contain multiple values
def print_complex_line(f, attr_list, mode):

	max_fields = 0
	tmp_list = []

	for attr in attr_list:

		if type(attr) is list:
			if len(attr) == 0:
				tmp_list.append(' ')
				continue

			if len(attr) > max_fields:
				max_fields = len(attr)

			tmp_list.append(attr[0])
		else:
			tmp_list.append(attr)

	print_line(f, tmp_list, mode)

	for i in range(1, max_fields):
		tmp_list = []

		for attr in attr_list:

			if type(attr) is list:
				if len(attr) == 0 or len(attr) < i:
					tmp_list.append(' ')
					continue

				tmp_list.append(attr[i])
			else:
				tmp_list.append(' ')

		print_line(f, tmp_list, mode)

	if mode == 'regular' :
		f.write('-' * len(attr_list) * (LA_ATTR_MAX_LEN + 2) + '\n')


def print_header(f, str, attr_list, mode):

	if mode == 'regular' :
		line_len = len(attr_list) * (LA_ATTR_MAX_LEN + 2)
		str_len = len(str)

		f.write('-' * line_len + '\n')
		f.write(' ' * (line_len / 2 - str_len / 2) + str + \
			' ' * (line_len - line_len / 2 - str_len / 2 - 2) + '|\n')
		f.write('-' * line_len + '\n')
		print_line_with_dash(f, attr_list, mode)
	elif mode == 'csv' :
		print_line(f, attr_list, mode)

	else :
		print '-E- unknown output mode ' + mode



###############################################################################
# SSA Log Analyzer output module calls                                        #
###############################################################################

def info_dump(file, dlist, header, field_list):

	mode = config.output_mode

	if not dlist:
		return

	fout = open(file, 'w')

	print_header(fout, header, field_list, mode)

	for elem in dlist:

		attr_list = []

		for attr in field_list:
			attr_list.append(getattr(elem, attr))

		print_complex_line(fout, attr_list, mode)

	fout.close()

