import socket
from threading import Thread
import os
import time
import pickle

class BatchClient(object):
    def __init__(self):
        # self.stop = False
        self.threads = {}
        self.cli = None
        self.connected = False

    def check_host(self, host):
        response = os.system("ping -c 1 " + host)
        # and then check the response...
        if response == 0:
            print(f"{host} is up!")
        else:
            print(f"{host} is down!")

    def check_server(self,host):
        #TODO: check if server running either by PID or by trying to connect to it. function may be redundant.
        pass

    def connect_server(self, host, port):
        try:
            self.cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.cli.connect((host, port))
            self.cli = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.cli.connect((host, port))
            self.cli.settimeout(5)
            self.connected = True
            print("client connected")

        except socket.timeout:
            print("connection timed out")
            self.connected = False
            self.cli.close()
        except Exception as error:
            self.connected = False
            self.cli.close()
            print(error)
            print("client not connected")
        return

    def get_connected_services(self):
        #TODO: connected detectors,
        # connected motors
        # monitors (pvs or objects to monitor)
        # PV mail client list (emails to send notifs to)
        #
        pass

    def get_queue(self):
        #TODO: get queue to update gui
        pass

    def send_queue(self):
        #TODO: send queue to update other clients
        pass

    def get_scan_status(self):
        #TODO: get current scan number, is_scanning,
        pass

    def begin_scan(self):
        #TODO: send command to begin next scan in queue
        pass

    def abort_scan(self):
        #TODO: send command to abort scan
        pass

    def pause_scan(self):
        # TODO: send command to pause scan
        pass

    def get_test_array(self):
        pass

    # def get_test_dict(self):
    #     client.send(b"get_test_dict")
    #     msg = client.recv(1024)
    #     data_arr = pickle.loads(msg)
    #     print('Received', data_arr)


