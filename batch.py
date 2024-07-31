#!/APSshare/anaconda/x86_64/bin/python

import epics
import epics.devices
from epics import caput, caget
import time
import numpy as np
import os
import json
import trajectories
import subprocess

class Scan(object):
    #get pv names from gui and check pvs are connected
    def __init__(self):
        self.scan1 = None
        self.scan2 = None
        self.eiger = None
        self.xspress3 = None
        self.tetramm = None
        self.softglue = None
        self.softglue_dma = None

    def define_devices_demo(self):
        t0 = time.time()
        os.environ["EPICS_CA_ADDR_LIST"] = "10.54.113.18"
        ########################################################## PV and Config stuff
        self.inner_loop = "2idbtst:scan1"
        self.outer_loop = "2idbtst:scan2"
        self.x_motor = "2idbtst:m1"
        self.y_motor = "2idbtst:m2"
        self.r_motor = "2idsft:m3"
        self.savedata = "2idbtst:"
        self.xspress3  = "XSP3_1Chan"
        self.softglu_pfx = "2idMZ1"
        self.eiger = "2ideEGR:cam1"
        self.tetramm = "2idsft:TetrAMM1"
        self.pos_cap = "testServer:"
        self.basedir = "/mnt/micdata2/savedata_dev"

        ########################################################## define Scan record 
        self.scan1 = epics.Device(f"{self.inner_loop}.", attrs=('BUSY', 'P1PV', 'R1PV', 'P2PV', 'NPTS', 'PDLY', 'P1SM', 'P2SM', 'P1PA', 'P2PA', 'ACQT', 'EXSC', 'SMSG', 'CMND', 'BSPV', 'ASPV', 'T1PV', 'T2PV', 'T3PV', 'T4PV'))
        self.scan1.P1PV = self.x_motor
        self.scan1.R1PV = f"{self.x_motor}.RBV" 
        self.scan1.P2PV = self.y_motor
        self.scan1.R2PV = f"{self.y_motor}.RBV"
        self.scan1.PASM = 2 #prior position
        self.scan1.P1AR = 0 #absolute
        self.scan1.P1SM = 1 #table mode x
        self.scan1.P2SM = 1 #table mode y
        self.scan1.BSPV = ""
        self.scan1.ASPV = ""
        self.scan1.T1PV = ""
        self.scan1.T2PV = ""
        self.scan1.T3PV = ""
        self.scan1.T4PV = ""
        self.scan2 = epics.Device(f"{self.outer_loop}.", attrs=('BUSY', 'P1PV', 'R1PV', 'P2PV', 'NPTS', 'PDLY', 'P1SM', 'P2SM', 'P1PA', 'P2PA', 'ACQT', 'EXSC', 'SMSG', 'CMND', 'BSPV', 'ASPV', 'T1PV', 'T2PV', 'T3PV', 'T4PV'))
        self.scan2.P1PV = ""
        self.scan2.R1PV = ""
        self.scan2.PASM = 2 #prior position
        self.scan2.P1AR = 0 #absolute
        self.scan2.P1SM = 1 #table mode r
        self.scan2.BSPV = ""
        self.scan2.ASPV = ""
        self.scan2.T1PV = f"{self.inner_loop}.EXSC" 
        self.scan2.T2PV = f'{self.xspress3}:det1:Acquire'
        self.scan2.T3PV = f'{self.tetramm}:Acquire'
        self.scan2.T4PV = ""

        timeout = 0.25
        #clear det triggers, clear busy records

        ########################################################## define saveData contorls (optional?") 
        self.save_data = epics.Device(f"{self.savedata}", attrs=('saveData_fileSystem', 'saveData_subDir', 'saveData_baseName', 'saveData_fileName', 'saveData_scanNumber', 'PDLY' ))
        ########################################################## define motors
        self.x_motor =  epics.Motor(self.x_motor, timeout=timeout)
        self.y_motor =  epics.Motor(self.y_motor, timeout=timeout)
        self.r_motor =  epics.Motor(self.r_motor, timeout=timeout)
        ########################################################## define Eiger (not using for BDP demo)
        # egr = epics.Device(f"{eiger}", attrs=('State_RBV', 'AcquireTime', 'AcquirePeriod', 'NumImages', 'NumExposures', 'CountingMode', 'TriggerMode', 'ManualTrigger','Trigger', 'NumTriggers', 
                                        # 'Acquire', 'ArrayCounter', 'ArrayCounter_RBV', 'FWNImagesPerFile', 'FWNamePattern', 'SaveFiles', 'FilePath', 'FileNumber', 'FilePathExists_RBV'))
        ########################################################## define Xspress3 
        self.xp3 = epics.Device(f'{self.xspress3}:det1:', attrs=('ERASE', 'Acquire', 'AcquireTime', 'NumImages', 'ArrayCounter_RBV', 'EraseOnStart', 'DetectorState_RBV', 'TriggerMode', 'Pva1:EnableCallbacks'))
        self.xp3_filesave = epics.Device(f'{self.xspress3}:HDF1:', attrs=('Capture', 'FilePath', 'FileName', 'FileNumber', 'FileWriteMode', 'FileTemplate', 'AutoIncrement', 'NumCaptured_RBV'))
        ########################################################## define TetraMM
        self.tmm = epics.Device(f'{self.tetramm}:', attrs=('Acquire', 'AcquireMode', 'Range', 'ValuesPerRead', 'AveragingTime', 'FastAveragingTime', 'FastAverageScan.SCAN','EmptyFreeList', 'TriggerMode', 'NumAcquired', 'NumAcquire'))
        self.tmm_filesave = epics.Device(f'{self.tetramm}:netCDF1:', attrs=('EnableCallbacks','Capture', 'FilePath', 'FileName', 'FileNumber', 'FileTemplate', 'AutoIncrement', 'WriteFile','FileWriteMode', 'WriteStatus', 'FilePathExists_RBV'))
        ########################################################## define SoftGlue 
        self.sg = epics.Device(f'{self.softglu_pfx}:SG:', attrs=('1_CLEAR_Signal.PROC', '2_CLEAR_Signal.PROC', 'UpCntr-1_CLEAR_Signal.PROC')) 
        self.dma = epics.Device(f'{self.softglu_pfx}:1acquireDma.', attrs=('C','F', 'D', 'VALF', 'VALG', 'VALC'))
        # return scan1, scan2, egr, xp3, xp3_filesave, tmm, tmm_filesave, sg, dma, sg, x_motor, y_motor, r_motor
        t1 = time.time()-t0
        print(f"defining devces took {t1} seconds")

    def init_devices_demo(self):
        t0 = time.time()
        self.scan2.NPTS = 1
        self.scan2.CMND = 0
        self.scan2.P1PA = np.array([0]) #this doesnt do anything, I just need outer loop to run once, I'm manually setting the rotation angle outisde of scan record.
        self.scan1.CMND = 0 

        #micdata mount point on VME crate not consistent with linux machine mount point: "/mnt/micdata2/savedata_dev/" =! //micdata/data2/savedata_dev
        #something wrong with savedata filewriting, not incluiding it for now. Cant reboot crate either 
        mount_pt = "//micdata/data"+self.basedir.split("micdata")[1]
        self.save_data.saveData_fileSystem =  f"{mount_pt}/mda"

        # save_data.saveData_fileSystem =  f"{basedir}/mda"
        # save_data.saveData_baseName = sample_name

        self.xp3.ERASE = 1
        self.xp3.EraseOnStart=0
        #TODO: set correct dwell time and number of acquisitions
        # xp3.TriggerMode = 3
        self.xp3.TriggerMode = 1 #using softtrigger for demo because hardware triggers unavailable
        xp3_prefix = self.xp3._prefix.split(":")[0]
        epics.caput(f"{xp3_prefix}:Pva1:EnableCallbacks", 1)
        self.xp3_filesave.FilePath = f"{self.basedir}/xspress3/"
        self.xp3_filesave.Autoincrement = 0
        self.xp3_filesave.FileTemplate = f"%s%s.h5"
        self.xp3_filesave.FileWriteMode = 2 #stream

        #TODO: setup triggers given dwell time, step size, frequency, etc.... (waiting on Tim for this)
        # tmm.TriggerMode = 1 #using softtrigger for demo because hardware triggers unavailable
        self.tmm.TriggerMode = 0
        self.tmm.EmptyFreeList = 1

        self.tmm_filesave.EnableCallbacks = 1
        self.tmm_filesave.FilePath = f"{self.basedir}/tetraMM/"
        self.tmm_filesave.AutoIncrement = 0
        self.tmm_filesave.FileTemplate = f"%s%s.nc"
        self.tmm_filesave.FileWriteMode = 2 #stream
        
        # egr.NumImages = npts
        # egr.NumExposures = npts
        # egr.TriggerMode = 3 #ext
        # egr.FWNamePattern = f"%s%s_%d"
        # egr.FilePath = "{savedatadir}eiger"
        # egr.SaveFiles = file_prefix
        epics.caput(f"{self.softglu_pfx}:SG:UpDnCntr-1_CLEAR_Signal.PROC", 1)
        epics.caput(f"{self.softglu_pfx}:SG:UpDnCntr-2_CLEAR_Signal.PROC", 1)
        epics.caput(f"{self.softglu_pfx}:SG:UpCntr-1_CLEAR_Signal.PROC", 1)
        subprocess.run(["pvput", f"{self.pos_cap}path", f"{self.basedir}/positions"], capture_output=False)

        # egr.Acquire=1
        # xp3.Acquire=1 #reenable when trigger mode set to external
        # tmm.Acquire=1 # reenable when trigger mode set to external
        t1 = time.time() - t0
        print(f"scan init took {t1} seconds")
        pass

    def begin_demo(self, x,y,t, r, base_name="sampleX_", reset=True):
        self.save_data.saveData_baseName = base_name
        fast = 1 #mm/s
        step_size = np.round(np.sqrt((x[1]-x[0])**2 + (y[1]-y[0])**2),8)
        dwell = t[1] #dwelltime in time array should all be the same
        npts = len(x)    
        self.scan1.NPTS = npts
        self.scan1.PDLY = dwell*0.2 #precision of pdly only goes down to 0.01, meaning dwell times are only good up to 
        self.scan1.P1PA = x #array x
        self.scan1.P2PA = y #array y
        self.xp3.NumImages = npts 
        self.xp3.AcquireTime = dwell 
        self.tmm.NumAcquire = npts
        self.tmm.AveragingTime = dwell
        self.tmm.FastAveragingTime = dwell
        self.tmm.ValuesPerRead = int(np.floor(100000*dwell))

        self.x_motor.VELO = fast
        self.y_motor.VELO = fast
        self.x_motor.move(x[0], wait=True, timeout=3)
        self.y_motor.move(y[0], wait=True, timeout=3)
        self.x_motor.VELO = dwell/step_size

        if reset:
            self.save_data.saveData_scanNumber = 0
            self.xp3_filesave.FileNumber = 0
            self.tmm_filesave.FileNumber = 0

        for r_pos in r:
            print(f"on angle {r_pos}")
            next_number = "{:04d}".format(self.save_data.saveData_scanNumber)

            filename = base_name+next_number
            self.xp3_filesave.FileName = filename
            self.tmm_filesave.FileName = filename
            
            self.xp3_filesave.Capture = 1
            self.tmm_filesave.Capture = 1
            self.dma.D = 1 #clear softglue array
            self.dma.F = 1 #clear buffer
            subprocess.run(["pvput", f"{self.pos_cap}name", filename], capture_output=True)
            # subprocess.run(["pvput", f"{pos_cap}reset", "1"], capture_output=False)
            subprocess.run(["pvput", f"{self.pos_cap}start", "1"], capture_output=True)
            
            self.r_motor.move(r_pos, wait=True, timeout=3)
            self.scan2.EXSC = 1
            time.sleep(3)
            
            while self.scan2.BUSY:
                # if self.stopped: 
                time.sleep(1)
            subprocess.run(["pvput", f"{self.pos_cap}stop", "1"], capture_output=True)
        return

    def define_xspress3(self,prefix):
        self.xspress3 = epics.Device(f'{prefix}:det1', attrs=('ERASE', 'Acquire', 'NumImages', 'ArrayCounter_RBV', 'EraseOnStart', 'DetectorState_RBV', 'TriggerMode', 'Pva1.EnableCallbacks'))
        self.xspress3_filesave = epics.Device(f'{prefix}:HDF1', attrs=('Capture', 'FilePath', 'FileName', 'FileNumber', 'FileWriteMode', 'FileTemplate', 'AutoIncrement', 'NumCaptured_RBV'))
    
    def define_eiger(self,prefix):
        self.eiger = epics.Device(f"{prefix}", attrs=('State_RBV', 'AcquireTime', 'AcquirePeriod', 'NumImages', 'NumExposures', 'CountingMode', 'TriggerMode', 'ManualTrigger','Trigger', 'NumTriggers', 
                                        'Acquire', 'ArrayCounter', 'ArrayCounter_RBV', 'FWNImagesPerFile', 'FWNamePattern', 'SaveFiles', 'FilePath', 'FilePathExists_RBV'))
    def define_tetramm(self,prefix):
        self.tetramm = epics.Device(f'{prefix}', attrs=('Acquire', 'AcquireMode', 'Range', 'ValuesPerRead', 'AveragingTime', 'FastAveragingTime', 'FastAverageScan.SCAN','EmptyFreeList', 'TriggerMode', 'NumAcquired'))
        self.tetramm_filesave = epics.Device(f'{prefix}:netCDF1', attrs=('Capture', 'FilePath', 'FileName', 'FileNumber', 'FileTemplate', 'AutoIncrement', 'WriteFile','FileWriteMode', 'WriteStatus', 'FilePathExists_RBV'))

    def define_softglue(self,prefix):
        self.softglue = epics.Device(f'{prefix}:SG', attrs=('1_CLEAR_Signal.PROC', '2_CLEAR_Signal.PROC', 'UpCntr-1_CLEAR_Signal.PROC')) 
        self.softglue_dma = epics.Device(f'{prefix}:1acquireDma', attrs=('C','F', 'D', 'VALF', 'VALG', 'VALC'))

    def define_xmotor(self, prefix):
        self.x_motor =  epics.Motor(prefix)

    def define_xmotor(self, prefix):
        self.y_motor =  epics.Motor(prefix)

    def define_xmotor(self, prefix):
        self.r_motor =  epics.Motor(prefix)

    def define_inner_loop(self, prefix):
        self.inner_loop = epics.Device(f"{prefix}", attrs=('P1PV', 'R1PV', 'P2PV', 'NPTS', 'PDLY', 'P1SM', 'P2SM', 'P1PA', 'P2PA', 'ACQT', 'EXSC', 'SMSG' ))
        self.inner_loop.P1PV = self.x_motor.Name
        self.inner_loop.R1PV = f"{self.x_motor}.RBV"
        self.inner_loop.P2PV = self.y_motor.Name
        self.inner_loop.R2PV = f"{self.y_motor}.RBV"
        self.inner_loop.PASM = 2 #prior position
        self.inner_loop.P1AR = 0 #absolute
        self.inner_loop.P1SM = 1 #table mode x
        self.inner_loop.P2SM = 1 #table mode y
    
    def define_outer_loop(self, prefix):
        self.outer_loop = epics.Device(f"{prefix}", attrs=('P1PV', 'R1PV', 'P2PV', 'NPTS', 'PDLY', 'P1SM', 'P2SM', 'P1PA', 'P2PA', 'ACQT', 'EXSC', 'SMSG'))
        self.outer_loop.P1PV = self.r_motor.Name
        self.outer_loop.R1PV = f"{self.r_motor}.RBV"
        self.outer_loop.PASM = 2 #prior position
        self.outer_loop.P1AR = 0 #absolute
        self.outer_loop.P1SM = 1 #table mode r

    def define_struck(self,prefix):
        #trigger type, num images, file saving, arm, erase, start, 
        pass

    def define_xmap(self,prefix):
        #trigger type, num images, file saving, arm, erase, start, 
        pass

    def define_hydra_controller(self, prefix):
        innerScanStartingPoint = self.inner_loop.P1SP
        innerScanStepSize = self.inner_loop.P1SI
        innerScanWidth = self.inner_loop.P1WD
        innerScanNumPoints = self.inner_loop.NPTS
        fastPositionerDial = self.x_motor.DVAL
        triggerStart = fastPositionerDial + innerScanStepSize
        triggerEnd = fastPositionerDial + innerScanWidth
        numTriggers = innerScanNumPoints - 1

        scan2 = epics.Device(f"{prefix}", attrs=('Delay.VAL', 'Width.VAL', 'Polarity.VAL', 'Mode.VAL', 'StartPosition.VAL', 'EndPosition.VAL', 'NumTriggers.VAL', 'StartStopCalc.PROC'))
        epics.caput("2xfm:Hydra1:Delay.VAL", 0)
        epics.caput("2xfm:Hydra1:Width.VAL", 100)
        epics.caput("2xfm:Hydra1:Polarity.VAL", 0)
        epics.caput("2xfm:Hydra1:Mode.VAL",1)
        epics.caput("2xfm:Hydra1:StartPosition.VAL", triggerStart)
        epics.caput("2xfm:Hydra1:EndPosition.VAL", triggerEnd)
        epics.caput("2xfm:Hydra1:NumTriggers.VAL", numTriggers)
        epics.caput("2xfm:Hydra1:StartStopCalc.PROC",1)

    def setupxspress3_filesaving(self):
        print("setting up xspress3 file saving... \n")
        if self.XSPRESS3 is not None:
            file_path = epics.caget(self.savePath,as_string=True).split("mda")[0]+"flyXRF"
            # saveDate_fileName = self.savePath.split(":")[0]+(":saveData_fileName.VAL")
            # file_name = epics.caget(saveDate_fileName,as_string=True).split(".")[0]+"_"
            file_template = "%s%s_%d.hdf5"

            time.sleep(1)
            if self.XSPRESS3.FilePathExists_RBV!=1:
                print("file path does not exist!")
                try:
                    mnt = os.listdir("/mnt")
                except FileNotFoundError:
                    print("/mnt directory not found. batchpy needs to run on beamline machine. \n file saving setup failed")
                    mnt = None

                if mnt is None:
                    return

                elif len(mnt) == 0:
                    print("nothing in /mnt directory. micdata probably not mounted...")
                    return
                elif len(mnt)>0:
                    print("micdata mount point exists, checking if micdata mounted...")
                    subdir_len = len(mnt)
                    save_path_folders = file_path.split("/")[:4]
                    save_path_folders = [i for i in save_path_folders if i] #remove empty strings from list of strings
                    if len(os.listdir("/mnt/{}".format(mnt[0])))!=0:
                        print("micdata mounted, fixing file path...")

                        for i in range(subdir_len):
                            contents = os.listdir("/mnt/{}".format(mnt[i]))
                            for folder in save_path_folders:
                                if folder in contents:
                                    print("found {} in /mnt/{}/".format(folder,mnt[i]))
                                    new_filepath = "/mnt/{}/{}/{}".format(mnt[i],folder, file_path.split(folder)[1])
                                    file_path = new_filepath
                                    self.XSPRESS3.FilePath = file_path
                                    if self.XSPRESS3.FilePathExists_RBV != 1:
                                        try:
                                            print("file path does not exist: {}".format(file_path))
                                        except:
                                            pass

    def setup_eiger(self, x,y,t, params): 
        savedatadir = params['savedatadir']
        file_prefix = params['file_prefix']
        self.eiger.NumImages = params["npts"]
        self.eiger.NumExposures = params["npts"]
        self.eiger.TriggerMode = 3 #ext
        self.eiger.FWNamePattern = f"%s%s_%d"
        self.eiger.FilePath = f"{savedatadir}eiger"
        self.eiger.SaveFiles = f"{file_prefix}eiger"
        self.eiger.Acquire=1

    def setup_xspress3(self, x,y,t, params):
        savedatadir = params['savedatadir']
        file_prefix = params['file_prefix']
        self.xspress3.ERASE = 1
        self.xspress3.NumImages = params["npts"] 
        self.xspress3.EraseOnStart=0
        self.xspress3.TriggerMode = 3
        self.xspress3.Pva1.EnableCallbacks = 1
        self.xspress3_filesave.FilePath = f"{savedatadir}xspress3"
        self.xspress3_filesave.FileName = file_prefix
        self.xspress3_filesave.Autoincrement = 1
        self.xspress3_filesave.FileTemplate = f"%s%s_%d"
        self.xspress3_filesave.FileWriteMode = 1 #stream
        self.xspress3.Acquire = 1
        self.xspress3_filesave.Capture=1

    def setup_tetramm(self, x,y,t, params):
        savedatadir = params['savedatadir']
        file_prefix = params['file_prefix']
        self.tetramm.TriggerMode = 3
        self.tetramm.NumAcquired = params["npts"]
        self.tetramm.EmptyFreeList = 1
        self.tetramm.ValuesPerRead = 5
        self.tetramm.AveragingTime = 0.00005
        self.tetramm.FastAveragingTime = 0.00005
        self.tetramm_filesave.FilePath = f"{savedatadir}tetraMM"
        self.tetramm_filesave.FileName = file_prefix
        self.tetramm_filesave.Autoincrement = 1
        self.tetramm_filesave.FileTemplate = f"%s%s_%d"
        self.tetramm_filesave.FileWriteMode = 1 #stream        pass
        self.tetramm.Acquire = 1
        self.tetramm_filesave.Capture=1

    def setup_softglue_triggers(self, x,y,t, params):
        # sg.1_CLEAR_Signal.PROC
        # sg.2_CLEAR_Signal.PROC
        # sg.UpCntr-1_CLEAR_Signal.PROC
        pass

    def setup_struck(self,x_npts,step_size):
        if self.STRUCK is not None:
            innerScanNumPoints = x_npts
            innerScanStepSize = step_size
            fastPositionerResolution = self.x_motor.MRES
            stepsPerPixel = np.floor(np.abs(innerScanStepSize / fastPositionerResolution) + 0.0001)
            self.STRUCK.ChannelAdvance = 1
            self.STRUCK.PresetReal = 0.0
            self.STRUCK.NuseAll = innerScanNumPoints - 2

            #if using step pak,
            prescale = int(step_size/fastPositionerResolution)
            self.STRUCK.Prescale = prescale
            if innerScanStepSize < fastPositionerResolution:
                print("step size resolution greater than motor resolution!")
            #if using hydra, set prescale to 1.
            self.STRUCK.EraseAll = 1
            return

    def setup_xmap(self, x,y,t, params):
        #TODO: define trigger type, num images, file saving, etc. 
        pass

    def is_ready():
        #TODO: check detector arm status
        #TODO: check motors in_position
        pass

    

    def begin(self, x,y,t, params):
        #TODO: start this as own thread so as to not freeeze GUI
        self.setup_eiger(x,y,t,params)
        self.setup_tetramm(x,y,t,params)
        self.setup_xspress3(x,y,t,params)
        self.setup_softglue_triggers(x,y,t,params)
        self.x_motor.VELO = params["fast_velo"]
        self.y_motor.VELO = 0.5 #subject to change based on motor speed
        self.x_motor.VAL = x[0] #TODO: add wait=True
        self.y_motor.VAL = y[0] #TODO: add wait=True
        self.x_motor.VELO = params["dwell"]/params["step_size"]
        self.y_motor.VELO = 0.5
        self.done = False

        if not is_ready:
            self.done = True
            return
        while not is_ready:
            time.sleep(1)
            print("waiting for struck and motor")

        self.x_motor.VELO = self.scan_speed
        time.sleep(1)
        tick = time.time()
        self.cycle = 0
        read_history_xp3 = np.zeros(10)
        read_history_struck = np.zeros(10)
        self.outer.EXSC = 1
        while not self.done:
            self.before_outer()
            self.before_inner()
            self.after_inner()
            self.after_outer()
            self.check_struck_done()

            time.sleep(0.1)
            self.cycle+=1
            if self.cycle>50:
                self.timer_event(self.cycle)

            done = self.check_done()
            #only check done status after 100th cycle to avoid early termination
            if done and self.cycle>=100:
                tock = time.time() - tick
                if tock < 5:
                    print("scan terminated early going back to while loop")
                    self.done = False
                else:
                    self.saveData_message = epics.caget(self.savePath.split(":")[0] + ":saveData_message.VAL", as_string=True)
                    self.inner.NPTS = 1
                    self.outer.NPTS = 1
                    time.sleep(1)
                    finish = time.time() - tick
                    finish = round(finish,2)
                    print("finished in {} seconds.".format(finish))
                    self.cleanup()
                    self.done = True
        return True

    def start_monitor(self):
        #TODO: start this as own thread so as to not freeeze GUI
        #if paused or idle: 
            #do something
        #if not paused: 
            #check detector current frame, if unchanginc, report warning.
            #get position array, plot positions array 
            #get scaler, plot scaler intensity. 
            #get scan progress, update log
        pass

    def check_done(self):
        is_done = self.outer.SMSG == "SCAN Complete"
        return is_done

    def add_wait(self):
        self.inner.WAIT = 1
        return
    
    def pause(self):
        pause_pv = self.inner._prefix.split("scan")[0]+'scanPause.VAL'
        epics.caput(pause_pv,1)
        return

    def is_paused(self):
        pause_pv = self.inner._prefix.split("scan")[0]+'scanPause.VAL'
        paused = epics.caget(pause_pv)
        if self.inner.WCNT > 0 or paused == 1:
            return True
        else:
            return False

    def resume(self):
        self.cycle = 0
        self.inner.WAIT = 0
        pause_pv = self.inner._prefix.split("scan")[0]+'scanPause.VAL'
        epics.caput(pause_pv,0)
        return

    def abort(self):
        #TODO: if aborting at start of gui, self.inner will not be defined.
        abort_PV = self.inner._prefix.split("scan")[0]+"AbortScans.PROC"
        epics.caput(abort_PV,1)
        time.sleep(0.1)
        epics.caput(abort_PV,1)
        time.sleep(0.1)
        epics.caput(abort_PV,1)
        self.saveData_message = epics.caget(self.savePath.split(":")[0] + ":saveData_message.VAL", as_string=True)
        self.reset_detector()
        return

    def reset_xspress3(self):
        self.XSPRESS3.Acquire = 0
        self.XSPRESS3.ERASE = 1
        self.XSPRESS3.Capture = 0
        self.XSPRESS3.FileNumber = 0
        saveDate_fileName = self.savePath.split(":")[0]+(":saveData_fileName.VAL")
        scan_number_pv = self.savePath.split(":")[0]+(":saveData_scanNumber.VAL")
        number = epics.caget(scan_number_pv, as_string=True)
        scan_number = list("0000")
        scan_number[-len(number):] = list(number)
        scan_number = "".join(scan_number)
        file_name = epics.caget(saveDate_fileName,as_string=True).split("_")[0]+"_"+str(scan_number)
        self.XSPRESS3.FileName = file_name

    def open_scan_q():
        current_dir = os.path.dirname(os.path.realpath(__file__))+"/"
        fname = "q_list.json"
        valid_files = []
        #check if files are .json and contain "q_list" keyword.
        for i, file in enumerate(os.listdir(current_dir)):
            if file.endswith(".json"):
                with open(current_dir+file,'rb') as f:
                    contents = json.load(f)
                    if contents[0] == "q_list":
                        valid_files.append(file)
                    f.close()
        #if no  valid files exist, create new one.
        if len(valid_files) ==0:
            q_list = {}
            with open(current_dir + fname, 'wb') as f:
                json.dump(["q_list",q_list], f)
                f.close()
        with open(current_dir + fname,'rb') as f:
            contents = json.load(f)
            q_list = contents[1]
        q_list = json.dumps(q_list)
        return q_list
    
    def save_scan_q(q_list:str):
        #TODO: parse q_list from gui lines
        # q_list = json.loads(q_list)
        current_dir = os.path.dirname(os.path.realpath(__file__))+"/"
        valid_files = []
        for i, file in enumerate(os.listdir(current_dir)):
            if file.endswith(".json"):
                with open(current_dir+file,'rb') as f:
                    contents = json.load(f)
                    if contents[0] == "q_list":
                        valid_files.append(file)
                    f.close()
        fname = max(valid_files, key=os.path.getmtime)
        with open(current_dir + fname, 'wb') as f:
            json.dump(["q_list",q_list], f)
            f.close()
        return    

    def validate_params(self, params:str, x_limits:str="", y_limits:str="", r_limits:str=""):
        params = json.loads(params)
        limits = json.loads(limits)
        x_limits = limits["x_limits"]
        y_limits = limits["y_limits"]
        r_limits = limits["r_limits"]
        x_valid = True
        y_valid = True
        r_valid = True

        if params["generator"] == "scan_record":
            if x_limits=="" or y_limits=="": #if parameters specified but not motor limits
                x_valid = False 
                y_valid = False 
                return False, "one or more motor limits not speicified"
                
            elif x_limits!="" and y_limits!="": #if parameters and limits specified
                if params["generator"] == "scan_record":
                    x_valid = params["x_center"] + params["x_width"]/2 < x_limits["x_pos_lim"] and \
                                params["x_center"] - params["x_width"]/2 > x_limits["x_neg_lim"] and \
                                params["x_step"] / params["dwell"] * 1000 < x_limits["x_vel"]
                    y_valid = params["y_center"] + params["y_width"]/2 > y_limits["y_pos_lim"] and \
                                params["y_center"] - params["y_center"]/2 > y_limits["y_neg_lim"]

                elif params["generator"] == "profile_move":
                    x_pos, y_pos, time_arr = self.generate_trajectory(params)
                    x_vel, y_vel = self.calculate_velo(x_pos, y_pos, time_arr)
                    # x_accel, y_accel = self.calculate_accel(x_vel, y_vel) #need to rethink this, motor record accel is in Seconds not m/s**2
                    
                    x_valid = (x_pos<x_limits["x_pos_lim"]).any() & (np.abs(x_vel)<x_limits["x_velo"]).any() & (np.abs(x_accel)<x_limits["x_acc"]).any()
                    y_valid = (y_pos<y_limits["y_pos_lim"]).any() & (np.abs(y_vel)<y_limits["y_velo"]).any() & (np.abs(y_accel)<y_limits["y_acc"]).any()

        if params["geometry"]=="3D" and r_limits=="": #if 3D but no r_limits
            r_valid= False
        elif params["geometry"]=="3D" and r_limits!="": #if 3D but and r_limits
            r_valid = params["r_center"] + params["r_width"]/2 > r_limits["r_pos_lim"] and \
                        params["r_center"] - params["r_width"]/2 > r_limits["r_neg_lim"]
            
        msg = "X: {}, Y: {}, R: {}".format(x_valid, y_valid, r_valid)
        valid = x_valid & y_valid & r_valid
        return valid, msg

    def generate_trajectory(self, params):
        trajectory = params["trajectory"]
        if trajectory  == "snake":
            xpts, ypts, times = trajectories.snake(eval(params["dwell_time"]), eval(params["x_size"]),  eval(params["x_center"]), eval(params["y_center"]), eval(params["x_width"]), eval(params["y_width"]))
        elif trajectory == "raster":
            xpts, ypts, times = trajectories.raster(eval(params["dwell_time"]), eval(params["x_size"]),  eval(params["x_center"]), eval(params["y_center"]), eval(params["x_width"]), eval(params["y_width"]), 2)
        elif trajectory == "spiral":
            xpts, ypts, times = trajectories.spiral(eval(params["dwell_time"]), eval(params["radial_step"]), eval(params["step_size"]), eval(params["x_center"]), eval(params["y_center"]), eval(params["diameter"]))
        elif trajectory == "lissajous":
            xpts, ypts, times = trajectories.lissajous(eval(params["dwell_time"]), eval(params["step_Size"]),  eval(params["x_center"]), eval(params["y_center"]), eval(params["x_width"]), eval(params["y_width"]), eval(params["cycles"]), eval(params["x_freq"]), eval(params["y_freq"]))
        else:
            return
        return xpts, ypts, times

    def calculate_velo(self, x_pos, y_pos, time_arr):
        x_velo = np.gradient(x_pos)/time_arr
        y_velo = np.gradient(y_pos)/time_arr
        return x_velo, y_velo

    def calculate_accel(self, x_vel, y_vel, time_arr):
        x_accel = np.gradient(x_vel)/time_arr
        y_accel = np.gradient(y_vel)/time_arr
        return x_accel, y_accel

    def get_motor_limits(self, motor):
        try:
            limits = {"poslim": motor.POSLIM, "neglim": motor.NEGLIM, "vel": motor.VEL, "acc": motor.ACCL}
        except Exception as e:
            print(e)
            limits["x_pos_lim"] = ""
            limits["x_neg_lim"] = ""
            limits["x_vel"] = ""
            limits["x_acc"] = ""
        return limits

    def get_scan_eta(self, params):
        overhead = 1.2
        dummy, dummy, times = self.generate_trajectory(params)
        total_time = np.sum(times)*overhead
        return total_time

    def get_progress():
        #TODO: there is built in scan progress tool in scan record apparently. 
        pass
    