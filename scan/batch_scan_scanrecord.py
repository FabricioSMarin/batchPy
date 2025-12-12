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
#TODO: duplicate calc record functionality to setup dtectors, triggers, etc. 
#TODO: create an identical funcitonality that does not use scan record plan. 

def before_loop1(params):
    pv_list = [    
        params["positioner1"].VELO, params["positioner1"].VMAX,
        params["positioner1"].VAL, params["l1_center"] - params["l1_width"].VAL/2,
        params["positioner1"].VELO, params["scan_speed"],
        params["hydra_controller"].StartStopCalc.PROC,
    ]
    ready_values = [params["positioner1"].VELO, params["scan_speed"],params["positioner1"].DMOV, 1]
    busy_loop(params, 1, pv_list, ready_values)
    return

def before_loop2(params):
    pv_list = [params["positioner2"].VAL, params["l2_center"] - params["l2_width"].VAL/2]
    ready_values = [params["positioner2"].DMOV, 1]
    busy_loop(params, 2, pv_list, ready_values)
    return

def before_loop3(params):
    pv_list = [params["positioner3"].VAL, params["l3_center"] - params["l3_width"].VAL/2]
    ready_values = [params["positioner3"].DMOV, 1]
    busy_loop(params, 3, pv_list, ready_values)
    return

def before_loop4(params):
    pv_list = [params["positioner4"].VAL, params["l4_center"] - params["l4_width"].VAL/2]
    ready_values = [params["positioner4"].DMOV, 1]
    busy_loop(params, 4, pv_list, ready_values)    
    return  

def after_loop1(params):
    pv_list = [params["positioner1"].VELO, params["positioner1"].VMAX, 
    params["positioner1"].VAL, params["l1_center"] - params["l1_width"].VAL/2]
    ready_values = [params["positioner1"].DMOV, 1]
    busy_loop(params, 1, pv_list, ready_values)
    return

def after_loop2(params):
    pv_list = [params["positioner2"].VAL, params["l2_center"] - params["l2_width"].VAL/2]
    ready_values = [params["positioner2"].DMOV, 1]
    busy_loop(params, 2, pv_list, ready_values)
    return

def after_loop3(params):
    pv_list = [params["positioner3"].VAL, params["l3_center"] - params["l3_width"].VAL/2]
    ready_values = [params["positioner3"].DMOV, 1]
    busy_loop(params, 3, pv_list, ready_values)
    return

def after_loop4(params):
    pv_list = [params["positioner4"].VAL, params["l4_center"] - params["l4_width"].VAL/2]
    ready_values = [params["positioner4"].DMOV, 1]
    busy_loop(params, 4, pv_list, ready_values)
    return

def run_scan(params):
    #TODO: monitor scan in a separate thread
    global scanning
    global paused
    global abort
    scanning = True
    paused = False
    abort = False
    setup_scan_record(params)
    setup_detectors(params)

    if params["loop4"] != "":
        N=4 
    elif params["loop3"] != "":
        N=3
    elif params["loop2"] != "":
        N=2
    elif params["loop1"] != "":
        N=1
    else:   
        return
    for i in range(1, N+1):
        epics.camonitor(params[f"before_busy{i}.VAL"], globals()[f'before_loop{i}'])
        epics.camonitor(params[f"after_busy{i}.VAL"], globals()[f'after_loop{i}'])
    run_loopN(params, N) #TODO: run in a separate thread

    scanning = True
    while scanning:
        time.sleep(2)
        scanning  = epics.caget(params[f"loop{N}.BUSY"])
        if abort:
            print("scan aborted")   
            if scanning:
                epics.caput(params[f"loop{N}.ABORT"], 1)
                epics.caput(params[f"loop{N}.ABORT"], 1)
                epics.caput(params[f"loop{N}.ABORT"], 1)

    for i in range(1, N+1):
        epics.camonitor(params[f"before_busy{i}.VAL"], None)
        epics.camonitor(params[f"after_busy{i}.VAL"], None)
    print("scan done")

def run_loopN(params, N):
    while paused:
        time.sleep(2)
    if abort:
        return
    epics.caput(params[f"loop{N}.EXSC"], 1)
    return

def busy_loop(params, N, pv_list,ready_values):
    ready = False
    while not ready:
        for i in range(1,len(pv_list)):
            epics.caput(pv_list[i-1], pv_list[i])
        time.sleep(0.25)
        ready = pvs_ready(ready_values)

    epics.caput(params[f"loop{N}.EXSC"], 0)
    return

def pvs_ready(ready_values):
    ready = True
    for i in range(1,len(ready_values)):
        if epics.caget(ready_values[i-1]) != ready_values[i]:
            ready = False
            break
    return ready