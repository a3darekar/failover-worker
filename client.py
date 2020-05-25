import socketio
import socket
import os
import time
import uuid
from netifaces import interfaces, ifaddresses, AF_INET


sock = socketio.Client()
TRED =  '\033[31m' # Red Text
ENDC = '\033[m'
ip_addr = '127.0.0.1'
secondary_ip = False

def ip4_addresses():
	ip_list = []
	global secondary_ip
	secondary_ip = False
	for interface in interfaces():
		for addr_fam, link in ifaddresses(interface).items():
			if addr_fam == AF_INET and 'docker' not in interface and 'lo' not in interface:
				print(interface, link[0])
				address = {'interface': interface, 'address': link[0]['addr'], 'netmask': link[0]['netmask']}
				if interface == 'wlp6s0' or interface == 'eth0':
					ip_addr = link[0]['addr']
				if interface ==	'wlp6s0:1' or interface ==	'eth0:1':
					print(interface)
					secondary_ip = True
	return ip_list

def message(event, data):
	sock.emit(event, data)

def await_reconnection_command():
	while True:
		reconnect_request = input("attempt reconnection? (y|Y): \t")
		if reconnect_request == 'Y' or 'y':
			return True

@sock.on('slack')
def on_message(data):
	print("Received message from server << ", data)


@sock.on('slack')
def on_message(data):
	print(data)

@sock.event
def connect():
	print("connected!")
	hostname = socket.gethostname()
	address_list = ip4_addresses()
	print(uuid.getnode())
	data = {
		"mac": uuid.getnode(),
		"pid": os.getpid(),
		"system": hostname,
		"primary_ip": ip_addr,
		"secondary_ip": secondary_ip,
		"additional_network_info": address_list
	}
	message('join', data)

@sock.event
def connect_error():
	print("The connection failed!")
	print("trying to recconnect.")
	await_reconnection_command()

@sock.event
def disconnect():
	print("I'm disconnected!")

def reconnect():
	time.sleep(2)
	sock.connect('http://localhost:5000')

if __name__ == '__main__':
	try:
		while True:
			if not sock.connected:
				reconnect()
				print('connected with sid: ', sock.sid)
			else:
				ping = input("Enter message for server: \t")
				if ping != 'disconnect':
					message('convo', ping)
				else:
					sock.disconnect()
					await_reconnection_command()
	except KeyboardInterrupt:
		print(TRED + "KeyboardInterrupt occured Disconnecting!", ENDC)
		exit()