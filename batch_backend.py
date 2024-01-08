#!/APSshare/anaconda/x86_64/bin/python

import epics
import epics.devices
from epics.devices import xspress3
from epics import caput, caget
from epics import PV
import time
import numpy as np
import pickle
import os

from datetime import datetime


class BatchSetup(object):
    #get pv names from gui and check pvs are connected
    def __init__(self):
        #THESE INSTANCE VARS ARE IN A SPECIFIC ORDER, must match teh pkl file.
        self.ibw = ""
        self.iaw = ""
        self.obw = ""
        self.oaw = ""
        self.xp3 = ""
        self.xmap = ""
        self.struck = ""
        self.z = ""
        self.y = ""
        self.x = ""
        self.r = ""
        self.fscan1 = ""
        self.fscanH = ""
        self.delay_calc = ""
        self.savePath = ""
        self.scan1 = ""
        self.scan2 = ""
        self.scanH = ""
        self.ca_addr_list = ""
        self.settings_vars = self.__dict__
        self.settings_vars = list(self.settings_vars)[:-1]
        # self.restore_settings()
        self.backend_ready = False
        self.done = False
        self.saveData_message = ""
        self.xp3_stuck = False
        self.struck_stuck = False
        self.event = False
        self.inner = None
        self.outer = None
        self.mca = None
        self.img = None
        self.dwell = 10
        self.fast_speed = 10

    def init_server(self):
        #TODO: start this in a thread
        from multiprocessing.connection import Listener, Client
        address = ('localhost', 6000)  # family is deduced to be 'AF_INET'
        srvr = Listener(address, authkey=b'secret password')
        conn = srvr.accept()
        while True:
            msg = conn.recv()
            # do something with msg
            conn.send("message received")
            if msg == 'close':
                conn.close()
                break
        srvr.close()

    def create_xspress3(self,prefix):
        try:
            xp3 = epics.Device(prefix+"det1:", attrs=("DetectorState_RBV", "NumImages", "AcquireTime",
                        "AcquireTime_RBV", "TriggerMode", "Acquire", "ERASE", "ArrayCounter_RBV",
                        "Capture", "Capture_RBV", "FilePath", "FileName", "FileTemplate", "FileNumber", "FilePathExists_RBV"))
            xp3._prefix = prefix
            epics.caput(prefix+"det1:TriggerMode",3)
            epics.caput(prefix+"det1:AutoIncrement",1)
            try:
                #old IOC does not have EraseOnStart, adding this incase running on old ioc.
                epics.caput(prefix+"det1:EraseOnStart",0)
            except:
                pass
        except:
            return None
        return xp3

    def setup_xspress3_filesaving(self):
        print("setting up xspress3 file saving... \n")
        if self.XSPRESS3 is not None:
            file_path = epics.caget(self.savePath,as_string=True).split("mda")[0]+"flyXRF"
            # saveDate_fileName = self.savePath.split(":")[0]+(":saveData_fileName.VAL")
            # file_name = epics.caget(saveDate_fileName,as_string=True).split(".")[0]+"_"
            file_template = "%s%s_%d.hdf5"
            self.XSPRESS3.FilePath = file_path
            time.sleep(1)
            if self.XSPRESS3.FilePathExists_RBV!=1:
                print("file path does not exist!")
                try:
                    mnt = os.listdir("/mnt")
                except FileNotFoundError:
                    print("/mnt directory not found. batchpy needs to run on beamline machine. \n file saving setup failed")
                    print("enter flyXRF path manually: i.e: /mnt/micdata1/2ide/2022-3/marin/flyXRF")
                    self.XSPRESS3.FilePath = "/mnt/micdata1/2ide/2022-3/marin/flyXRF"
                    time.sleep(1)
                    if self.XSPRESS3.FilePathExists_RBV != 1:
                        print("failed to mount /mnt/micdata1/2ide/2022-3/marin/flyXRF")
                        print("setting hardcoded path to user2idd home directory... : /home/beams/USER2IDD/local_xspress3_save")
                        self.XSPRESS3.FilePath = "/home/beams/USER2IDD/local_xspress3_save"
                    mnt = None

                if mnt is None:
                    # self.XSPRESS3.FileName = file_name
                    self.XSPRESS3.FileTemplate = file_template
                    return

                elif len(mnt) == 0:
                    print("nothing in /mnt directory. micdata probably not mounted...")
                    new_dir = os.path.expanduser("~")+"/local_xspress3_save"
                    path_exists = os.path.exists(new_dir)
                    print("saving to: {}".format(new_dir))
                    print("When convenient, have IT mount micdata before starting future scans.")

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
                                            print("file path does not exist, attemptint to create it...")
                                            os.system("mkdir {}".format(file_path))
                                        except:
                                            print("cannot create file path, check file path or permissions")
                self.XSPRESS3.FileTemplate = file_template

    def connect_pvs(self):
        timeout = 0.1
        try:
            tic = time.time()
            #TODO: might need to configure EPICS_CA_ADDR_LIST in client computer to talk to xspress3 PVS
            #do this in ~/.tcshrc file along with any other aliases and
            os.environ["EPICS_CA_ADDR_LIST"] = self.ca_addr_list
            # os.environ["EPICS_CA_ADDR_LIST"] = "164.54.113.18"
            self.XSPRESS3 = self.create_xspress3(self.xp3)
            if self.XSPRESS3 is None:
                raise
            self.setup_xspress3_filesaving()
            print("xspress3 setup time took: {} seconds".format(time.time()-tic))
        except Exception as e:
            print(e)
            self.XSPRESS3 = None
            print("xspress3 not connected")

        try:
            tic = time.time()
            try:
                self.STRUCK = epics.devices.struck.Struck(self.struck)
            except:
                self.STRUCK = None
                print("struck not connected")

            if epics.devices.mca.MultiXMAP.PV(epics.Device,self.xmap,timeout=timeout).value is not None:
                self.XMAP = epics.devices.mca.MultiXMAP(self.xmap)
            else:
                self.XMAP = None
                print("XMAP not connected")

            if epics.Motor.PV(epics.Device,self.x,timeout=timeout).value is not None:
                self.x_motor = epics.Motor(self.x)
            else:
                self.x_motor = None
                print("x-motor not connected")

            if epics.Motor.PV(epics.Device,self.y,timeout=timeout).value is not None:
                self.y_motor = epics.Motor(self.y)
            else:
                self.y_motor = None
                print("y-motor not connected")

            if epics.Motor.PV(epics.Device,self.z,timeout=timeout).value is not None:
                self.z_motor = epics.Motor(self.z)
            else:
                self.z_motor = None
                print("z-motor not connected")

            if epics.Motor.PV(epics.Device,self.r,timeout=timeout).value is not None:
                self.r_motor = epics.Motor(self.r)
            else:
                self.r_motor = None
                print("r-motor not connected")

            if epics.devices.scan.Scan.PV(epics.Device,self.fscan1,timeout=timeout).value is not None:
                self.Fscan1 = epics.devices.scan.Scan(self.fscan1, timeout=timeout)
            else:
                self.Fscan1 = None
                print("Fscan1 record not connected")

            if epics.devices.scan.Scan.PV(epics.Device,self.fscanH,timeout=timeout).value is not None:
                self.FscanH = epics.devices.scan.Scan(self.fscanH, timeout=timeout)
            else:
                self.FscanH = None
                print("FscanH record not connected")

            if epics.devices.scan.Scan.PV(epics.Device,self.scan1,timeout=timeout).value is not None:
                self.Scan1 = epics.devices.scan.Scan(self.scan1, timeout=timeout)
            else:
                self.Scan1 = None
                print("Scan1 record not connected")

            if epics.devices.scan.Scan.PV(epics.Device,self.scan2,timeout=timeout).value is not None:
                self.Scan2 = epics.devices.scan.Scan(self.scan2, timeout=timeout)
            else:
                self.Scan2 = None
                print("Scan2 record not connected")

            if epics.devices.scan.Scan.PV(epics.Device,self.scanH,timeout=timeout).value is not None:
                self.ScanH = epics.devices.scan.Scan(self.scanH, timeout=timeout)
            else:
                self.ScanH = None
                print("ScanH record not connected")

            #check if busy record exists/is connected
            self.inner_before_wait = epics.PV(self.ibw,connection_timeout=timeout)
            self.inner_after_wait = epics.PV(self.iaw,connection_timeout=timeout)
            self.outer_before_wait = epics.PV(self.obw,connection_timeout=timeout)
            self.outer_after_wait = epics.PV(self.oaw,connection_timeout=timeout)

            if self.outer_before_wait.connected:
                self.outer_before_wait.value = 0
                self.Fscan1.BSPV = self.outer_before_wait.pvname
                self.Fscan1.BSWAIT = 0
                self.Scan1.BSWAIT = 0
            else:
                if self.Fscan1 is not None:
                    self.Fscan1.BSPV = ""

            if self.inner_before_wait.connected:
                self.inner_before_wait.value = 0
                self.FscanH.BSPV = self.inner_before_wait.pvname
                self.FscanH.BSWAIT = 0
                self.ScanH.BSWAIT = 0
            else:
                if self.FscanH is not None:
                    self.FscanH.BSPV = ""

            if self.inner_after_wait.connected:
                self.inner_after_wait.value = 0
                self.FscanH.ASPV = self.inner_after_wait.pvname
                self.FscanH.ASWAIT = 0
                self.ScanH.ASWAIT = 0
            else:
                if self.FscanH is not None:
                    self.FscanH.ASPV = ""

            if self.outer_after_wait.connected:
                self.outer_after_wait.value = 0
                self.Fscan1.ASPV = self.outer_after_wait.pvname
                self.Fscan1.ASWAIT = 0
                self.Scan1.ASWAIT = 0
            else:
                if self.Fscan1 is not None:
                    self.Fscan1.ASPV = ""

            if self.x_motor is None or self.y_motor is None or self.Fscan1 is None or self.FscanH is None \
                    or self.Scan2 is None or self.ScanH is None or self.Scan1 is None:
                print("One or more crucial PVs not connected ")
                self.backend_ready = False
            else:
                self.backend_ready =True
                # self.save_settings()
            print("setting up all other pvs took: {} seconds".format(time.time()-tic))

        except:
            pass
        return

    def alt_scanning(self):
        #TODO: if no scan records specified, need to create alternate method of scanning and implement the following.
        #metho of signaling busy records
        #method of triggering (detector trigger PV fields)
        #method of beginning scan
        #method for pausing scan
        #method for continuing scan
        #method for aborting scan
        #mothod for SAVING metadata
        #method for defining what metadata to save
        pass

    def restore_settings(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))+"/"
        file = "default_settings.pkl"
        if os.path.isfile(current_dir+file):
            with open(current_dir+file,'rb') as f:
                contents = pickle.load(f)
                filetype = contents[0]
                last_opened = contents[1]
                settings = contents[2]
                f.close()

                for i, key in enumerate(self.settings_vars):
                    try:
                        if settings[i] == "":
                            settings[i] = "empty"
                        self.__dict__[key] = settings[i]
                    except:
                        return
                        # print("cannot put {} in {}".format(settings[i], key))
        return

    def open_settings(self, path):
        with open(path,'rb') as f:
            contents = pickle.load(f)
            filetype = contents[0]
            last_opened = contents[1]
            settings = contents[2]
            f.close()

            for i, key in enumerate(self.settings_vars):
                try:
                    if settings[i] == "":
                        settings[i] = "empty"
                    self.__dict__[key] = settings[i]
                    print("setting PV {} in {}".format(settings[i], key))
                except:
                    print("cannot put {} in {}".format(settings[i], key))
                    return
            try:
                save_list = ["settings", datetime.now(), settings, "default_settings.pkl", 1]
                cwd = os.path.dirname(os.path.abspath(__file__)) + "/"
                with open(cwd + "default_settings.pkl", 'wb') as f:
                    pickle.dump(save_list, f)
                    f.close()
                return
            except IOError as e:
                print(e)
        return

    #copy scan record settings, save to file
    def save_scanrecord_settings(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))+"/"
        file = "scanrecord_settings.pkl"
        Fscan1_save = self.Fscan1.save_state()
        FscanH_save = self.FscanH.save_state()
        Scan1_save = self.Scan1.save_state()
        Scan2_save = self.Scan2.save_state()
        ScanH_save = self.ScanH.save_state()
        save_list = [Fscan1_save, FscanH_save, Scan1_save, Scan2_save, ScanH_save]

        if os.path.exists(current_dir+file):
            with open(current_dir+file, 'rb') as f:
                pickle.dump(save_list, f)
        else:
            with open(current_dir+file, 'wb') as f:
                pickle.dump(save_list, f)
                f.close()
        return

    def timer_event(self, cycle):
        cycle_frequency = 5
        try:
            if cycle%cycle_frequency == 0:
                self.event = True
            else:
                self.event = False
        except:
            self.event = False
        return

    def run_scan(self,scan_type, x_center, x_width, x_npts, y_center, y_width, y_npts, dwell):
        self.done = False
        if scan_type == "fly":
            self.inner = self.FscanH
            self.outer = self.Fscan1
        elif scan_type == "step":
            self.inner = self.ScanH
            self.outer = self.Scan1

        self.reset_detector()

        is_ready = self.init_scan(scan_type, x_center, x_width, x_npts, y_center, y_width, y_npts, dwell)
        if not is_ready:
            self.cleanup()
            self.done = True
            return
        self.x_motor.VELO = self.fast_speed
        self.x_motor.VAL = self.inner.P1SP
        self.y_motor.VAL = self.outer.P1SP
        in_position = self.check_position()
        while not is_ready and not in_position:
            is_ready = self.init_scan(scan_type, x_center, x_width, x_npts, y_center, y_width, y_npts, dwell)
            in_position = self.check_position()
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
            # read_history_xp3, self.xp3_stuck = self.check_detector_stuck(self.cycle, read_history_xp3)
            # read_history_struck, self.struck_stuck = self.check_struck_stuck(self.cycle, read_history_struck)

            # if self.xp3_stuck or self.struck_stuck:
            #     read_history_xp3 = np.zeros(10)
            #     read_history_struck = np.zeros(10)

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

    def run_tomo(self,scan_type, x_center, x_width, x_npts, y_center, y_width, y_npts, dwell, r_center, r_width, r_npts):
        start = r_center - r_width//2
        end = r_center + r_width//2
        angles= np.linspace(start, end, r_npts)
        if len(angles)==0:
            self.run_scan(scan_type, x_center, x_width, x_npts, y_center, y_width, y_npts, dwell)
        else:
            for i in angles:
                self.r_motor.VELO = 5
                self.r_motor.VAL = i
                time.sleep(0.01)
                in_pos = self.check_r_position()
                self.r_motor.VELO = 1
                retry = 0
                while not in_pos:
                    in_pos = self.check_r_position()
                    retry+=1
                    if retry >=20:
                        print("rotation stage not in position, aborting current line and pausing at next line. ")
                        self.done = True
                        return
                self.run_scan(scan_type, x_center, x_width, x_npts, y_center, y_width, y_npts, dwell)

    #check pvs and update
    def update_ui(self):
        #check if devices are connected
        #try to set PV in linedit
        #get PV and update linedit
        #every X seconds update linedit
        pass

    #restore scan record from file
    def restore_scan_record(self):
        with open('default_settings.pkl', 'rb') as f:
            loaded_list = pickle.load(f)

        self.Fscan1.restore_state(loaded_list[0])
        self.FscanH.restore_state(loaded_list[1])
        self.Scan1.restore_state(loaded_list[2])
        self.Scan2.restore_state(loaded_list[3])
        self.ScanH.restore_state(loaded_list[4])
        return

    #set detector triggers in scan records
    def init_scan_record(self):
        try:
            caput(self.delay_calc.split(".")[0] + ".OUTN", self.x_motor._prefix.split(".")[0] + ".VAL")
            caput(self.delay_calc.split(".")[0] + "EnableCalc.VAL",1)
            caput(self.delay_calc.split(".")[0] + ".ODLY",1.5)
        except:
            print("setup error")
            return
        if self.FscanH is not None:
            self.FscanH.P1SM = 2
            self.FscanH.P1AR = 0
            self.FscanH.PASM = 1
            self.FscanH.ACQT = 1
            self.FscanH.T1PV = ""
            self.FscanH.T2PV = ""
            self.FscanH.T3PV = ""
            self.FscanH.T4PV = ""
            self.FscanH.P1PV = self.delay_calc

        if self.Fscan1 is not None:
            self.Fscan1.P1SM = 0
            self.Fscan1.P1AR = 0
            self.Fscan1.PASM = 1
            self.Fscan1.T1PV = ""
            self.Fscan1.T2PV = ""
            self.Fscan1.T3PV = ""
            self.Fscan1.T4PV = ""
            self.Fscan1.P1PV = self.y_motor._prefix.split(".")[0]

        if self.STRUCK is not None:
            self.FscanH.T3PV = self.STRUCK._prefix + "EraseStart"
        else:
            pass
        if self.XMAP is not None:
            self.FscanH.T2PV = self.XMAP._prefix + "netCDF1:Capture"
            self.FscanH.T3PV = self.XMAP._prefix + "EraseStart"
        else:
            pass
        if self.XSPRESS3 is not None:
            self.Fscan1.T1PV = self.XSPRESS3._prefix + "det1:Capture"
            self.Fscan1.T2PV = self.XSPRESS3._prefix + "det1:Acquire"
            self.Fscan1.T4PV = self.FscanH._prefix + "EXSC"
        else:
            pass

        if self.inner_before_wait is not None: self.FscanH.BSPV = self.inner_before_wait.pvname
        else: self.FscanH.BSPV = ""

        if self.inner_after_wait is not None: self.FscanH.ASPV = self.inner_after_wait.pvname
        else: self.FscanH.ASPV = ""

        if self.outer_after_wait is not None: self.Fscan1.ASPV = self.outer_after_wait.pvname
        else: self.Fscan1.ASPV = ""

        if self.outer_before_wait is not None: self.Fscan1.BSPV = self.outer_before_wait.pvname
        else: self.Fscan1.BSPV = ""

        if self.ScanH is not None:
            self.ScanH.P1SM = 2
            self.ScanH.P1AR = 0
            self.ScanH.PASM = 1
            self.ScanH.ACQT = 1
            self.ScanH.T1PV = ""
            self.ScanH.T2PV = ""
            self.ScanH.T3PV = ""
            self.ScanH.T4PV = ""
            self.ScanH.P1PV = self.delay_calc

        if self.Scan1 is not None:
            self.Scan1.P1SM = 0
            self.Scan1.P1AR = 0
            self.Scan1.PASM = 1
            self.Scan1.T1PV = ""
            self.Scan1.T2PV = ""
            self.Scan1.T3PV = ""
            self.Scan1.T4PV = ""
            self.Scan1.P1PV = self.y_motor._prefix.split(".")[0]
        if self.STRUCK is not None:
            self.ScanH.T3PV = self.STRUCK._prefix + "EraseStart"
        else:
            pass

        if self.XMAP is not None:
            self.ScanH.T2PV = self.XMAP._prefix + "netCDF1:Capture"
            self.ScanH.T3PV = self.XMAP._prefix + "EraseStart"
        else:
            pass

        if self.XSPRESS3 is not None:
            self.ScanH.T1PV = self.XSPRESS3._prefix + "det1:Capture"
            self.ScanH.T2PV = self.XSPRESS3._prefix + "det1:Acquire"
            self.Scan1.T4PV = self.ScanH._prefix + "EXSC"
            #! self.Scan1.T1PV = self.XSPRESS3._prefix + "det1:ERASE"
        else:
            pass

        if self.inner_before_wait is not None: self.ScanH.BSPV = self.inner_before_wait.pvname
        else: self.ScanH.BSPV = ""

        if self.inner_after_wait is not None: self.ScanH.ASPV = self.inner_after_wait.pvname
        else: self.ScanH.ASPV = ""

        if self.outer_after_wait is not None: self.Scan1.ASPV = self.outer_after_wait.pvname
        else: self.Scan1.ASPV = ""

        if self.outer_before_wait is not None: self.Scan1.BSPV = self.outer_before_wait.pvname
        else: self.Scan1.BSPV = ""


    def init_scan(self, scan_type, x_center, x_width, x_npts, y_center, y_width, y_npts, dwell):
        # unit_sf = 1/1000
        unit_sf = 1
        self.dwell = dwell
        dwell = dwell/1000
        try:
            x_step = abs(x_width/x_npts)
            y_step = abs(y_width/y_npts)
        except ZeroDivisionError:
            return

        if x_step < self.x_motor.MRES:
            print("step size smaller than x_motor resolution, cannot run scan. ")
            return False

        if y_step < self.y_motor.MRES:
            print("step size smaller than y_motor resolution, cannot run scan. ")
            return False

        if self.outer_before_wait.connected:
            self.outer_before_wait.value = 0

        if self.inner_before_wait.connected:
            self.inner_before_wait.value = 0

        if self.inner_after_wait.connected:
            self.inner_after_wait.value = 0

        if self.outer_after_wait.connected:
            self.outer_after_wait.value = 0

        if scan_type == "fly":
            abort_PV = self.inner._prefix.split("scan")[0] + 'AbortScans.VAL'

            if not (self.inner.FAZE ==0 or self.inner.FAZE ==12):
                epics.caput(abort_PV,1)
                time.sleep(0.1)
                epics.caput(abort_PV,1)
                time.sleep(0.1)
                epics.caput(abort_PV,1)

            self.inner.NPTS = x_npts           #set number of points
            self.inner.P1WD = x_width                               #set width
            self.inner.P1CP = x_center                              #set center

            self.outer.NPTS = y_npts
            self.outer.P1WD = y_width
            self.outer.P1CP = y_center
            self.outer.PDLY = 0.25

            self.scan_speed = x_step / dwell

            if self.XSPRESS3 is not None:
                self.XSPRESS3.NumImages = x_npts - 2
                self.XSPRESS3.AcquireTime = dwell

            if self.STRUCK is not None:
                self.setup_struck(x_npts,x_step)


        elif scan_type == "step":
            abort_PV = self.inner._prefix.split("scan")[0] + 'AbortScans.VAL'
            epics.caput(abort_PV,1)
            time.sleep(0.1)
            epics.caput(abort_PV,1)
            time.sleep(0.1)
            epics.caput(abort_PV,1)

            self.inner.P1CP = x_center
            self.inner.P1WD = x_width
            self.inner.NPTS = x_npts

            self.outer.P1CP = y_center
            self.outer.P1WD = y_width
            self.outer.NPTS = y_npts

            self.scan_speed = x_step / dwell

            if self.XSPRESS3 is not None:
                self.XSPRESS3.NumImages = x_npts - 2
                self.XSPRESS3.AcquireTime = dwell
                # self.XSPRESS3.TriggerMode = 1
                # try:
                    # epics.caput(self.XSPRESS3._prefix+"det1:EraseOnStart",1)
                # except:
                #     print("some PVs not available for this ioc")

        else:
            #TODO: reserve for future scan types
            pass

        return True

    def check_done(self):
        # is_done = self.Fscan1.FAZE == 0 or self.Fscan1.FAZE == 12 or self.Fscan1.SMSG == "SCAN Complete"
        is_done = self.outer.SMSG == "SCAN Complete"
        # is_done = self.Fscan1.CPT == self.Fscan1.NPTS and self.Fscan1.EXSC == 0 and self.FscanH.CPT == self.FscanH.NPTS and self.FscanH.EXSC == 0
        return is_done


    def check_position(self):
        ready = abs(self.x_motor.VAL - self.x_motor.RBV) < 0.1 and abs(self.y_motor.VAL - self.y_motor.RBV) < 0.1
        retry = 0
        while not ready or retry > 5:
            try:
                self.x_motor.VELO = self.fast_speed
                self.x_motor.VAL = self.x_motor.VAL
                self.y_motor.VAL = self.y_motor.VAL
                ready = abs(self.x_motor.VAL - self.x_motor.VAL) < 0.1 and abs(self.y_motor.VAL - self.y_motor.VAL) < 0.1
                retry += 1
            except:
                retry += 1
                if retry > 5:
                    self.x_motor.VELO = self.scan_speed
                    break
        if retry > 5:
            self.x_motor.VELO = self.scan_speed
            return False
        else:
            self.x_motor.VELO = self.scan_speed
            return True
    def check_r_position(self):
        val = abs(self.r_motor.VAL - self.r_motor.RBV)
        ready = val < 0.1
        retry = 0
        while not ready:
            try:
                self.r_motor.VAL = self.r_motor.VAL
                time.sleep(0.1)
                new_val = abs(self.r_motor.VAL - self.r_motor.RBV)
                if abs(new_val-val) < 0.1:
                    retry+=1
                else:
                    ready = new_val < 0.1
            except:
                retry += 1
            if retry > 10:
                break
        if retry > 10:
            return False
        else:
            return True

    def check_struck(self):
        struck_retry = 0
        if self.STRUCK is not None:
            struck_ready = self.STRUCK.CurrentChannel == 0
            while not struck_ready:
                struck_retry+=1
                print("struck retrying...")
                self.STRUCK.StopAll = 0
                self.STRUCK.Acquiring = 0
                self.STRUCK.EraseAll = 1
                struck_ready = self.STRUCK.CurrentChannel == 0
                if struck_retry >=10:
                    return False
            return True

    def check_struck_done(self):
        if self.STRUCK is not None:
            struck_done = self.STRUCK.NuseAll == self.STRUCK.CurrentChannel
            if struck_done:
                self.STRUCK.EraseAll = 1
                self.STRUCK.Acquiring = 0
                return True

    # def check_struck_stuck(self, cycle, read_history):
    #     cycle_frequency = 15
    #     if self.STRUCK is None:
    #         return read_history, False
    #     else:
    #         pass
    #         if cycle%cycle_frequency == 0:
    #             i = cycle//cycle_frequency%10
    #             read_history[i] = self.STRUCK.CurrentChannel
    #             if cycle//cycle_frequency >=cycle_frequency:
    #                 if read_history[0] == read_history[-1] and self.inner.FAZE !=0 and self.inner.FAZE!=12 and not self.is_paused():
    #                     print("STRUCK may be stuck.. ")
    #                     return read_history, True
    #                 else:
    #                     return read_history, False
    #             else:
    #                 return read_history, False
    #         else:
    #             return read_history, False

    # def check_detector_stuck(self, cycle, read_history):
    #     cycle_frequency = 15
    #     try:
    #         alive = epics.caget(self.XSPRESS3._prefix + "det1:CONNECTED")
    #         if not alive:
    #             print("Xspress3 IOC is down. pausing scan...")
    #             return read_history, True
    #         else:
    #             if cycle%cycle_frequency == 0: #check every tenth cycle
    #                 i = cycle//cycle_frequency%10 #every thenth cycle revolving index
    #                 read_history[i] = epics.caget(self.XSPRESS3._prefix+"det1:ArrayCounter_RBV")
    #                 if cycle//cycle_frequency >=cycle_frequency:
    #                     if read_history[0] == read_history[-1] and self.inner.FAZE !=0 and self.inner.FAZE!=12 and not self.is_paused():
    #                         print("detector may be stuck.. ")
    #                         return read_history, True
    #                     else:
    #                         return read_history, False
    #                 else:
    #                     return read_history, False
    #             else:
    #                 return read_history, False
    #     except:
    #         return read_history, True

    def check_readout_system(self):
        xp3_retry = 0
        if self.XSPRESS3 is not None:
            acquiring = self.XSPRESS3.Acquire
            arr_cntr = self.XSPRESS3.ArrayCounter_RBV

            # current_line = self.Fscan1.CPT
            # capture_ready = self.XSPRESS3.Capture_RBV
            state = self.XSPRESS3.DetectorState_RBV #[idle, acquire, readout, correct, saving, aborting, error, waiting, init, disconnected, aborted]
            path_exists = self.XSPRESS3.FilePathExists_RBV
            xp3_retry = 0
            if path_exists == 0:
                print("file path does not exist.. cannot save to micdata or local user. \n pausing scan")
                self.add_wait()
                return False
            if state == 9:
                print("xspress3 disconnected.")
                return False
            if state == 6:
                print("xspress3 in error state")
                return False
            while xp3_retry <=10:
                # if acquiring==1 and arr_cntr==0 and file_number==self.outer.CPT and capture_ready==1:
                if arr_cntr==0:
                    return True
                if arr_cntr!=0:
                    self.XSPRESS3.ERASE=1
                # if capture_ready!=1:
                #     self.XSPRESS3.Capture=1
                # if acquiring !=1:
                #     self.XSPRESS3.Acquire = 1
                # acquiring = self.XSPRESS3.Acquire
                arr_cntr = self.XSPRESS3.ArrayCounter_RBV
                current_line = self.outer.CPT
                # capture_ready = self.XSPRESS3.Capture_RBV
                xp3_retry+=1

            # while acquiring == 1: #if num frames read at the start of acquisition is not 0, reset it.
            #     arr_cntr = self.XSPRESS3.ArrayCounter_RBV
            #     if arr_cntr > 0:
            #         self.XSPRESS3.Acquire = 0
            #         # self.XSPRESS3.
            #         xp3_retry += 1
            #     elif xp3_retry >=10:
            #         return False

                # else:
                #     return True
                # xp3_retry+=1

            return True

        if self.XMAP is not None:
            status_dict = {
            0: "Done",
            1: "Acquiring"}
            status = self.XMAP.Acquiring
            retry = 0
            while status != 0:
                status = self.XMAP.Acquiring
                retry+=1

            if retry > 5:
                print("detector taking a while to ready: {} ".format(status_dict[int(status)]))
            else:
                print("detector ready")
            return True

    def setup_struck(self,x_npts,step_size):
        if self.STRUCK is not None:
            innerScanNumPoints = x_npts
            innerScanStepSize = step_size
            fastPositionerResolution = self.x_motor.MRES
            stepsPerPixel = np.floor(np.abs(innerScanStepSize / fastPositionerResolution) + 0.0001)
            self.STRUCK.ChannelAdvance = 1
            #TODO: add pvs to make sure client wait options are set to "Disable" and "Done"
            # self.STRUCK.EnableClientWait = 0
            # self.STRUCK.ClientWait = 0
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

    def setup_triggers(self):

        innerScanStartingPoint = self.inner.P1SP
        innerScanStepSize = self.inner.P1SI
        innerScanWidth = self.inner.P1WD
        innerScanNumPoints = self.inner.NPTS
        fastPositionerDial = self.x_motor.DVAL

        triggerStart = fastPositionerDial + innerScanStepSize
        triggerEnd = fastPositionerDial + innerScanWidth
        numTriggers = innerScanNumPoints - 1

        epics.caput("2xfm:Hydra1:Delay.VAL", 0)
        epics.caput("2xfm:Hydra1:Width.VAL", 100)
        epics.caput("2xfm:Hydra1:Polarity.VAL", 0)
        epics.caput("2xfm:Hydra1:Mode.VAL",1)
        epics.caput("2xfm:Hydra1:StartPosition.VAL", triggerStart)
        epics.caput("2xfm:Hydra1:EndPosition.VAL", triggerEnd)
        epics.caput("2xfm:Hydra1:NumTriggers.VAL", numTriggers)
        epics.caput("2xfm:Hydra1:StartStopCalc.PROC",1)
        time.sleep(.25)
        return

    def before_outer(self):
        val = self.outer_before_wait.value
        if val == 1:
            not_paused = (self.outer.pause != 1 and self.inner.WCNT == 0 and self.outer.WCNT == 0)
            print(not_paused)
            ready = not_paused

            retry = 0
            while not ready:
                retry+=1
                not_paused = (self.outer.pause != 1 and self.inner.WCNT == 0 and self.outer.WCNT == 0)
                ready = not_paused
                if retry >=10:
                    print("before outer retry >10")
            self.x_motor.VELO = self.scan_speed
            self.outer_before_wait.value = 0
        else:
            pass
        return

    def before_inner(self):
        val = self.inner_before_wait.value
        if val == 1:
            in_position = self.check_position()
            not_paused = (self.inner.pause != 1 and self.inner.WCNT == 0 and self.outer.WCNT == 0)
            detector_ready = self.check_readout_system()
            struck_ready = self.check_struck()
            ready = not_paused and detector_ready and struck_ready and in_position

            retry = 0
            while not ready:
                print("not ready...")
                if not struck_ready:
                    print("struck not ready")
                    struck_ready = self.check_struck()
                if not detector_ready:
                    print("detector not ready")
                    detector_ready = self.check_readout_system()
                if not in_position:
                    print("not in position..")
                    in_position = self.check_position()
                if not not_paused:
                    print("paused")
                    not_paused = (self.outer.pause != 1 and self.inner.WCNT == 0 and self.outer.WCNT == 0)
                ready = not_paused and detector_ready and struck_ready and in_position

                # retry+=1
                # if retry >=10:
                #     print("before inner retrying...")
                #     if not struck_ready:
                #         self.STRUCK.StopAll= 0
                #     # if not detector_ready:
                #     #     self.XSPRESS3.Acquire = 0
                #     if not in_position:
                #         self.inner_before_wait.value = 1
                #         return
                #     if not not_paused:
                #         return

            self.x_motor.VELO = self.scan_speed
            self.inner_before_wait.value = 0
        else:
            pass
        return

    def after_inner(self):
        val = self.inner_after_wait.value
        if val == 1:
            # self.XSPRESS3.Acquire = 0
            if self.STRUCK is not None:
                self.STRUCK.StopAll = 1
            #TODO: not sure if good idea to caget this after each loop... maybe better to read file after acquisition.
            # self.mca = self.XSPRESS3.get("MCA1:ArrayData")

            self.x_motor.VELO = self.fast_speed
            self.x_motor.VAL = self.inner.P1SP
            self.inner_after_wait.value = 0
        else:
            pass
        return

    def after_outer(self):
        val = self.outer_after_wait.value
        if val == 1:
            # self.reset_detector()
            self.img = self.get_scan_result()
            self.outer_after_wait.value = 0
        else:
            pass
        return

    def get_scan_result(self):
        pass
        #TODO: get file path+name
        # open as hdf5
        # get array data
        # close h5 file
        # create empty array of size of scan
        # sum each array per pixel
        # fill empty array with new values
        # return new array

    def add_wait(self):
        self.inner.WAIT = 1
        return
    def pause_scan(self):
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

    def continue_scan(self):
        self.cycle = 0
        self.inner.WAIT = 0
        pause_pv = self.inner._prefix.split("scan")[0]+'scanPause.VAL'
        epics.caput(pause_pv,0)
        return

    def abort_scan(self):
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

    def reset_detector(self):
        if self.XSPRESS3 is not None:
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

        if self.STRUCK is not None:
            self.STRUCK.StopAll = 1
            self.STRUCK.NuseAll = 0
            self.STRUCK.Acquiring = 0

        if self.XMAP is not None:
            # TODO: get XMAP stop PV
            # self.XMAP.StopAll == 1
            pass
        return

    def cleanup(self):
        # self.restore_scan_record()
        # self.reset_detector()
        self.inner_before_wait.value = 0
        self.inner_after_wait.value = 0
        self.outer_before_wait.value = 0
        self.outer_after_wait.value = 0
        return