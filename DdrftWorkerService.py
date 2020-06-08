import os
import socket
import requests

import servicemanager
import win32event
import win32service
import win32serviceutil

from datetime import datetime

import traceback

from client import run

class DdrftWorkerService(win32serviceutil.ServiceFramework):
	"""Base class to create winservice in Python

	_svc_name_ : Name of the Windows service
	_svc_display_name_ : Name of the Winservice that will be displayed in Service Control Manager
	_svc_description_ : Description of the Winservice that will be displayed in Service Control Manager

	For E.g.	
	_svc_name_ = 'pythonService'
	_svc_display_name_ = 'Python Service'
	_svc_description_ = (
		"Python base class Windows Service. "
		"For more details https://github.com/mhammond/pywin32/issues"
	)

	"""

	_svc_name_ = 'ddrft_worker'
	_svc_display_name_ = 'DDRFT Worker Monitor Service'
	_svc_description_ = (
		"Distributed database replication - fault tolerance"
		"For more details contact <email.id@placeholder.domain>"
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


	def start(self):
		"""
		Override to add logic before the start
		eg. running condition
		if you need to do something at the service initialization
		"""
		self.is_running = True

	def stop(self):
		"""
		Override to add logic before the stop
		eg. if you need to do something just before the service is stopped.
		"""
		self.is_running = False

	def restart(self):
		self.SvcStop()
		self.SvcDoRun()

	def main(self):
		'''
		Business logic Main class to be ovverridden to add logic
		this can be a While True statement that executes your code indefinitely
		'''
		run()


	@classmethod
	def parse_command_line(cls):
		'''
		ClassMethod to parse the command line
		'''
		win32serviceutil.HandleCommandLine(cls)


if __name__ == '__main__':

	DdrftWorkerService.parse_command_line()
