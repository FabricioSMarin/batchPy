import socket
from threading import Thread
import os
import time


def check_host(host):
    response = os.system("ping -c 1 " + host)
    # and then check the response...
    if response == 0:
        print(f"{host} is up!")
    else:
        print(f"{host} is down!")

def check_server(host):
    #TODO: check if server running either by PID or by trying to connect to it. function may be redundant.
    pass

def connect_server(host, port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    return client
def get_connected_services():
    #TODO: connected detectors,
    # connected motors
    # monitors (pvs or objects to monitor)
    # PV mail client list (emails to send notifs to)
    #
    pass

def get_queue():
    #TODO: get queue to update gui
    pass
def send_queue():
    #TODO: send queue to update other clients
    pass
def get_scan_status():
    #TODO: get current scan number, is_scanning,
    pass

def begin_scan():
    #TODO: send command to begin next scan in queue
    pass

def abort_scan():
    #TODO: send command to abort scan
    pass

def pause_scan():
    # TODO: send command to pause scan
    pass


HOST = '127.0.0.1'
PORT = 22262
client = connect_server(HOST,PORT)

if client == None:
    print("client not connected")
else:
    client.send(b"test")
    time.sleep(1)
    response = client.recv(10240).decode("utf-8")
    print(response)


