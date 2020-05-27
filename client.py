import socketio
import time, datetime, os, socket, uuid
from netifaces import interfaces, ifaddresses, AF_INET

from timeloop import Timeloop
from datetime import timedelta, datetime

LOGINPASSWD = os.environ.get('PASSWORD', False)
NODE_ID = int(os.environ.get('NODE_ID', False))

tl = Timeloop()
sock = socketio.Client()


@tl.job(interval=timedelta(seconds=2))
def ping_beat():
	if sock.connected:
		now = datetime.now()
		message('ping', now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-2])


def get_neighbors(identity):
	file = open('network_config.txt', 'r')
	matrices = file.readlines()
	items = matrices[NODE_ID].rstrip('\n').split(', ')
	neighbors = [ True if item == "True" else item for item in items ]
	neighbors = [ False if item == "False" else item for item in neighbors ]
	print("Self ID: ", neighbors[0])
	print("All possible neighbors are: ")
	for neighbor in neighbors[1:]:
		print(neighbor, end=' ')
	print()
	neighbors.pop(0)
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
	print("Received recovery request:", data)
	print("Recovering Node "+ str(data['disconnected_node']) + "...")
	print(TLOAD + "creating virtual IP address: " + data['ip'], ENDC)
	if sys.platform.startswith('win'):
		os.system("ifconfig wlp6s0:1 192.168.0.150 netmask 255.255.255.0 up")
	elif sys.platform.startswith('lin'):
		if not LOGINPASSWD:
			print(TRED + "Environment variable not Initialized. Unable to recover", ENDC)
			message('update node', data)
			return
		os.system("echo " + LOGINPASSWD + " | sudo -S ifconfig wlp6s0:1 192.168.0.150 netmask 255.255.255.0 up")
	else:
		print(TRED + "Unable to determine the System os. Unable to recover", ENDC)
		message('update node', data)
		return
	ip_addresses = get_ip4_addresses()
	print(ip_addresses)
	print(secondary_ip)
	if secondary_ip:
		print(TGREEN + "Success! Notifying Server...", ENDC)
		updated_data = populate_server_info(ip_addresses)
		message('update node', updated_data)
	else:
		print(TRED + "unable to recover node", ENDC)
		message('update node', data)


@sock.event
def connect():
	ip_addresses = get_ip4_addresses()
	data = populate_server_info(ip_addresses)
	message('join', data)
	print("connected!")


@sock.event
def connect_error():
	print("The connection failed!")
	print("trying to recconnect.")
	await_reconnection_command()

@sock.event
def disconnect():
	tl.stop()
	print("I'm disconnected!")

def reconnect():
	time.sleep(2)
	sock.connect('http://localhost:5000')
	tl.start()

if __name__ == '__main__':
	try:
		print(TLOAD+"initializing Node identity, gathering IP addresses and connecting to Failover Server", ENDC)
		if NODE_ID is False:
			print(TRED+ "ERROR! Could not load Node identity", ENDC)
			print("Initialize the Node identity with environment variable 'NODE_ID'. Look at README.txt for more info.")
			exit()
		while True:
			if not sock.connected:
				reconnect()
			else:
				ping = input("type in disconnect to terminate the session: \t")
				if ping == 'disconnect':
					sock.disconnect()
					await_reconnection_command()
	except KeyboardInterrupt:
		tl.stop()
		print(TLOAD + "KeyboardInterrupt occured.")
		print(TRED + "Disconnecting!", ENDC)
		exit()