#!/bin/bash
# CherryPy Django webserver starter script by Loic d'Anterroches
# 
# Based on Example of python daemon starter script
# based on skeleton from Debian GNU/Linux cliechti@gmx.net
#
# Create one for each of your django server and place it in your
# system starter script folder. For example /etc/init.d/ on debian
# based systems.
#

####################################
# Configuration
#
# Your path.
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
# Location of the webserver.py file
DAEMON=/home/rob/projects/backtrac/webserver.py
# PID file to be created. It must match with the PID file in the
# configuration module.
PIDFILE=/var/run/cecil.pid
# Before running the daemon we change the current working directory to
# this directory so to be able to include config files which are not
# in the python path.
BASEDIR=/home/rob/projects/backtrac/
# Config module for the webserver.
CONFIG=cecilconf
#
####################################

DESC="Cecil Django server"
CWD="`pwd`"

test -f $DAEMON || exit 0

set -e
cd $BASEDIR
source /home/rob/.virtualenvs/backtrac/bin/activate
case "$1" in
  start)
	echo -n "Starting $DESC: "
	start-stop-daemon --start --quiet --pidfile $PIDFILE \
	    --exec $DAEMON -- --conf $CONFIG
	echo "$CONFIG."
	;;
  stop)
	echo -n "Stopping $DESC: "
	start-stop-daemon --stop --quiet --pidfile $PIDFILE 
	rm -f $PIDFILE
	echo "$CONFIG."
	;;
  #reload)
	#
	#	If the daemon can reload its config files on the fly
	#	for example by sending it SIGHUP, do it here.
	#
	#	If the daemon responds to changes in its config file
	#	directly anyway, make this a do-nothing entry.
	#
	# echo "Reloading $DESC configuration files."
	# start-stop-daemon --stop --signal 1 --quiet --pidfile \
	#	/var/run/$CONFIG.pid --exec $DAEMON
  #;;
  restart|force-reload)
	#
	#	If the "reload" option is implemented, move the "force-reload"
	#	option to the "reload" entry above. If not, "force-reload" is
	#	just the same as "restart".
	#
	echo -n "Restarting $DESC: "
	start-stop-daemon --stop --quiet --pidfile $PIDFILE
	rm -f $PIDFILE
	sleep 1
	start-stop-daemon --start --quiet --pidfile $PIDFILE \
	    --exec $DAEMON -- --conf $CONFIG
	echo "$CONFIG."
	;;
  *)
	N=$0 #/etc/init.d/$CONFIG.sh
	# echo "Usage: $N {start|stop|restart|reload|force-reload}" >&2
	echo "Usage: $N {start|stop|restart|force-reload}" >&2
	exit 1
	;;
esac
cd $CWD

exit 0

