import epics
from trajectories import *
import numpy as np
import time
import threading
import os
import sys
import h5py
import subprocess

#TODO: for demo. get position filesaving working 
#TODO: change basedir to s2data
#TODO: create aliases to startup gui, MCA screens and maybe live position view (ultimately GUI)
#TODO: try to implement changes on GUI
#TODO: 
'''Checklist: 
*startup 2idbtst from VME crate, open terminal type 2idtst <enter> 
*startup xspress3/tetramm ioc: open terminal and type 2iddxsporess3 start <enter> 2iddxspress3 caqtdm <enter>
*startup eiger ioc: ssh into nenya as user2ide, open terminal and 2idEGR start <enter> open terminal as user2idd, type 2idEGR caqtdm <enter>
*startup softglue ioc: power cycle softglue device if necessary, open terminal, type sgz <enter>
*startup Keenan position stream service, open terminal, type ***
*start GUI form 2iddxspress3: open terminal, type batchscan <enter> 
    OR run python scan script from /****
*startup rsync service for each machine saving data: nenya, 2idfdxspress3, or save to micdata for now
'''

def define_devices():
    t0 = time.time()
    os.environ["EPICS_CA_ADDR_LIST"] = "10.54.113.18"
    ########################################################## PV and Config stuff
    inner_loop = "2idbtst:scan1"
    outer_loop = "2idbtst:scan2"
    x_motor = "2idbtst:m1"
    y_motor = "2idbtst:m2"
    r_motor = "2idsft:m3"
    savedata = "2idbtst:"
    xspress3  = "XSP3_1Chan"
    softglue = "2idMZ1"
    eiger = "2ideEGR:cam1"
    tetramm = "2idsft:TetrAMM1"
    pos_cap = "testServer:"
    basedir = "/mnt/micdata2/savedata_dev"

    ########################################################## define Scan record 
    scan1 = epics.Device(f"{inner_loop}.", attrs=('BUSY', 'P1PV', 'R1PV', 'P2PV', 'NPTS', 'PDLY', 'P1SM', 'P2SM', 'P1PA', 'P2PA', 'ACQT', 'EXSC', 'SMSG', 'CMND', 'BSPV', 'ASPV', 'T1PV', 'T2PV', 'T3PV', 'T4PV'))
    scan1.P1PV = x_motor
    scan1.R1PV = f"{x_motor}.RBV" 
    scan1.P2PV = y_motor
    scan1.R2PV = f"{y_motor}.RBV"
    scan1.PASM = 2 #prior position
    scan1.P1AR = 0 #absolute
    scan1.P1SM = 1 #table mode x
    scan1.P2SM = 1 #table mode y
    scan1.BSPV = ""
    scan1.ASPV = ""
    scan1.T1PV = ""
    scan1.T2PV = ""
    scan1.T3PV = ""
    scan1.T4PV = ""
    scan2 = epics.Device(f"{outer_loop}.", attrs=('BUSY', 'P1PV', 'R1PV', 'P2PV', 'NPTS', 'PDLY', 'P1SM', 'P2SM', 'P1PA', 'P2PA', 'ACQT', 'EXSC', 'SMSG', 'CMND', 'BSPV', 'ASPV', 'T1PV', 'T2PV', 'T3PV', 'T4PV'))
    scan2.P1PV = ""
    scan2.R1PV = ""
    scan2.PASM = 2 #prior position
    scan2.P1AR = 0 #absolute
    scan2.P1SM = 1 #table mode r
    scan2.BSPV = ""
    scan2.ASPV = ""
    scan2.T1PV = f"{inner_loop}.EXSC" 
    scan2.T2PV = f'{xspress3}:det1:Acquire'
    scan2.T3PV = f'{tetramm}:Acquire'
    scan2.T4PV = ""
    #clear det triggers, clear busy records

    ########################################################## define saveData contorls (optional?") 
    save_data = epics.Device(f"{savedata}", attrs=('saveData_fileSystem', 'saveData_subDir', 'saveData_baseName', 'saveData_fileName', 'saveData_scanNumber', 'PDLY' ))
    ########################################################## define motors
    x_motor =  epics.Motor(x_motor)
    y_motor =  epics.Motor(y_motor)
    r_motor =  epics.Motor(r_motor)
    ########################################################## define Eiger (not using for BDP demo)
    # egr = epics.Device(f"{eiger}", attrs=('State_RBV', 'AcquireTime', 'AcquirePeriod', 'NumImages', 'NumExposures', 'CountingMode', 'TriggerMode', 'ManualTrigger','Trigger', 'NumTriggers', 
                                    # 'Acquire', 'ArrayCounter', 'ArrayCounter_RBV', 'FWNImagesPerFile', 'FWNamePattern', 'SaveFiles', 'FilePath', 'FileNumber', 'FilePathExists_RBV'))
    ########################################################## define Xspress3 
    xp3 = epics.Device(f'{xspress3}:det1:', attrs=('ERASE', 'Acquire', 'AcquireTime', 'NumImages', 'ArrayCounter_RBV', 'EraseOnStart', 'DetectorState_RBV', 'TriggerMode', 'Pva1:EnableCallbacks'))
    xp3_filesave = epics.Device(f'{xspress3}:HDF1:', attrs=('Capture', 'FilePath', 'FileName', 'FileNumber', 'FileWriteMode', 'FileTemplate', 'AutoIncrement', 'NumCaptured_RBV'))
    ########################################################## define TetraMM
    tmm = epics.Device(f'{tetramm}:', attrs=('Acquire', 'AcquireMode', 'Range', 'ValuesPerRead', 'AveragingTime', 'FastAveragingTime', 'FastAverageScan.SCAN','EmptyFreeList', 'TriggerMode', 'NumAcquired', 'NumAcquire'))
    tmm_filesave = epics.Device(f'{tetramm}:netCDF1:', attrs=('EnableCallbacks','Capture', 'FilePath', 'FileName', 'FileNumber', 'FileTemplate', 'AutoIncrement', 'WriteFile','FileWriteMode', 'WriteStatus', 'FilePathExists_RBV'))
    ########################################################## define SoftGlue 
    sg = epics.Device(f'{softglue}:SG:', attrs=('1_CLEAR_Signal.PROC', '2_CLEAR_Signal.PROC', 'UpCntr-1_CLEAR_Signal.PROC')) 
    
    dma = epics.Device(f'{softglue}:1acquireDma.', attrs=('C','F', 'D', 'VALF', 'VALG', 'VALC'))
    # return scan1, scan2, egr, xp3, xp3_filesave, tmm, tmm_filesave, sg, dma, sg, x_motor, y_motor, r_motor
    t1 = time.time()-t0
    print(f"defining devces took {t1} seconds")
    return scan1, scan2, xp3, xp3_filesave, tmm, tmm_filesave, sg, dma, x_motor, y_motor, r_motor, save_data, pos_cap, basedir

def generate_dir_structure(basedir):
    subdirs = ["xspress3", "eiger", "mda", "tetramm", "positions"]
    for subdir in subdirs:
        if not os.path.exists(f'{basedir}{subdir}'):
            os.makedirs(f'{basedir}{subdir}', exist_ok=True)
    return 
            
def init_devices():
    t0 = time.time()
    generate_dir_structure(basedir)

    scan2.NPTS = 1
    scan2.CMND = 0
    scan2.P1PA = np.array([0]) #this doesnt do anything, I just need outer loop to run once, I'm manually setting the rotation angle outisde of scan record.
    scan1.CMND = 0 

    #micdata mount point on VME crate not consistent with linux machine mount point: "/mnt/micdata2/savedata_dev/" =! //micdata/data2/savedata_dev
    #something wrong with savedata filewriting, not incluiding it for now. Cant reboot crate either 
    mount_pt = "//micdata/data"+basedir.split("micdata")[1]
    save_data.saveData_fileSystem =  f"{mount_pt}/mda"

    # save_data.saveData_fileSystem =  f"{basedir}/mda"
    # save_data.saveData_baseName = sample_name

    xp3.ERASE = 1
    xp3.EraseOnStart=0
    #TODO: set correct dwell time and number of acquisitions
    # xp3.TriggerMode = 3
    xp3.TriggerMode = 1 #using softtrigger for demo because hardware triggers unavailable
    xp3_prefix = xp3._prefix.split(":")[0]
    epics.caput(f"{xp3_prefix}:Pva1:EnableCallbacks", 1)
    xp3_filesave.FilePath = f"{basedir}/xspress3/"
    xp3_filesave.Autoincrement = 0
    xp3_filesave.FileTemplate = f"%s%s.h5"
    xp3_filesave.FileWriteMode = 2 #stream

    #TODO: setup triggers given dwell time, step size, frequency, etc.... (waiting on Tim for this)
    # tmm.TriggerMode = 1 #using softtrigger for demo because hardware triggers unavailable
    tmm.TriggerMode = 0
    tmm.EmptyFreeList = 1

    tmm_filesave.EnableCallbacks = 1
    tmm_filesave.FilePath = f"{basedir}/tetraMM/"
    tmm_filesave.AutoIncrement = 0
    tmm_filesave.FileTemplate = f"%s%s.nc"
    tmm_filesave.FileWriteMode = 2 #stream
    
    # egr.NumImages = npts
    # egr.NumExposures = npts
    # egr.TriggerMode = 3 #ext
    # egr.FWNamePattern = f"%s%s_%d"
    # egr.FilePath = "{savedatadir}eiger"
    # egr.SaveFiles = file_prefix

    epics.caput(f"{sg}:1_CLEAR_Signal.PROC", 1)
    epics.caput(f"{sg}:2_CLEAR_Signal.PROC", 1)
    epics.caput(f"{sg}:UpCntr-1_CLEAR_Signal.PROC", 1)
    subprocess.run(["pvput", f"{pos_cap}path", f"{basedir}/positions"], capture_output=False)

    # egr.Acquire=1
    # xp3.Acquire=1 #reenable when trigger mode set to external
    # tmm.Acquire=1 # reenable when trigger mode set to external
    t1 = time.time() - t0
    print(f"scan init took {t1} seconds")
    
#TODO: add run_scan callback to monitor when scan is done instead of looping.  
def run_scan(x,y,t, r, base_name="sampleX_", reset=True):
    save_data.saveData_baseName = base_name
    fast = 1 #mm/s
    step_size = np.round(np.sqrt((x[1]-x[0])**2 + (y[1]-y[0])**2),8)
    dwell = t[1] #dwelltime in time array should all be the same
    npts = len(x)    
    scan1.NPTS = npts
    scan1.PDLY = dwell*0.2 #precision of pdly only goes down to 0.01, meaning dwell times are only good up to 
    scan1.P1PA = x #array x
    scan1.P2PA = y #array y
    xp3.NumImages = npts 
    xp3.AcquireTime = dwell 
    tmm.NumAcquire = npts
    tmm.AveragingTime = dwell
    tmm.FastAveragingTime = dwell
    tmm.ValuesPerRead = int(np.floor(100000*dwell))

    x_motor.VELO = fast
    y_motor.VELO = fast
    x_motor.move(x[0], wait=True, timeout=3)
    y_motor.move(y[0], wait=True, timeout=3)
    x_motor.VELO = dwell/step_size

    if reset:
        save_data.saveData_scanNumber = 0
        xp3_filesave.FileNumber = 0
        tmm_filesave.FileNumber = 0

    for r_pos in r:
        print(f"on angle {r_pos}")
        next_number = "{:04d}".format(save_data.saveData_scanNumber)

        filename = base_name+next_number
        xp3_filesave.FileName = filename
        tmm_filesave.FileName = filename
        
        xp3_filesave.Capture = 1
        tmm_filesave.Capture = 1
        dma.D = 1 #clear softglue array
        dma.F = 1 #clear buffer
        subprocess.run(["pvput", f"{pos_cap}name", filename], capture_output=True)
        # subprocess.run(["pvput", f"{pos_cap}reset", "1"], capture_output=False)
        subprocess.run(["pvput", f"{pos_cap}start", "1"], capture_output=True)
        
        r_motor.move(r_pos, wait=True, timeout=3)
        scan2.EXSC = 1
        time.sleep(3)
        
        while scan2.BUSY:
            if stopped: 
                break
        subprocess.run(["pvput", f"{pos_cap}stop", "1"], capture_output=True)
    return

def monitor_scan():
    while not stopped: 
        #TODO:check for pause
        #TODO:check scan_record(s) incrementing
        #TODO:check scan progress
        #TODO:check xp3 incrementing
        #TODO:check egr incrementing
        #TODO:check tetramm incrementing
        #TODO: scatterplot scan progress 
        #TODO: get scaler data to show intensity in scatterplot
        #escape condition == abort or scan_done
        return
    
def create_master_file(basedir, sample_name):
    subgroups = ["xspress3", "eiger", "mda", "tetramm", "positions"]
    with h5py.File(f"{basedir}/{sample_name}master.h5", "w") as f:
        for subgroup in subgroups:
            f.create_group(subgroup)
            files = os.listdir(f"{basedir}/{subgroup}")
            files = [file for file in files if file.split(".")[-1]=="h5"]
            files = [file for file in files if file.split("_")[0]==sample_name.strip("_")]
            for file in files:
                f[f"/{subgroup}/{file}"] = h5py.ExternalLink(f"{basedir}/{subgroup}/{file}", "/")
        
########################################################### Scan Params
global stopped
stopped = False
scan1, scan2, xp3, xp3_filesave, tmm, tmm_filesave, sg, dma, x_motor, y_motor, r_motor, save_data, pos_cap, basedir = define_devices()

base_name = "sample0_"
x,y,t = snake(dwell=0.1, step_size=0.01, x_center=0, y_center=0, x_width=0.1, y_width=0.1)
# x,y,t = raster(dwell=0.1, step_size=0.1, x_center=0, y_center=0, x_width=1, y_width=1, x_return_vel=1)
# x,y,t  = spiral(dwell=0.1, r_step_size=0.1, step_size = 0.1, x_center=0, y_center=0, diameter=1)
# init_devices()
r = np.linspace(0,2, 5)
# scan2.add_callback(attr=scan2.BUSY, callback=scan_finished())
run_scan(base_name=base_name, r_positions=r, reset=True)
create_master_file(basedir="/mnt/micdata2/savedata_dev", sample_name=base_name)

samplename = "sample1_"
x,y,t = snake(dwell=0.1, step_size=0.001, x_center=0, y_center=0, x_width=0.1, y_width=0.1)
r = np.linspace(0,2, 5)
run_scan(base_name=base_name, r=r, reset=True)
create_master_file(basedir="/mnt/micdata2/savedata_dev", sample_name=samplename)


#maybe skip threading for now..
# scn = threading.Thread(target = run_scan)# mntr = threading.Thread(target = monitor_scan)


# while True:
#     user_input = input("options: pause, resume, abort")
#     if user_input == "pause": 
#         print("paused")

#     elif user_input == "resume":
#         print("paused")

#     elif user_input == "abort":
#         stopped = True
#         scn.exit()
#         mntr.exit()
#         break
#     else: 
#         print("not valid input")
