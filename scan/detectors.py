import epics
import numpy as np
import time

def setup_scan_record_fly(outer, inner, before_out, before_in, after_out, after_in, npts, num_lines, struck, xmap, xspress3, disable_calcs=[]):
    for i in range(len(disable_calcs)):
        epics.caput(f"{disable_calcs[i]}Enable",0, wait=True)
        epics.caput(f"{disable_calcs[i]}.SCAN",0, wait=True)

    epics.caput(f"{outer}.BSWAIT",0, wait=True)
    epics.caput(f"{inner}.BSWAIT",0, wait=True)
    epics.caput(f"{outer}.ASWAIT",0, wait=True)
    epics.caput(f"{inner}.ASWAIT",0, wait=True)
    epics.caput(f"{inner}.NPTS",npts, wait=True)
    epics.caput(f"{inner}.BSPV",before_in, wait=True)
    epics.caput(f"{outer}.BSPV",before_out, wait=True)
    epics.caput(f"{inner}.ASPV",after_in, wait=True)
    epics.caput(f"{outer}.ASPV",after_out, wait=True)
    epics.caput(f"{outer}.NPTS",num_lines, wait=True)
    epics.caput(f"{outer}.R1PV","time", wait=True)
    epics.caput(f"{inner}.R1PV","time", wait=True)
    epics.caput(f"{outer}.P1PV","", wait=True)
    epics.caput(f"{inner}.P1PV","", wait=True)
    epics.caput(f"{inner}.T1PV","", wait=True)
    epics.caput(f"{inner}.T2PV","", wait=True)
    epics.caput(f"{inner}.T3PV","", wait=True)
    epics.caput(f"{outer}.T3PV","", wait=True)
    epics.caput(f"{outer}.T4PV",f"{inner}.EXSC", wait=True)

    if struck is not None:
        epics.caput(f"{inner}.T4PV",f"{struck}:EraseStart", wait=True)
    else:
        epics.caput(f"{inner}.T4PV","", wait=True)
    if xmap is not None:
        epics.caput(f"{outer}.T1PV",f"{xmap}:netCDF1:Capture", wait=True)
        epics.caput(f"{outer}.T2PV",f"{xmap}:EraseStart", wait=True)
    else:
        epics.caput(f"{inner}.T1PV","", wait=True)
        epics.caput(f"{inner}.T2PV","", wait=True)
    if xspress3 is not None:
        epics.caput(f"{xspress3}:det1:NumImages",npts, wait=True)
        epics.caput(f"{xspress3}:det1:TriggerMode", 1, wait=True) #3=TTL Veto Only, 1=Internal Trigger
        epics.caput(f"{xspress3}:HDF1:AutoNumber",1, wait=True)
        epics.caput(f"{xspress3}:HDF1:FileNumber",0, wait=True)
        epics.caput(f"{inner}.T1PV",f"{xspress3}:HDF1:Capture", wait=True)
        epics.caput(f"{inner}.T2PV",f"{xspress3}:det1:Acquire", wait=True)
        epics.caput(f"{xspress3}:HDF1:FileTemplate", "%s%s_%04d.h5", wait=True)
    else:
        epics.caput(f"{inner}.T1PV","", wait=True)
        epics.caput(f"{inner}.T2PV","", wait=True)

def setup_scan_record_step(outer, inner, before_out, before_in, after_out, after_in, npts, num_lines, struck, xmap, xspress3, disable_calcs=[]):
    for i in range(len(disable_calcs)):
        epics.caput(f"{disable_calcs[i]}Enable",0, wait=True)
        epics.caput(f"{disable_calcs[i]}.SCAN",0, wait=True)

    epics.caput(f"{outer}.BSWAIT",0, wait=True)
    epics.caput(f"{inner}.BSWAIT",0, wait=True)
    epics.caput(f"{outer}.ASWAIT",0, wait=True)
    epics.caput(f"{inner}.ASWAIT",0, wait=True)
    epics.caput(f"{inner}.NPTS",npts, wait=True)
    epics.caput(f"{inner}.BSPV",before_in, wait=True)
    
def setup_xmap_step(params):
    pass
def setup_tetramm_step(params):
    pass
def setup_xspress3_step(params):
    pass
def setup_struck_step(params): #not used for step scans
    pass
def setup_eiger_step(params):
    pass
def setup_interferometer_step(params):
    pass
def setup_scaler_step(params):
    pass
def setup_tetramm_fly(params):
    pass

def setup_triggers(params):
    pass

def setup_hydra_controller(params):
    params["hydra_controller"].StartPosition.VAL = params["motors"]["x"].VAL + params["step_size"]
    params["hydra_controller"].EndPosition.VAL = params["motors"]["x"].VAL + params["width"]
    params["hydra_controller"].NumTriggers.VAL = params["loop1"].NPTS - 1
    return

def setup_xmap_fly(params):
    npts = params["loop1"].NPTS
    nbuffs = np.ceil((npts)/124)
    epics.caput(f"{params["xmap"]}:PixelsPerRun",npts, wait=True)
    epics.caput(f"{params["xmap"]}:netCDF1:NumCapture",nbuffs, wait=True)
    epics.caput(f"{params["xmap"]}:netCDF1:Capture",0, wait=True)
    epics.caput(f"{params["xmap"]}:StopAll",1, wait=True)
    epics.caput(f"{params["xmap"]}:CollectMode", 1, wait=True)
    return

def setup_xspress3_fly(params):
    npts = params["loop1"].NPTS
    epics.caput(f"{params["xspress3"]}:NumImages",npts, wait=True)
    epics.caput(f"{params["xspress3"]}:det1:TriggerMode", 1, wait=True) #3=TTL Veto Only, 1=Internal Trigger
    epics.caput(f"{params["xspress3"]}:HDF1:AutoNumber",1, wait=True)

def setup_struck_fly(params):
    npts = params["loop1"].NPTS
    epics.caput(f"{params["struck"]}:ChannelAdvance",1, wait=True)
    epics.caput(f"{params["struck"]}:PresetReal",0.0, wait=True)
    epics.caput(f"{params["struck"]}:NuseAll",npts-2, wait=True)
    epics.caput(f"{params["struck"]}:Prescale",1, wait=True)
    epics.caput(f"{params["struck"]}:EraseAll",1, wait=True)
    return

def setup_eiger_fly(params):
    pass

def setup_interferometer_fly(params):
    pass

def setup_scaler_fly(params):
    pass

def before_scan(scanum, filename_PV, dwell_PV, xmap, xspress3, struck, npts):
    #setting up filename
    scan_num = epics.caget(f"{scanum}")
    beamline =f"{scanum.split(':')[0]}"
    fname_prefix = epics.caget(f"{filename_PV}")
    name = f"{fname_prefix}_{beamline}_{scan_num:04d}_"
    dwell = epics.caget(f"{dwell_PV}")/1000
    # prescale =np.abs(step_size/motor_resolution) #Note: this value may differ depending on motor pulse source/stepsize
    prescale = 1

    if xmap is not None:
        nbuffs = np.ceil(npts/124)
        epics.caput(f"{xmap}:netCDF1:Capture",0, wait=True)
        epics.caput(f"{xmap}:StopAll",1, wait=True)
        epics.caput(f"{xmap}:netCDF1:FileName", f"{name}XMAP", wait=True)
        epics.caput(f"{xmap}:netCDF1:FileNumber",0, wait=True)
        epics.caput(f"{xmap}:CollectMode", 1, wait=True)
        epics.caput(f"{xmap}:PixelsPerRun",npts-2, wait=True)
        epics.caput(f"{xmap}:netCDF1:NumCapture",nbuffs, wait=True)
    if xspress3 is not None:
        epics.caput(f"{xspress3}:det1:NumImages",npts, wait=True)
        epics.caput(f"{xspress3}:det1:AcquireTime",epics.caget(f"{dwell_PV}")/1000, wait=True)
        epics.caput(f"{xspress3}:HDF1:FileNumber",0, wait=True)
        epics.caput(f"{xspress3}:HDF1:FileName", f"{name}XSPRESS3", wait=True)
    if struck is not None:
        epics.caput(f"{struck}:StopAll",1, wait=True)
        epics.caput(f"{struck}:NuseAll",npts-2, wait=True)
        epics.caput(f"{struck}:Dwell",dwell, wait=True)
        epics.caput(f"{struck}:Prescale",prescale, wait=True)
        epics.caput(f"{struck}:ChannelAdvance",0, wait=True) #0= internal trigger, 1= external trigger

def after_outer():
    #NOTE: normally you would reset detectors to capture continuously at a fixed rate for monitoring purposes
    pass
def before_inner():
    #NOTE: normally you would set stage speed and arm triggers
    pass
def after_inner():
    #NOTE: normally you would reset stage speed to max speed for retrace move
    pass

def change_filename(filename_PV, value, scanum, xmap=None, xspress3=None):
    print(f"{filename_PV} changed to: {value}")
    scan_num = epics.caget(f"{scanum}")
    beamline =f"{scanum.split(':')[0]}"
    fname_prefix = value
    name = f"{fname_prefix}_{beamline}_{scan_num:04d}_"
    if xmap is not None:
        epics.caput(f"{xmap}:netCDF1:FileName", f"{name}XMAP", wait=False)
    if xspress3 is not None:
        epics.caput(f"{xspress3}:HDF1:FileName", f"{name}XSPRESS3", wait=False)


def run_scan(outer, before_out, after_out, before_in, after_in, scanum, filename_PV, dwell_PV, xmap=None, xspress3=None, struck=None, npts=None):
    epics.caput(f"{outer}.EXSC",1, wait=False)
    time.sleep(1)
    before_scan(scanum, filename_PV, dwell_PV, xmap, xspress3, struck, npts) #gets called before each line for some reason.
    while epics.caget(f"{outer}.BUSY"):
        print("scanning")
        time.sleep(2)
        if epics.caget(f"{before_out}.VAL") == 1:
            print("before outer")
            epics.caput(f"{before_out}.VAL",0, wait=False)
        if epics.caget(f"{after_out}.VAL") == 1:
            print("after outer")
            after_outer()
            epics.caput(f"{after_out}.VAL",0, wait=False)
        if epics.caget(f"{before_in}.VAL") == 1:
            print("before inner")
            before_inner()
            epics.caput(f"{before_in}.VAL",0, wait=False)
        if epics.caget(f"{after_in}.VAL") == 1:
            print("after inner")
            after_inner()
            epics.caput(f"{after_in}.VAL",0, wait=False)
#wait for scan to finish

def trigger_detectors(params): #for scan-record-less scans
    if params["scan_type"] == "fly":
        if "xspress3" in params["detectors"]:
            epics.caput(params["xspress3"].Capture.PROC, 1)
        if "xmap" in params["detectors"]:
            epics.caput(params["xmap"].Capture.PROC, 1)
        if "eiger" in params["detectors"]:
            epics.caput(params["eiger"].Capture.PROC, 1)
        if "tetramm" in params["detectors"]:
            epics.caput(params["tetramm"].Capture.PROC, 1)

    if "xspress3" in params["detectors"]:
        epics.caput(params["xspress3"].EraseStart.PROC, 1)
    if "xmap" in params["detectors"]:
        epics.caput(params["xmap"].EraseStart.PROC, 1)
    if "eiger" in params["detectors"]:
        epics.caput(params["eiger"].EraseStart.PROC, 1)
    if "tetramm" in params["detectors"]:
        epics.caput(params["tetramm"].EraseStart.PROC, 1)
    if "struck" in params["detectors"]:
        epics.caput(params["struck"].EraseStart.PROC, 1)

def setup_detector(detector_type, params=None, **kwargs):
    # Setup detector based on type
    if params["scan_type"] == "fly":
        if detector_type == "xmap":
            setup_xmap_fly(params)
        elif detector_type == "tetramm":
            setup_tetramm_fly(params)
        elif detector_type == "xspress3":
            setup_xspress3_fly(params)
        elif detector_type == "struck":
            setup_struck_fly(params)
        elif detector_type == "eiger":
            setup_eiger_fly(params)
        elif detector_type == "interferometer":
            setup_interferometer_fly(params)
        elif detector_type == "scaler":
            setup_scaler_fly(params)
    else:
        if detector_type == "xmap":
            setup_xmap_step(params)
        elif detector_type == "tetramm":
            setup_tetramm_step(params)
        elif detector_type == "xspress3":
            setup_xspress3_step(params)
        elif detector_type == "struck":
            setup_struck_step(params)   
        elif detector_type == "eiger":
            setup_eiger_step(params)
        elif detector_type == "interferometer":
            setup_interferometer_step(params)
        elif detector_type == "scaler":
            setup_scaler_step(params)
        else:
            print(f"Warning: Unknown detector type '{detector_type}'")
            return
    return
def setup_triggers(params, beamline):
    if params["scan_type"] == "fly":
        if beamline == "2xfm":
            setup_hydra_controller(params)
            setup_struck_fly(params, prescale=1)

        elif beamline == "bnp":
            setup_struck_fly(params, prescale=1)

        else:
            setup_struck_fly(params)
                
    return
def setup_scan_record(params):
    if params["scan_type"] == "fly":
        setup_scan_record_fly(params)
    else:
        setup_scan_record_step(params)
    return