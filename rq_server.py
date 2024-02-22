import redis
from rq import Queue, Worker
import time
import batch_backend
import subprocess
import os
import pickle
import datetime
import epics

#TODO:
# check if clients still connected by having client regularly send ping request as a heartbeat,
#   if no heartbeat received after X seconds, close that connection, terminate that thread, and remove thread from threads
#  startup server remotely
#  server check when client disconnects.

'''
open_config
save_config

open_session
save_session

save_event_log
save_scan_log
'''

class rqServer(object):
    def __init__(self):
        self.threads = {}
        self.pid = None
        self.backend = batch_backend.BatchScan()
        pv_dict = self.open_config()
        self.cage_pvs(pv_dict)

    def init_server(self, addr, port, confile="redis.conf"):
        #check if server running
        r = redis.Redis(host=addr, port=port, decode_responses=True, socket_connect_timeout=1)  # short timeout for the test
        try:
            r.ping()
            print("redis server: {}".format(addr))
        except:
            print("redis server not running, starting server...")
            command = "redis-server {}".format(confile)
            self.command_detatch(command)

        r = redis.Redis(host=addr, port=port, decode_responses=True, socket_connect_timeout=1)  # short timeout for the test



        #TODO:
        # open settings_file {key: PV_name}
        # start listening for new connections.
        pass

    def command_detatch(self, command):
        # subprocess.call("{}python", "{}server.py".format(python_path,cwd), shell=True)
        # TODO: check if this starts and detaches from main process.
        subprocess.Popen([command], shell=True)
        return

    def open_config(self):
        #TODO: get PV config file
        current_dir = os.path.dirname(os.path.abspath(__file__))+"/"
        valid_files = []
        last_opened = []
        #check if files are .pkl and contain "settings" keyword.
        for i, file in enumerate(os.listdir(current_dir)):
            if file.endswith(".pkl"):
                with open(current_dir+file,'rb') as f:
                    contents = pickle.load(f)
                    if contents[0] == "settings":
                        last_opened.append(contents[1])
                        valid_files.append(file)
                    f.close()
        #if no  valid files exist, create new one.
        if len(valid_files) ==0:
            fname = "default_settings.pkl"
            settings = {}
            for key in self.var_dict:
                settings.append(key.text())
            with open(current_dir + fname, 'wb') as f:
                pickle.dump(["settings",datetime.now(),settings], f)
                f.close()
                return
        #if file does exist,
        else:
            #check which settings file is last opened, open that one.
            most_recent_file = valid_files[last_opened.index(max(last_opened))]
            with open(current_dir+most_recent_file,'rb') as f:
                contents = pickle.load(f)
                settings = contents[2]
        return settings

    def caget_pvs(self,pv_dict):
        for key in pv_dict:
            epics.caget(key, timeout=0.3)