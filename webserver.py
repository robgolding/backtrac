#!/usr/bin/env python
#
# Copyright 2006-2008, Loic d'Anterroches
#
# Released under the Python license.
#
# Daemon main loop based on Juergen Hermanns
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012
# downloaded from: http://homepage.hispeed.ch/py430/python/daemon.py
# 

import logging
import sys
import os
import signal
import time
from optparse import OptionParser
from wsgiserver import CherryPyWSGIServer as Server
from django.core.handlers.wsgi import WSGIHandler
# Django related import are performed after the loading of the
# configuration as we need to set the DJANGO_SETTINGS_MODULE
# environment variable which comes from the config.

from translogger import TransLogger

# Global variable!
options = None

def change_uid_gid(uid, gid=None):
    """Try to change UID and GID to the provided values.
    UID and GID are given as names like 'nobody' not integer.

    Src: http://mail.mems-exchange.org/durusmail/quixote-users/4940/1/
    """
    if not os.geteuid() == 0:
        # Do not try to change the gid/uid if not root.
        return
    (uid, gid) = get_uid_gid(uid, gid)
    os.setgid(gid)
    os.setuid(uid)

def get_uid_gid(uid, gid=None):
    """Try to change UID and GID to the provided values.
    UID and GID are given as names like 'nobody' not integer.

    Src: http://mail.mems-exchange.org/durusmail/quixote-users/4940/1/
    """
    import pwd, grp
    uid, default_grp = pwd.getpwnam(uid)[2:4]
    if gid is None:
        gid = default_grp
    else:
        try:
            gid = grp.getgrnam(gid)[2]            
        except KeyError:
            gid = default_grp
    return (uid, gid)

def chown_pid_log(uid, gid=None):
    global options
    if not os.geteuid() == 0:
        # Do not try to change the gid/uid if not root.
        return
    (uid, gid) = get_uid_gid(uid, gid)
    if os.path.exists(options.PIDFILE):
        os.chown(options.PIDFILE, uid, gid)
    os.chown(options.LOGFILE, uid, gid)

class Runner:
    """Runner class.

    Store some basic info like the server instance so the signal
    handling methods can easily access it.
    """

    def __init__(self):
        """Simply init the server with nothing."""
        self.server = None

    def clean(self):
        """Clean the PID file"""
        global options
        if options.RUN_AS_DAEMON:
            try:
                os.remove(options.PIDFILE)
            except Exception, e:
                log = logging.getLogger("webserver.py")
                log.debug("Can't clean PID file: %s" % options.PIDFILE)
                log.debug(str(e))

    def main(self):
        """Real main loop of the daemon."""
        global options
        log = logging.getLogger("webserver.py")        
        if options.RUN_AS_DAEMON:
            #ensure the that the daemon runs a normal user
            change_uid_gid(options.SERVER_USER, options.SERVER_GROUP)
        if options.DJANGO_SERVE_ADMIN:
            from django.core.servers.basehttp import AdminMediaHandler
            app = AdminMediaHandler(WSGIHandler())
        else:
            app = WSGIHandler()
        app = TransLogger(app)
        self.server = Server((options.IP_ADDRESS, options.PORT),
                             app, options.SERVER_THREADS, options.SERVER_NAME)
        if options.SSL:
            self.server.ssl_certificate = options.SSL_CERTIFICATE
            self.server.ssl_private_key = options.SSL_PRIVATE_KEY
        signal.signal(signal.SIGUSR1, self.signal_handler)
        signal.signal(signal.SIGHUP, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)    
        try:
            log.info("Start the server on %s:%s" % (options.IP_ADDRESS, str(options.PORT)))
            self.server.start()
        except KeyboardInterrupt:
            self.server.stop()
            log.debug("KeyboardInterrupt: stop the server")
            self.clean()

    def signal_handler(self, sig, stack):
        """Handle the signal sent to the daemon."""
        if sig == signal.SIGUSR1:
            pass
        elif sig == signal.SIGHUP:
            log.debug("Should reload itself.")
        elif sig == signal.SIGTERM:
            self.server.stop()
            log.debug("SIGTERM: stop the server")
            self.clean()
            sys.exit(0)
        else:
            log.debug("SIG: %s" % str(sig))

# TERM, INT
# QUIT
# HUP
# USR1
# USR2
# WINCH

def parse_options():
    """Return the run options for the server.

    It is merging options from command line and from the config python
    module. It sets and import the right stuff for Django.
    """
    parser = OptionParser()
    parser.add_option("--conf", "-c", dest="config",
                      help="load configuration from file",
                      action="store", default="config")
    (cmd_options, args) = parser.parse_args()
    try:
        options = __import__(cmd_options.config)
    except ImportError, e:
        raise EnvironmentError, "Could not import settings '%s' (Is it on sys.path? Does it have syntax errors?): %s" % (cmd_options.config, e)
    os.environ["DJANGO_SETTINGS_MODULE"] = options.DJANGO_SETTINGS
    return options

if __name__ == "__main__":
    # Get the options
    options = parse_options()
    #
    # Logging stuff.
    #
    logging.basicConfig(filename=options.LOGFILE,
                        format='%(asctime)s %(levelname)s %(message)s')
    log = logging.getLogger("webserver.py")
    if options.DEBUG:
        log.setLevel(logging.DEBUG)
    else:
        log.setLevel(getattr(logging, options.LOGLEVEL.upper()))
    
    if options.CONSOLE_LOGGING:
        console = logging.StreamHandler()
        formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        console.setFormatter(formatter)
        log.addHandler(console)
    
    from cecil.apps.backups.utils import resubmit_all
    
    resubmit_all()
    
    if options.RUN_AS_DAEMON:
        log.info("Run as daemon")
        # do the UNIX double-fork magic, see Stevens' "Advanced
        # Programming in the UNIX Environment" for details (ISBN 0201563177)
        if os.path.exists(options.PIDFILE):
            log.info("PID file exists: %s, webserver already running, exiting" % options.PIDFILE)
            sys.exit(1)
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError, e:
            log.debug("Fork #1 failed: %d (%s)" % (e.errno, e.strerror))
            sys.exit(1)
        # decouple from parent environment
        os.chdir(options.DAEMON_RUN_DIR)   #don't prevent unmounting....
        os.setsid()
        os.umask(0)
        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent, print eventual PID before
                open(options.PIDFILE,'w').write("%d"%pid)
                chown_pid_log(options.SERVER_USER, options.SERVER_GROUP)
                sys.exit(0)
        except OSError, e:
            log.debug("Fork #2 failed: %d (%s)" % (e.errno, e.strerror))
            sys.exit(1)
    # Start the daemon main loop
    run = Runner()
    run.main()

