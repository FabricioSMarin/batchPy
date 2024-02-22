import redis
from rq import Queue, Worker
import time
import batch_backend
import subprocess
import os
import pickle
import datetime
import epics
from datetime import datetime, timedelta

#TODO:
#  server check when client disconnects.

'''
TODO
open_session
save_session

save_event_log
save_scan_log

get_connected_clients
'''

class rqServer(object):
    def __init__(self):
        self.threads = {}
        self.pid = None
        self.backend = batch_backend.BatchScan()
        pv_dict = self.open_config()
        self.pv_dict = self.caget_pvs(pv_dict)
        self.r = None

    def start_server(self, addr, port, confile="redis.conf"):
        #check if server running
        r = redis.Redis(host=addr, port=port, decode_responses=True, socket_connect_timeout=1)  # short timeout for the test
        try:
            r.ping()
            print("redis server: {}".format(addr))
        except:
            print("redis server not running, starting server...")
            command = "redis-server {}".format(confile)
            subprocess.Popen([command], shell=True)
        return

    def caget_pvs(self,pv_dict):
        for pv in pv_dict.keys():
            try:
                value = epics.caget(pv, as_string=True,connection_timeout=0.05,use_monitor=False)
            except:
                value = None

            if value == None:
                pv_dict[pv] = [False,value]
            else:
                pv_dict[pv] = [True,value]
        return pv_dict

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

    def save_config(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))+"/"
        valid_files = []
        for i, file in enumerate(os.listdir(current_dir)):
            if file.endswith(".pkl"):
                with open(current_dir+file,'rb') as f:
                    contents = pickle.load(f)
                    if contents[0] == "settings":
                        valid_files.append(file)
                    f.close()
        #use latest file
        fname = max(valid_files, key=os.path.getmtime)
        with open(current_dir + fname, 'wb') as f:
            pickle.dump(["settings",datetime.now(),self.pv_dict], f)
            f.close()
            return

    def connected_clients(self):
        clients = self.r.client_list()
        #TODO: parse ip adds only
        return self.r.client_list()