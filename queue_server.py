import redis

from rq import Queue, Worker
from redis import Redis
import numpy as np
import time
import batch_backend
import subprocess
import os
import pickle
import epics
from datetime import datetime, timedelta


class rqs(object):
    def __init__(self):
        self.backend = batch_backend.BatchScan()
        self.settings = self.open_settings()
        self.r = None
        self.scan_id = 0
        self.start_listening()

    def start_listening(self):
        while True: 
            time.sleep(2)
            commands = self.r.get("commands")
            #first in first out
            next_command = commands[0]

    def start_server(self, host, port, confile="redis.conf"):
        #check if server running
        self.r = redis.Redis(host=host, port=port, decode_responses=True, socket_connect_timeout=1)  # short timeout for the test
        try:
            if self.r.ping():
                print("redis server: {}".format(host))
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
            settings["server_addr"] = None
            settings["scan_generator"] = None
            settings["before_inner_loop"] = None
            settings["after_inner_loop"] = None
            settings["before_outer_loop"] = None
            settings["after_outer_loop"] = None
            settings["delay_calc"] = None
            settings["save_data_path"] = None
            settings["scan_inner"] = None
            settings["scan_outer"] = None
            settings["det1"] = None
            settings["det2"] = None
            settings["det3"] = None
            settings["det4"] = None
            settings["x_motor"] = None
            settings["y_motor"] = None
            settings["r_motor"] = None
            settings["profile_move"] = None
            settings["softgluezynq"] = None

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
            pickle.dump(["settings",self.settings], f)
            f.close()
            return

    def save_event_log(self):
        #TODO update/save log
        pass

    def remove_from_q(self,scan_id):
        qfail = Queue("failed", connection=Redis())
        qfail.count
        qfail.empty()

    def rearange_q(self,scan_id1, scan_id2):
        pass

    def clear_q(self):
        pass

    def get_q(self):
        pass

    def add_to_q(self,params):
        valid, msg = self.validate_params(params)
        if valid:
            q = Queue(connection=self.r)
            job = q.enqueue(self.backend.run_scan, params)
            scan_id = self.generate_scan_id()
            eta = self.get_eta(params)
        else:
            return None, None, msg
        return scan_id, eta, msg

    def open_q(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))+"/"
        fname = "q_list.pkl"
        valid_files = []
        #check if files are .pkl and contain "q_list" keyword.
        for i, file in enumerate(os.listdir(current_dir)):
            if file.endswith(".pkl"):
                with open(current_dir+file,'rb') as f:
                    contents = pickle.load(f)
                    if contents[0] == "q_list":
                        valid_files.append(file)
                    f.close()
        #if no  valid files exist, create new one.
        if len(valid_files) ==0:
            q_list = {}
            for key in self.var_dict:
                q_list.append(key.text())
            with open(current_dir + fname, 'wb') as f:
                pickle.dump(["q_list",q_list], f)
                f.close()
        with open(current_dir + fname,'rb') as f:
            contents = pickle.load(f)
            q_list = contents[1]
        return q_list


    def save_q(self):
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

    def validate_params(self,params):
        #TODO: check motor position limts
        # check motor velocity limits 
        # check motor acceleration limits ** (if profile move and if accel limit exists), return as warning, but permit scan 
        try:
            limits = self.get_motor_limits(self.settings["x_motor"],self.settings["y_motor"],self.settings["r_motor"])
        except: 
            print("one or more motor not connected or invalid PV")
        x_valid = True
        y_valid = True
        r_valid = True

        for param in params.keys():
            if params["generator"] == "scan_record":
                if param == "x_width:": 
                    x_valid = params["x_center"] + params["x_width"]/2 < limits["x_pos_lim"] and \
                                params["x_center"] - params["x_width"]/2 > limits["x_neg_lim"] and \
                                params["x_step"] / params["dwell"] * 1000 < limits["x_vel"]
                    
                if param == "y_width":
                    y_valid = params["y_center"] + params["y_width"]/2 > limits["y_pos_lim"] and \
                                params["y_center"] - params["y_center"]/2 > limits["y_neg_lim"]

                if param == "r_width":
                    r_valid = params["r_center"] + params["r_width"]/2 > limits["r_pos_lim"] and \
                                params["r_center"] - params["r_width"]/2 > limits["r_neg_lim"]
                    
            if params["generator"] == "profile_move":
                x_pos, y_pos, time_arr = self.generate_trajectory(params)
                x_vel, y_vel = self.calculate_velo(x_pos, y_pos, time_arr)
                x_accel, y_accel = self.calculate_accel(x_vel, y_vel)

                if param == "x_width:": 
                    x_valid = (x_pos<limits["x_pos_lim"]).any() & (np.abs(x_vel)<limits["x_velo"]).any() & (np.abs(x_accel)<limits["x_acc"]).any()

                if param == "y_width":
                    y_valid = (y_pos<limits["y_pos_lim"]).any() & (np.abs(y_vel)<limits["y_velo"]).any() & (np.abs(y_accel)<limits["y_acc"]).any()

                if param == "r_width":
                    r_valid = params["r_center"] + params["r_width"]/2 > limits["r_pos_lim"] and \
                                params["r_center"] - params["r_width"]/2 > limits["r_neg_lim"]
            msg = "X: {}, Y: {}, R: {}".format(x_valid, y_valid, r_valid)
            valid = x_valid & y_valid & r_valid
        return valid, msg
    
    def get_motor_limits(self,x_motor=None, y_motor=None, r_motor=None):
        limits = {}
        limits["x_pos_lim"] = None
        limits["x_neg_lim"] = None
        limits["x_vel"] = None
        limits["x_acc"] = None
        limits["y_pos_lim"] = None
        limits["y_neg_lim"] = None
        limits["y_vel"] = None
        limits["y_acc"] = None
        limits["r_pos_lim"] = None
        limits["r_neg_lim"] = None
        limits["r_vel"] = None
        limits["r_acc"] = None

        #TODO: make motor into ophyd or MOTOR object to be able to get all settings related to it without individual epicsget calls
        if x_motor is not None: 
            limits["x_pos_lim"] = None
            limits["x_neg_lim"] = None
            limits["x_vel"] = None
            limits["x_acc"] = None

        if x_motor is not None: 
            limits["x_pos_lim"] = None
            limits["x_neg_lim"] = None
            limits["x_vel"] = None
            limits["x_acc"] = None

        if x_motor is not None: 
            limits["x_pos_lim"] = None
            limits["x_neg_lim"] = None
            limits["x_vel"] = None
            limits["x_acc"] = None
        
        return limits

    def get_scan_eta(self,params):
        #TODO: calculate eta based on params
        pass

    def get_total_eta(self):
        pass

    def generate_scan_id(self):
        #TODO: increase scan id counter, add new id and scan to database self.save_q()
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

    def get_device_status(self):
        pass

    def get_connected_clients(self):
        clients = self.r.client_list()
        #TODO: parse ip addrs only
        return self.r.client_list()

    
