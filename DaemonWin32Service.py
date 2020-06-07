import os
import socket
import requests

import servicemanager
import win32event
import win32service
import win32serviceutil
from datetime import datetime
import traceback

class DaemonWin32Service(win32serviceutil.ServiceFramework):
	"""Base class to create winservice in Python

	_svc_name_ : Name of the Windows service
	_svc_display_name_ : Name of the Winservice that will be displayed in Service Control Manager
	_svc_description_ : Description of the Winservice that will be displayed in Service Control Manager
	"""

	_svc_name_ = 'pythonService'
	_svc_display_name_ = 'Python Service'
	_svc_description_ = (
		"Python base class Windows Service. "
		"For more details https://github.com/mhammond/pywin32/issues"
	)

	def __init__(self, args):
		win32serviceutil.ServiceFramework.__init__(self, args)
		self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
		socket.setdefaulttimeout(60)

	def SvcStop(self):
		"""
		Called when the service is asked to stop
		"""
		self.stop()
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		win32event.SetEvent(self.hWaitStop)

	def SvcDoRun(self):
		"""
		Called when the service is asked to start
		"""
		self.start()
		servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
							  servicemanager.PYS_SERVICE_STARTED,
							  (self._svc_name_, ''))
		self.run = True
		try:
			self.process = Process(target=self.main)
			self.process.start()
			self.process.run()
		except:
			servicemanager.LogErrorMsg(traceback.format_exc())
			os._exit(-1)

	def start(self):
		"""
		Override to add logic before the start
		eg. running condition
		if you need to do something at the service initialization
		"""
		self.SvcDoRun()

	def stop(self):
		"""
		Override to add logic before the stop
		eg. if you need to do something just before the service is stopped.
		"""
		pass

	def restart(self):
		self.SvcStop()
		self.SvcDoRun()

	def main(self):
		'''
		Business logic Main class to be ovverridden to add logic
		this can be a While True statement that executes your code indefinitely
		'''
		pass

	@classmethod
	def parse_command_line(cls):
		'''
		ClassMethod to parse the command line
		'''
		win32serviceutil.HandleCommandLine(cls)
