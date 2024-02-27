import redis

from rq import Queue, Worker
from redis import Redis

import time
import batch_backend
import subprocess
import os
import pickle
import datetime
import epics
from datetime import datetime, timedelta


class rqs(object):
    def __init__(self):
        self.threads = {}
        self.pid = None
        self.backend = batch_backend.BatchScan()
        self.settings = self.open_settings()
        self.r = None
        self.scan_id = 0

    def start_server(self, host, port, confile="redis.conf"):
        #check if server running
        self.r = redis.Redis(host=host, port=port, decode_responses=True, socket_connect_timeout=1)  # short timeout for the test
        try:
            self.r.ping()
            print("redis server: {}".format(addr))
        except:
            print("redis server not running, starting server...")
            command = "redis-server {}".format(confile)
            subprocess.Popen([command], shell=True)
        return
    def connect_server(self, host, port):
    	self.r = redis.Redis(host=host, port=port, decode_responses=True, socket_connect_timeout=1)  

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

    def open_settings(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))+"/"
        fname = "default_settings.pkl"
        valid_files = []
        #check if files are .pkl and contain "settings" keyword.
        for i, file in enumerate(os.listdir(current_dir)):
            if file.endswith(".pkl"):
                with open(current_dir+file,'rb') as f:
                    contents = pickle.load(f)
                    if contents[0] == "settings":
                        valid_files.append(file)
                    f.close()
        #if no  valid files exist, create new one.
        if len(valid_files) ==0:
            settings = {}
            for key in self.var_dict:
                settings.append(key.text())
            with open(current_dir + fname, 'wb') as f:
                pickle.dump(["settings",settings], f)
                f.close()
        with open(current_dir + fname,'rb') as f:
            contents = pickle.load(f)
            settings = contents[1]
        return settings

    def save_settings(self):
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

    def open_batches(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))+"/"
        fname = "batch_list.pkl"
        valid_files = []
        #check if files are .pkl and contain "batch_list" keyword.
        for i, file in enumerate(os.listdir(current_dir)):
            if file.endswith(".pkl"):
                with open(current_dir+file,'rb') as f:
                    contents = pickle.load(f)
                    if contents[0] == "batch_list":
                        valid_files.append(file)
                    f.close()
        #if no  valid files exist, create new one.
        if len(valid_files) ==0:
            batch_list = {}
            for key in self.var_dict:
                batch_list.append(key.text())
            with open(current_dir + fname, 'wb') as f:
                pickle.dump(["batch_list",batch_list], f)
                f.close()
        with open(current_dir + fname,'rb') as f:
            contents = pickle.load(f)
            batch_list = contents[1]
        return batch_list
        pass

    def save_batches(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))+"/"
        valid_files = []
        for i, file in enumerate(os.listdir(current_dir)):
            if file.endswith(".pkl"):
                with open(current_dir+file,'rb') as f:
                    contents = pickle.load(f)
                    if contents[0] == "batch_list":
                        valid_files.append(file)
                    f.close()
        #use latest file
        fname = max(valid_files, key=os.path.getmtime)
        with open(current_dir + fname, 'wb') as f:
            pickle.dump(["batch_list",self.pv_dict], f)
            f.close()
            return

    def save_event_log(self):
        #TODO update/save log
        pass

    def connected_clients(self):
        clients = self.r.client_list()
        #TODO: parse ip addrs only
        return self.r.client_list()

    def remove_from_q(self,scan_id):
        qfail = Queue("failed", connection=Redis())
        qfail.count
        qfail.empty()

    def rearange_q(self,scan_id1, scan_id2):
        pass

    def clear_q(self):
        pass

    def add_to_q(self,params):
        valid = self.validate_params(params)
        if valid:
            queue = Queue(connection=self.r)
            job = queue.enqueue(self.backend.run_scan, params)
            scan_id = self.generate_scan_id()
            eta = self.get_eta(params)

        return scan_id, eta

    def get_scan_eta(self,params):
        #TODO: calculate eta based on params
        pass

    def generate_scan_id(self):
        #TODO: increase scan id counter, add new id and scan to database self.save_batches()
        pass

    def begin_scan(self):
        #TODO: start next job in queue
        pass

    def pause_scan(self):
        #TODO: send current job a "wait=1" condition
        pass

    def resume_scan(self):
        #TODO: send current job a "wait=0" condition
        pass

    def abort_scan(self):
        #TODO: quit current job, set scan status to "aborted"
        # stop workers
        pass

    def change_settings(self):
        #TODO: apply PV settings and re-init batch_backend
        pass

    def get_current_scan(self):
        #TODO: returns scan_id, Next scan in queue if idle, none if nothing queued
        pass

    def get_scan_params(self,scan_id):
        #TODO: returns params dictionary with param keys: value
        pass

    def get_trajectory(self,scan_id):

        pass

    def get_progress(self, scan_id):
        pass

    def get_scan_eta(self,scan_id):
        pass

    def get_total_eta(self):
        pass

    def get_device_status(self):
        pass

    def get_queue(self):
        pass

    
