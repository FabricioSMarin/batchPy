from ast import If
import epics
import epics.devices
from epics import caput, caget
import time
import numpy as np
import os
import json
import trajectories
import subprocess
from detectors import *

def before_loop1(params):
    pv_list = [    
        params["positioner1"].VELO, params["positioner1"].VMAX,
        params["positioner1"].VAL, params["l1_center"] - params["l1_width"].VAL/2,
        params["positioner1"].VELO, params["scan_speed"],
        params["hydra_controller"].StartStopCalc.PROC,
    ]
    ready_values = [params["positioner1"].VELO, params["scan_speed"], params["positioner1"].DMOV, 1]
    busy_loop(pv_list, ready_values)
    return

def before_loop2(params):
    setup_detectors(params)
    pv_list = [params["positioner2"].VAL, params["l2_center"] - params["l2_width"].VAL/2]
    ready_values = [params["positioner2"].DMOV, 1]
    busy_loop(pv_list, ready_values)
    return

def before_loop3(params):
    pv_list = [params["positioner3"].VAL, params["l3_center"] - params["l3_width"].VAL/2]
    ready_values = [params["positioner3"].DMOV, 1]
    busy_loop(pv_list, ready_values)
    return

def before_loop4(params):
    pv_list = [params["positioner3"].VAL, params["l3_center"] - params["l3_width"].VAL/2]
    ready_values = [params["positioner3"].DMOV, 1]
    busy_loop(pv_list, ready_values)    
    return  

def after_loop1(params):
    pv_list = [params["positioner1"].VELO, params["positioner1"].VMAX, 
    params["positioner1"].VAL, params["l1_center"] - params["l1_width"].VAL/2]
    ready_values = [params["positioner1"].DMOV, 1]
    busy_loop(pv_list, ready_values)
    return

def after_loop2(params):
    pv_list = [params["positioner2"].VAL, params["l2_center"] - params["l2_width"].VAL/2]
    ready_values = [params["positioner2"].DMOV, 1]
    busy_loop(pv_list, ready_values)
    return

def after_loop3(params):
    pv_list = [params["positioner3"].VAL, params["l3_center"] - params["l3_width"].VAL/2]
    ready_values = [params["positioner3"].DMOV, 1]
    busy_loop(pv_list, ready_values)
    return

def after_loop4(params):
    pv_list = [params["positioner4"].VAL, params["l4_center"] - params["l4_width"].VAL/2]
    ready_values = [params["positioner4"].DMOV, 1]
    busy_loop(pv_list, ready_values)
    return

def run_scan(params):
    #TODO: run this in a separate thread 
    #TODO: monitor scan in a separate thread

    setup_detectors(params)
    global scanning
    global paused
    global abort
    scanning = True
    paused = False
    abort = False
    if params["loop4"] != "":
        run_loopN(params, 4)
    elif params["loop3"] != "":
        run_loopN(params, 3)
    elif params["loop2"] != "":
        run_loopN(params, 2)
    elif params["loop1"] != "":
        run_loopN(params, 1)
    else:   
        print("no loop to run")
    
    while scanning:
        time.sleep(2)
        if abort:
            print("scan aborted")   
            break
    print("scan done")

def run_loopN(params, N):   
    while paused:
        time.sleep(2)
    if abort:
        return
        
    globals()[f'before_loop{N}'](params)

    if params["scan_type"] == "fly":
        if N==1:
            end_pos = params[f"l{N}_center"].VAL + params[f"l{N}_width"].VAL/2
            trigger_detectors(params)
            epics.caput(params[f"positioner{N}"], end_pos)

        elif N>1:
            params["scan_type"] = "step"

    if params["scan_type"] == "step":
        positions = np.arange(params[f"l{N}_center"].VAL - params[f"l{N}_width"]/2, 
        params[f"l{N}_center"].VAL + params[f"l{N}_width"]/2, 
        params[f"l{N}_size"].VAL)
        for pos in positions:
            epics.caput(params[f"positioner{N}"], pos)
            trigger_detectors(params)
            if N>1:
                run_loopN(params, N-1)
            elif N==1:
                time.sleep(params["dwell_time"].VAL)
            else:
                print("not sure how to handle this")
                return False

    print(f"loop{N} done")
    return

def busy_loop(pv_list,ready_values):
    ready = False
    while not ready:
        for i in range(1,len(pv_list)):
            epics.caput(pv_list[i-1], pv_list[i])
        time.sleep(0.25)
        ready = pvs_ready(ready_values)
    return
    
def pvs_ready(ready_values):
    ready = True
    for i in range(1,len(ready_values)):
        if epics.caget(ready_values[i-1]) != ready_values[i]:
            ready = False
            break
    return ready