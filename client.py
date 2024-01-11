import socket
from threading import Thread
import os
import time
import pickle

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
    client.connect((host, port))
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

def get_test_array():
    pass

def get_test_dict():
    client.send(b"get_test_dict")
    msg = client.recv(1024)
    data_arr = pickle.loads(msg)
    print('Received', data_arr)

hostname = socket.gethostname()
HOST = socket.gethostbyname(hostname)
PORT = 22262
is_connected = True
try:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    client.settimeout(5)

except socket.timeout:
    print("connection timed out")
    is_connected = False

except Exception as error:
    print(error)
    print("client not connected")
    is_connected = False

while is_connected:
    try:
        if client == None:
            break
        message = input("enter message: ")
        message = pickle.dumps(message)
        client.send(message)
        time.sleep(1)
        response = client.recv(1024)
        response = pickle.loads(response)
        print(response)
        if response == "disconnecting client" or "stopping server":
            break

    except socket.timeout:
        print("timeout")
        break
client.close()

