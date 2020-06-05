from DaemonWin32Service import DaemonWin32Service

from client import *

class DdrftWorkerService(DaemonWin32Service):

	_svc_name_ = 'ddrft_worker'
	_svc_display_name_ = 'DDRFT Worker Monitor Service'
	_svc_description_ = (
		"Distributed database replication - fault tolerance"
		"For more details contact <email.id@placeholder.domain>"
	)
	
	def start(self):
		self.is_running = True

	def stop(self):
		self.is_running = False

	def main(self):
		tl.start()
		logger = logging.getLogger('operations')
		pingLogger = logging.getLogger('ping')
		logger.critical("-------------------------------Program Execution Started-------------------------------")
		try:
			logger.info("initializing Node identity, gathering IP addresses and connecting to Failover Server")
			if NODE_ID is False:
				logger.critical("ERROR! Could not load Node identity")
				logger.warning("Initialize the Node identity with environment variable 'NODE_ID'. Look at README.txt for more info.")
				logger.critical("-----------------------------------Program terminated-----------------------------------")
				tl.stop()
				print("exiting windows service {}".format(str(e)))
				break
			while self.is_running:
				if not sock.connected:
					reconnect()
				else:
					ping = input("type in disconnect to terminate the session: \n")
					if ping == 'disconnect':
						sock.disconnect()
						await_reconnection_command()
		except KeyboardInterrupt:
			logger.info("KeyboardInterrupt occured.")
			logger.warning("Disconnecting!")
			logger.info('Session Interrupted by User. Program terminated')
			logger.critical("-----------------------------------Program terminated-----------------------------------")
			tl.stop()
			print("exiting windows service {}".format(str(e)))
			break


if __name__ == '__main__':

    print("Installing {} Service".format(LoggerService.__name__))

    LoggerService.parse_command_line()
