#!/usr/bin/python -tt

###############################################################################
#									      #
#              Scalable SA Monitoring Graphic User Interface                  #
#									      #
###############################################################################

import os
import sys
import subprocess
from PyQt4 import QtGui, QtCore

MLNX_LOGO_IMAGE		= 'mellanox_logo.png'
SSA_GUI_HEADER		= 'Scalable SA Maintain'
WORK_DIR		= os.path.dirname(os.path.realpath(sys.argv[0])) + '/../'

# list of tupples in following format: ( 'path', 'path type', 'topology name filter')
TOPO_DIRS		= [ ('setups', 'relative', ''), ('/opt/regression/topologies', 'absolute', 'ssa_setup') ]

class ssa_gui(QtGui.QWidget):

	def __init__(self):
		super(ssa_gui, self).__init__()

		self.initUI()

	def initUI(self):

		# WIDGETS
		self.co_box = QtGui.QTextEdit(self)
		self.co_box.setReadOnly(True)

		self.action	= QtGui.QLabel('Choose action')
		self.topology	= QtGui.QLabel('Choose topology')

		self.btn_run = QtGui.QPushButton('Run')
		self.btn_run.clicked.connect(self.run_ssa)

		self.btn_exit = QtGui.QPushButton('Exit')
		self.btn_exit.clicked.connect(QtCore.QCoreApplication.instance().quit)

		self.action_combo = QtGui.QComboBox(self)
		self.action_combo.addItem('start')
		self.action_combo.addItem('stop')
		self.action_combo.addItem('status')
		self.action_combo.addItem('clean')

		self.topology_combo = QtGui.QComboBox(self)

		for path in TOPO_DIRS:
			if path[1] == 'relative':
				topo_dir = os.path.join(WORK_DIR, path[0])
			else:
				topo_dir = path[0]

			topo_list = os.listdir(topo_dir)

			for item in topo_list:
				if path[2] != '' and not path[2] in item:
					continue

				self.topology_combo.addItem(topo_dir + '/' + item)

		# GRID
		grid = QtGui.QGridLayout()
		grid.setSpacing(10)

		grid.addWidget(self.co_box, 1, 0, 1, 3)
		grid.addWidget(self.action, 2, 0)
		grid.addWidget(self.action_combo, 2, 1)
		grid.addWidget(self.topology, 3, 0)
		grid.addWidget(self.topology_combo, 3, 1)
		grid.addWidget(self.btn_run, 2, 2)
		grid.addWidget(self.btn_exit, 3, 2)

		self.setLayout(grid)

		self.setGeometry(300, 300, 700, 500)
		self.center()
		self.setWindowTitle(SSA_GUI_HEADER)
		self.setWindowIcon(QtGui.QIcon(MLNX_LOGO_IMAGE))

		# Init process
		self.process = QtCore.QProcess(self)
		self.process.readyRead.connect(self.dataReady)

		self.process.started.connect(lambda: self.btn_run.setEnabled(False))
		self.process.finished.connect(lambda: self.btn_run.setEnabled(True))

		self.show()

	def closeEvent(self, event):

		reply = QtGui.QMessageBox.question(self, 'Message',
			"Are you sure to quit?", QtGui.QMessageBox.Yes |
			QtGui.QMessageBox.No, QtGui.QMessageBox.No)

		if (reply == QtGui.QMessageBox.Yes):
			event.accept()
		else:
			event.ignore()

	def center(self):

		qr = self.frameGeometry()
		cp = QtGui.QDesktopWidget().availableGeometry().center()
		qr.moveCenter(cp)
		self.move(qr.topLeft())

	def dataReady(self):

		cursor = self.co_box.textCursor()
		cursor.movePosition(cursor.End)
		cursor.insertText(str(self.process.readAll()))
		self.co_box.ensureCursorVisible()

	def run_command(self, cmd):

		cmd_arr = str(cmd).split()

		# clear console
		self.co_box.setText('')

		self.process.start(cmd_arr[0], cmd_arr[1:])

		# Command for debuggin
		#self.process.start('ping',['127.0.0.1'])

	def run_ssa(self):
		cmd = WORK_DIR + './maintain.py ' + \
		      '-t ' + self.topology_combo.currentText() + \
		      ' --setup ' + self.action_combo.currentText()

		self.run_command(cmd)
		#self.co_box.append(cmd)


def main():

	app = QtGui.QApplication(sys.argv)
	app.setStyle('cleanlooks')
	gui_obj = ssa_gui()
	sys.exit(app.exec_())


# This is the standard boilerplate that calls the main() function
if __name__ == '__main__':
        main()
