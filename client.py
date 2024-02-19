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

    def get_scan_progress(self):
        #TODO: send command to get scan progress
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

    def get_motor_limits(self):
        try:
            #TODO: send "get_motor_limits" command, parse string, and update limits
            x_hlm = self.backend.x_motor.HLM
            x_llm = self.backend.x_motor.LLM
            x_vmax = self.backend.x_motor.VMAX
            x_vmin = self.backend.x_motor.VBAS
            x_res = self.backend.x_motor.MRES
            y_hlm = self.backend.y_motor.HLM
            y_llm = self.backend.y_motor.LLM
            y_res = self.backend.y_motor.MRES
            if self.backend.r == "empty":
                r_llm = -1000
                r_hlm = 1000
            else:
                r_llm = self.backend.r_motor.LLM
                r_hlm = self.backend.r_motor.HLM

            lines = [vars(self.gui)[i] for i in self.gui.line_names]
            for line in lines:
                line.x_hlm = x_hlm
                line.x_llm = x_llm
                line.x_vmax = x_vmax
                line.x_vmin = x_vmin
                line.x_res = x_res
                line.y_hlm = y_hlm
                line.y_llm = y_llm
                line.y_res = y_res
                line.r_llm = r_llm
                line.r_hlm = r_hlm
        except Exception as e:
            print(e)
            pass

