#!/bin/bash

#
# Need to execute before running ./gui/maintain_gui.py
#

yum install PyQt4

export GTK2_RC_FILES="$HOME/.gtkrc-2.0"
echo "gtk-theme-name=\"myTheme\"" > ~/.gtkrc-2.0
