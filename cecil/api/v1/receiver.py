import socket, time, string, sys, urlparse, uuid, signal, select, datetime, os
import tarfile
from threading import *

from django.conf import settings

class PackageReceiver(Thread):

	def __init__(self, backup, port=None, callback=lambda x: None, exception_callback=lambda x: None):
		Thread.__init__(self)
		
		if not os.path.exists(settings.BACKTRAC_TMP_DIR):
			os.makedirs(settings.BACKTRAC_TMP_DIR)
		
		port = port or 0
		self.backup = backup
		self.filename = os.path.join(settings.BACKTRAC_TMP_DIR, 'r-%s.tar.gz' % backup.uuid)
		self.callback = callback
		self.exception_callback = exception_callback
		
		self.stopping = False
		
		self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server.bind(('', port))
		self.port = self.server.getsockname()[1]
		self.server.listen(1)
		
		self.client = None
	
	def run(self):
		try:
			self.receive()
		except Exception as e:
			self.exception_callback(e)
	
	def receive(self):
		while not self.stopping:
			rr, rw, rx = select.select([self.server], [], [], 1)
			if self.server in rr:
				self.client, address = self.server.accept()
				self.transfer()
				break
		self.server.close()
		self.callback(self.filename)
	
	def transfer(self):
		f = open(self.filename, 'wb')
		while 1:
			data = self.client.recv(1024)
			if not data:
				break
			f.write(data)
		f.close()
	
	def close(self):
		self.server.shutdown(socket.SHUT_RDWR)
		self.server.close()
		
		if self.client is not None:
			self.client.shutdown(socket.SHUT_RDWR)
			self.client.close()
	
	def sighandler(self, signum, frame):
		self.stopping = True
