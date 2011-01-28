Backtrac Backup System
======================

Backtrac is a version centric backup system for office and professional use.

The web interface offers fast and effective access to all your files, with
instant restoration of the unlimited version history for every file.

All aspects of the system are written in pure Python, making use of the Django
web development framework. The core networking functionality is implemented
using the Twisted framework.

Requirements
============

Both the client and server applications require Python version 2.6 or greater.
Python 3.x is not supported at the present time.

Client
------

The client is implemented in pure Python, based on the Twisted networking
toolkit. This is the only 3rd party library that is required.

* Twisted >= 10.2.0

Server
------

The server daemon is also based on Twisted, and also makes use of the Django
framework for database access (via the ORM). The web interface is also built
entirely using Django.

The application is being developed against Django trunk, with the expectation
that version 1.3 will be released before Backtrac itself is finished. As such,
the server is detailed as requiring Django version 1.3.

* Twisted >= 10.2.0
* Django == 1.3

Installation
============

Coming soon.
