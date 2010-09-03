###########################################################################
# Configuration
#
# Django settings
DJANGO_SETTINGS = 'cecil.settings'
DJANGO_SERVE_ADMIN = True # Serve admin files

# Server settings
IP_ADDRESS = '127.0.0.1'
PORT = 8000
SERVER_NAME = 'localhost'
SERVER_THREADS = 20
# Change it to True if you want it to run as daemon, if you use a
# daemon.sh file you should also change it to True
RUN_AS_DAEMON = False
DAEMON_RUN_DIR = '/' # The daemon will change directory to this one
                     # this is needed to prevent unmounting your
                     # disk.

# Log settings
LOGFILE = '/tmp/webserver.log'
LOGLEVEL = 'INFO' # if DEBUG is True, overwritten to DEBUG
CONSOLE_LOGGING = False
DEBUG = True

# It must match with the path given in your daemon.sh file if you are
# using a daemon.sh file to control the server. 
PIDFILE = '/var/run/cecil.pid' 

# Launch as root to dynamically chown
SERVER_USER = 'nobody'
SERVER_GROUP = 'nobody'

# Enable SSL, if enabled, the certificate and private key must 
# be provided.
SSL = False
SSL_CERTIFICATE = '/full/path/to/certificate'
SSL_PRIVATE_KEY = '/full/path/to/private_key'

#
###########################################################################
