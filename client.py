import socketio
import socket
import os
import time
import uuid
from netifaces import interfaces, ifaddresses, AF_INET

from timeloop import Timeloop
from datetime import timedelta

tl = Timeloop()
sock = socketio.Client()
TGREEN = '\033[32m' # Green Text
TRED = '\033[31m' # Red Text
TLOAD = '\033[33m'
ENDC = '\033[m'
ip_addr = '127.0.0.1'
secondary_ip = False

# Node identity
NODE_ID = int(os.environ.get('NODE_ID', False))


@tl.job(interval=timedelta(seconds=2))
def sample_job_every_2s():
	if sock.connected:
		message('ping', None)


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


def ip4_addresses():
	ip_list = []
	global secondary_ip
	secondary_ip = False
	for interface in interfaces():
		for addr_fam, link in ifaddresses(interface).items():
			if addr_fam == AF_INET and 'docker' not in interface and 'lo' not in interface:
				address = {'interface': interface, 'address': link[0]['addr'], 'netmask': link[0]['netmask']}
				if interface == 'wlp6s0' or interface == 'eth0':
					ip_addr = link[0]['addr']
					ip_list.append({interface: ip_addr})
				if interface ==	'wlp6s0:1' or interface ==	'eth0:1':
					secondary_ip = True
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
	print("Recovering Node "+ str(data['recovery_node']) + "...")
	print(TLOAD + "creating virtual IP address: " + data['ip'])
	secondary_ip = data['ip']
	print(TGREEN + "Success! Notifying Server...", ENDC)
	return True, NODE_ID, secondary_ip

@sock.event
def connect():
	hostname = socket.gethostname()
	address_list = ip4_addresses()
	neighbors = get_neighbors(NODE_ID)
	data = {
		"mac": uuid.getnode(),
		"pid": os.getpid(),
		"system": hostname,
		"NODE_ID": NODE_ID,
		"neighbors": neighbors,
		"primary_ip": ip_addr,
		"secondary_ip": secondary_ip,
		"additional_network_info": address_list
	}
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