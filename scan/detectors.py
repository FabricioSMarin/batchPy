import epics
import numpy as np
import time

def setup_scan_record_fly(params):

    # for i in range(len(disable_calcs)):
    #     epics.caput(f"{disable_calcs[i]}Enable",0, wait=True)
    #     epics.caput(f"{disable_calcs[i]}.SCAN",0, wait=True)
    npts_x = int(eval(params["l1_width"])/eval(params["l1_size"])) #number of lines
    npts_y = int(eval(params["l2_width"])/eval(params["l2_size"])) #number of lines
    dwell = eval(params["dwell"])
    epics.caput(f"{params["outer"]}.BSWAIT",0, wait=True)
    epics.caput(f"{params["inner"]}.BSWAIT",0, wait=True)
    epics.caput(f"{params["outer"]}.ASWAIT",0, wait=True)
    epics.caput(f"{params["inner"]}.ASWAIT",0, wait=True)
    epics.caput(f"{params["inner"]}.NPTS",npts_x, wait=True)
    epics.caput(f"{params["inner"]}.BSPV",params["before_in"], wait=True)
    epics.caput(f"{params["outer"]}.BSPV",params["before_out"], wait=True)
    epics.caput(f"{params["inner"]}.ASPV",params["after_in"], wait=True)
    epics.caput(f"{params["outer"]}.ASPV",params["after_out"], wait=True)
    epics.caput(f"{params["outer"]}.NPTS",npts_y, wait=True)
    epics.caput(f"{params["outer"]}.R1PV",params["loop1"], wait=True)
    epics.caput(f"{params["inner"]}.R1PV",params["loop2"], wait=True)
    epics.caput(f"{params["outer"]}.P1PV","", wait=True)
    epics.caput(f"{params["inner"]}.P1PV","", wait=True)
    epics.caput(f"{params["inner"]}.T1PV","", wait=True)
    epics.caput(f"{params["inner"]}.T2PV","", wait=True)
    epics.caput(f"{params["inner"]}.T3PV","", wait=True)
    epics.caput(f"{params["outer"]}.T3PV","", wait=True)
    epics.caput(f"{params["outer"]}.T4PV",f"{params["inner"]}.EXSC", wait=True)


    epics.caput(f"{params["inner"]}.T4PV",f"{params["struck"]}:EraseStart", wait=True)

    if "xmap" in params["detectors"]:
        epics.caput(f"{params["outer"]}.T1PV",f"{params["xmap"]}:netCDF1:Capture", wait=True)
        epics.caput(f"{params["outer"]}.T2PV",f"{params["xmap"]}:EraseStart", wait=True)
    else:
        epics.caput(f"{params["inner"]}.T1PV","", wait=True)
        epics.caput(f"{params["inner"]}.T2PV","", wait=True)
    if "xspress3" in params["detectors"]:
        epics.caput(f"{params["xspress3"]}:det1:NumImages",npts_x, wait=True)
        epics.caput(f"{params["xspress3"]}:det1:TriggerMode", 1, wait=True) #3=TTL Veto Only, 1=Internal Trigger
        epics.caput(f"{params["xspress3"]}:HDF1:AutoIncrement",1, wait=True)
        epics.caput(f"{params["xspress3"]}:HDF1:FileNumber",0, wait=True)
        epics.caput(f"{params["inner"]}.T1PV",f"{params["xspress3"]}:HDF1:Capture", wait=True)
        epics.caput(f"{params["inner"]}.T2PV",f"{params["xspress3"]}:det1:Acquire", wait=True)
        epics.caput(f"{params["xspress3"]}:HDF1:FileTemplate", "%s%s_%04d.h5", wait=True)
    else:
        epics.caput(f"{params["inner"]}.T1PV","", wait=True)
        epics.caput(f"{params["inner"]}.T2PV","", wait=True)

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

def setup_hydra_controller(params):
    params["hydra_controller"].StartPosition.VAL = params["motors"]["x"].VAL + params["step_size"]
    params["hydra_controller"].EndPosition.VAL = params["motors"]["x"].VAL + params["width"]
    params["hydra_controller"].NumTriggers.VAL = params["loop1"].NPTS - 1
    return

def setup_xmap_fly(params, detector_pv=None):
    npts = params["loop1"].NPTS
    nbuffs = np.ceil((npts)/124)
    epics.caput(f"{detector_pv}:PixelsPerRun",npts, wait=True)
    epics.caput(f"{detector_pv}:netCDF1:NumCapture",nbuffs, wait=True)
    epics.caput(f"{detector_pv}:netCDF1:Capture",0, wait=True)
    epics.caput(f"{detector_pv}:StopAll",1, wait=True)
    epics.caput(f"{detector_pv}:CollectMode", 1, wait=True)
    return

def setup_xspress3_fly(params, detector_pv=None):
    npts = int(eval(params["l1_width"])/eval(params["l1_size"]))
    epics.caput(f"{detector_pv}:det1:NumImages",npts, wait=True)
    epics.caput(f"{detector_pv}:det1:TriggerMode", 3, wait=True) #3=TTL Veto Only, 1=Internal Trigger
    epics.caput(f"{detector_pv}:HDF1:AutoIncrement",1, wait=True)

def setup_struck_fly(params, detector_pv=None, prescale=1):
    npts = params["loop1"].NPTS
    # mres = params['loop1_motor_resolution']
    #loop1_step_size = params['loop1_step_size']
    #prescale = np.abs(step_size/motor_resolution) #Note: this value may differ depending on motor pulse source/stepsize
    epics.caput(f"{detector_pv}:ChannelAdvance",0, wait=True) #0= internal trigger, 1= external trigger
    epics.caput(f"{detector_pv}:PresetReal",0.0, wait=True)
    epics.caput(f"{detector_pv}:NuseAll",npts-2, wait=True)
    epics.caput(f"{detector_pv}:Prescale", prescale, wait=True)
    epics.caput(f"{detector_pv}:EraseAll",1, wait=True)
    return

def setup_eiger_fly(params, detector_pv=None):
    pass

def setup_interferometer_fly(params, detector_pv=None):
    pass

def setup_scaler_fly(params, detector_pv=None):
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

def setup_detector(detector, params=None):
    # Setup detector based on type
    for device in params["detectors"][detector]:
        if params["scan_type"] == "fly":
            if detector == "xmap":
                setup_xmap_fly(params, detector_pv=device)
            elif detector == "tetramm":
                setup_tetramm_fly(params, detector_pv=device)
            elif detector == "xspress3":
                setup_xspress3_fly(params, detector_pv=device)
            elif detector == "struck":
                setup_struck_fly(params, detector_pv=device)
            elif detector == "eiger":
                setup_eiger_fly(params, detector_pv=device)
            elif detector == "interferometer":
                setup_interferometer_fly(params, detector_pv=device)
        else:
            if detector == "xmap":
                setup_xmap_step(params, detector_pv=device)
            elif detector == "tetramm":
                setup_tetramm_step(params, detector_pv=device)
            elif detector == "xspress3":
                setup_xspress3_step(params, detector_pv=device)
            elif detector == "struck":
                setup_struck_step(params, detector_pv=device)
            elif detector == "eiger":
                setup_eiger_step(params, detector_pv=device)
            elif detector == "interferometer":
                setup_interferometer_step(params, detector_pv=device)

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