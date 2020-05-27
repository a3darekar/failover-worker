import socketio, time, datetime, os, socket, uuid, logging, sys
from netifaces import interfaces, ifaddresses, AF_INET

from timeloop import Timeloop
from datetime import timedelta, datetime

tl = Timeloop()
sock = socketio.Client()
LOGINPASSWD = os.environ.get('PASSWORD', False)
NODE_ID = int(os.environ.get('NODE_ID', False))
secondary_ip = False
primary_ip = None

logger = logging.getLogger('operations')
fileHandler = logging.FileHandler('operations.log')
formatter = logging.Formatter('[%(asctime)s] - [%(name)s] - [%(levelname)s] - %(message)s')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.setLevel(logging.DEBUG)

pingLogger = logging.getLogger('ping')
pingFileHandler = logging.FileHandler('ping.log')
pingFileHandler.setFormatter(formatter)
pingLogger.addHandler(pingFileHandler)
pingLogger.setLevel(logging.DEBUG)

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
		pingLogger.debug("Sent alive ping")
		message('ping', now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-2])


def get_neighbors(identity):
	file = open('network_config.txt', 'r')
	matrices = file.readlines()
	items = matrices[NODE_ID].rstrip('\n').split(', ')
	neighbors = [ True if item == "True" else item for item in items ]
	neighbors = [ False if item == "False" else item for item in neighbors ]
	logger.info("Self ID: %s", NODE_ID)
	neighbors.pop(0)
	logger.info("All possible neighbors are: %s", neighbors)
	return neighbors


def populate_server_info(ip_addresses):
	hostname = socket.gethostname()
	address_list = ip_addresses
	neighbors = get_neighbors(NODE_ID)
	data = {
		"system": hostname,
		"NODE_ID": NODE_ID,
		"neighbors": neighbors,
		"primary_ip": ip_addr,
		"secondary_ip": secondary_ip,
		"additional_network_info": address_list
	}
	return data


def get_ip4_addresses():
	ip_list = []
	global secondary_ip
	global ip_addr
	secondary_ip = False
	for interface in interfaces():
		for addr_fam, link in ifaddresses(interface).items():
			if addr_fam == AF_INET and 'docker' not in interface and 'lo' not in interface:
				address = {'address': link[0]['addr'], 'netmask': link[0]['netmask']}
				if interface == 'wlp6s0' or interface == 'eth0':
					ip_addr = link[0]['addr']
					ip_list.append({interface: address})
				if interface ==	'wlp6s0:1' or interface ==	'eth0:1':
					secondary_ip = link[0]['addr']
	return ip_list


def message(event, data):
	sock.emit(event, data)


def await_reconnection_command():
	while True:
		reconnect_request = input("attempt reconnection? (y|Y): \t")
		if reconnect_request == 'Y' or 'y':
			return True


@sock.on('recover')
def on_message(data):
	logger.info("Received recovery request:", data)
	logger.info("Recovering Node "+ str(data['disconnected_node']) + "...")
	logger.info("creating virtual IP address: " + data['ip'])
	if sys.platform.startswith('win'):
		os.system("ifconfig wlp6s0:1 " + data['ip'] + " netmask 255.255.255.0 up")
	elif sys.platform.startswith('lin'):
		if not LOGINPASSWD:
			logger.warning("Environment variable not Initialized. Unable to recover")
			message('update node', data)
			return
		os.system("echo " + LOGINPASSWD + " | sudo -S ifconfig wlp6s0:1 " + data['ip'] + " netmask 255.255.255.0 up")
	else:
		logger.warning("Unable to determine the System os. Unable to recover")
		message('update node', data)
		return
	ip_addresses = get_ip4_addresses()
	logger.info(ip_addresses)
	logger.info(secondary_ip)
	if secondary_ip:
		logger.info("Success! Notifying Server...")
		updated_data = populate_server_info(ip_addresses)
		message('update node', updated_data)
	else:
		logger.warning("unable to recover node")
		message('update node', data)


@sock.event
def connect():
	ip_addresses = get_ip4_addresses()
	data = populate_server_info(ip_addresses)
	message('join', data)
	logger.info("connected!")


@sock.event
def connect_error():
	logger.critical("The connection failed!")
	logger.warning("trying to recconnect.")
	await_reconnection_command()

@sock.event
def disconnect():
	logger.warning("I'm disconnected!")

def reconnect():
	time.sleep(2)
	sock.connect('http://localhost:5000')

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