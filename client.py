import socketio, time, datetime, os, socket, uuid, logging, sys
from netifaces import interfaces, ifaddresses, AF_INET

from scapy.all import *

from timeloop import Timeloop
from datetime import timedelta, datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


tl = Timeloop()
sock = socketio.Client()
LOGINPASSWD = os.environ.get('PASSWORD', False)
NODE_ID = int(os.environ.get('NODE_ID', False))

ip_interface = None
primary_ip = None
secondary_ip = None
primary_netmask = None
secondary_netmask = None

logging.getLogger('timeloop').setLevel(logging.ERROR)

logger = logging.getLogger(r'operations')
fileHandler = logging.FileHandler(os.path.join(BASE_DIR, 'operations.log'))
formatter = logging.Formatter('[%(asctime)s] [%(name)s] [%(levelname)s] - %(message)s')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.setLevel(logging.DEBUG)

pingLogger = logging.getLogger('ping')
pingFileHandler = logging.FileHandler(os.path.join(BASE_DIR, 'ping.log'))
pingFileHandler.setFormatter(formatter)
pingLogger.addHandler(pingFileHandler)
pingLogger.setLevel(logging.INFO)

ch = logging.StreamHandler() 			# Console Log Handler
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)
pingLogger.addHandler(ch)


@tl.job(interval=timedelta(seconds=2))
def pingLeat():
	if sock.connected:
		now = datetime.now()
		pingLogger = logging.getLogger('ping')
		pingLogger.info("Sent alive ping as node %s", NODE_ID)
		message('ping', now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-2])


def get_neighbors(identity):
	nw_config_path = os.path.join(BASE_DIR, 'network_config.txt')
	file = open(nw_config_path, 'r')
	matrices = file.readlines()
	items = matrices[NODE_ID].rstrip('\n').split(', ')
	neighbors = [ True if item == "True" else item for item in items ]
	neighbors = [ False if item == "False" else item for item in neighbors ]
	neighbors.pop(0)
	return neighbors


def populate_server_info():
	hostname = socket.gethostname()
	neighbors = get_neighbors(NODE_ID)
	data = {
		"system": hostname,
		"NODE_ID": NODE_ID,
		"neighbors": neighbors,
		"primary_ip": primary_ip,
		"primary_netmask": primary_netmask,
		"secondary_ip": secondary_ip,
		"secondary_netmask": secondary_netmask,
	}
	return data


def get_ip4_addresses():
	global secondary_ip
	global primary_ip
	global ip_interface
	global primary_netmask
	global secondary_netmask
	secondary_ip = None
	secondary_netmask = None
	for interface in interfaces():
		for addr_fam, link in ifaddresses(interface).items():
			if addr_fam == AF_INET and 'docker' not in interface and 'lo' not in interface:
				if sys.platform.startswith('win'):
					windodws_ip_configs = get_windows_if_list()
					if link[0]['addr'] != '127.0.0.1':
						for config in windodws_ip_configs:
							if interface == config['guid']:
								ip_interface = config['name']
						primary_ip = link[0]['addr']
						primary_netmask = link[0]['netmask']
					try:
						secondary_ip = link[1]['addr']
						secondary_netmask = link[1]['netmask']
					except IndexError:
						pass
				elif sys.platform.startswith('lin'):
					if interface == 'wlp6s0' or interface == 'eth0':
						primary_ip = link[0]['addr']
						primary_netmask = link[0]['netmask']
						ip_interface = interface + ':1'
					if interface ==	'wlp6s0:1' or interface ==	'eth0:1':
						secondary_ip = link[0]['addr']
						secondary_netmask = link[0]['netmask']


def message(event, data):
	sock.emit(event, data)


def await_reconnection_command():
	while True:
		reconnect_request = input("attempt reconnection? (y|Y): \t")
		if reconnect_request == 'Y' or 'y':
			return True


@sock.on('recover')
def on_message(data):
	logger.info("Received recovery request. Recovering node "+ str(data['disconnected_node']) + "...")
	logger.info("creating virtual IP address: " + data['ip'])
	if sys.platform.startswith('win'):
		logger.critical('netsh interface ipv4 add address "' + ip_interface + '" ' + data['ip'] + ' ' + data['netmask'])
		cmd_result = os.system('netsh interface ipv4 add address "' + ip_interface + '" ' + data['ip'] + ' ' + data['netmask'])
		logger.critical("Success") if cmd_result == 0 else logger.critical("Error")
	elif sys.platform.startswith('lin'):
		if not LOGINPASSWD:
			logger.warning("Environment variable not Initialized. Unable to recover")
			message('update node', data)
			return
			logger.critical("echo " + LOGINPASSWD + " | sudo -S ifconfig " + ip_interface + " " + data['ip'] + " netmask " + data['netmask'] + " up")
		cmd_result = os.system("echo " + LOGINPASSWD + " | sudo -S ifconfig " + ip_interface + " " + data['ip'] + " netmask " + data['netmask'] + " up")
		logger.critical("Success") if cmd_result == 0 else logger.critical("Error")
	else:
		logger.warning("Unable to determine the System os. Unable to recover")
		message('update node', data)
		return
	get_ip4_addresses()
	if secondary_ip:
		logger.info("Successfully created secondary IP as %s Notifying Server...", secondary_ip)
		updated_data = populate_server_info()
		updated_data.update({'disconnected_node': data['disconnected_node']})
		message('update node', updated_data)
	else:
		logger.warning("unable to recover node")
		message('update node', data)


@sock.on('restore')
def on_message(data):
	logger.info("Received restoration request. Restoring Node "+ str(data['restore_node']) + "...")
	logger.info("Deleting virtual IP address: " + secondary_ip)
	if secondary_ip and secondary_netmask:
		if sys.platform.startswith('win'):
			logger.critical('netsh interface ipv4 delete address "' + ip_interface + '"" ' + secondary_ip + ' ' + secondary_netmask)
			cmd_result = os.system('netsh interface ipv4 delete address "' + ip_interface + '"" ' + secondary_ip + ' ' + secondary_netmask)
			logger.critical("Success") if cmd_result == 0 else logger.critical("Error")
		elif sys.platform.startswith('lin'):
			if not LOGINPASSWD:
				logger.warning("Environment variable not Initialized. Unable to restore IP.")
				message('restore node', data)
				return
				logger.critical("echo " + LOGINPASSWD + " | sudo -S ifconfig " + ip_interface + " " + secondary_ip + " netmask " + secondary_netmask + " down")
			cmd_result = os.system("echo " + LOGINPASSWD + " | sudo -S ifconfig " + ip_interface + " " + secondary_ip + " netmask " + secondary_netmask + " down")
			logger.critical("Success") if cmd_result == 0 else logger.critical("Error")
		else:
			logger.warning("Unable to determine the System os. Unable to restore IP")
			message('restore node', data)
			return
	get_ip4_addresses()
	if not secondary_ip:
		logger.info("Successfully removed secondary IP. Notifying Server...")
		updated_data = populate_server_info()
		updated_data.update({'restore_node': data['restore_node']})
		updated_data.update({'status': True})
		message('restore node', updated_data)
	else:
		logger.warning("unable to restore IP")
		data.update({'status': False})
		message('restore node', data)


@sock.event
def connect():
	get_ip4_addresses()
	data = populate_server_info()
	message('join', data)
	logger.info("connected!")


@sock.event
def connect_error(message):
	logger.debug(message + " Trying to recconnect in 5 seconds")
	try:
		time.sleep(5)
	except KeyboardInterrupt:
		logger.info("KeyboardInterrupt occured.")
		logger.warning("Disconnecting!")
		logger.info('Session Interrupted by User. Program terminated')
		logger.critical("-----------------------------------Program terminated-----------------------------------")
		tl.stop()
		exit()
	reconnect()

@sock.event
def disconnect():
	logger.warning("I'm disconnected!")

def reconnect():
	logger.debug("Attempting Connection")
	try:
		time.sleep(2)
		sock.connect('http://localhost:5000')
	except Exception as e:
		print(e)

if __name__ == '__main__':
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
			exit()
		while True:
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
		exit()