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
        timeout = 0.05
        #THESE INSTANCE VARS ARE IN A SPECIFIC ORDER, must match teh pkl file.
        self.ibw = ""
        self.iaw = ""
        self.obw = ""
        self.oaw = ""
        self.xp3 = ""
        self.xmap = ""
        self.struck = ""
        self.z = ""
        self.x = ""
        self.y = ""
        self.r = ""
        self.fscan1 = ""
        self.fscanH = ""
        self.delay_calc = ""
        self.savePath = ""
        self.scan1 = ""
        self.scan2 = ""
        self.scanH = ""
        self.restoresettings()


        if epics.devices.xspress3.Xspress3.PV(epics.Device,self.xp3+"det1:CONNECTED",timeout=timeout).value is not None:
            self.XSPRESS3 = epics.devices.xspress3.Xspress3(self.xp3)
            self.XSPRESS3._pvs["HDF1:FilePath"].put(self.savePath)
        else:
            self.XSPRESS3 = None
            print("xspress3  not connected")

        if epics.devices.struck.Struck(self.struck).Prescale is not None:
            self.STRUCK = epics.devices.struck.Struck(self.struck)
        else:
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

        if self.outer_before_wait is not None:
            self.outer_before_wait.value = 0
            self.Fscan1.BSPV = self.outer_before_wait.pvname
        else:
            self.Fscan1.BSPV = ""

        if self.inner_before_wait is not None:
            self.inner_before_wait.value = 0
            self.FscanH.BSPV = self.inner_before_wait.pvname
        else:
            self.FscanH.BSPV = ""

        if self.inner_after_wait is not None:
            self.inner_after_wait.value = 0
            self.FscanH.ASPV = self.inner_after_wait.pvname
        else:
            self.FscanH.ASPV = ""

        if self.outer_after_wait is not None:
            self.outer_after_wait.value = 0
            self.Fscan1.ASPV = self.outer_after_wait.pvname
        else:
            self.Fscan1.ASPV = ""

        if self.x_motor is None or self.y_motor is None or self.Fscan1 is None or self.FscanH is None \
                or self.Scan2 is None or self.ScanH is None or self.Scan1 is None:
            print("One or more crucial PVs not connected ")
        else:
            self.save_settings()

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

    def restoresettings(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))+"/"
        file = "default_settings.pkl"
        with open(current_dir+file,'rb') as f:
            contents = pickle.load(f)
            filetype = contents[0]
            last_opened = contents[1]
            settings = contents[2]
            f.close()

            for i, key in enumerate(self.__dict__.keys()):
                try:
                    if settings[i] == "":
                        settings[i] = "empty"
                    self.__dict__[key] = settings[i]
                except:
                    print("cannot put {} in {}".format(settings[i], key))
        return

    #copy scan record settings, save to file
    def save_settings(self):
        Fscan1_save = self.Fscan1.save_state()
        FscanH_save = self.FscanH.save_state()
        Scan1_save = self.Scan1.save_state()
        Scan2_save = self.Scan2.save_state()
        ScanH_save = self.ScanH.save_state()

        save_list = [Fscan1_save, FscanH_save, Scan1_save, Scan2_save, ScanH_save]

        with open('saved_settings.pkl', 'wb') as f:
            pickle.dump(save_list, f)
        return

    # for each scan: run it.
    def run_scans(self,scans):
        scan_type = "fly"
        if scan_type == "fly":
            for scan in scans:
                self.init_pvs(scan)
                self.reset_detector()
                self.x_motor.VELO = self.fast_speed
                self.x_motor.VAL = self.FscanH.P1SP
                self.y_motor.VAL = self.Fscan1.P1SP
                self.check_position()
                self.x_motor.VELO = self.scan_speed
                self.Fscan1.EXSC = 1
                done = False
                while not done:
                    self.check_busy()
                    done = self.Fscan1.EXSC == 0
                    print('scan is ongoing')
                    time.sleep(3.0)

        if scan_type == "step":
            for scan in scans:
                self.init_pvs(scan)
                self.x_motor.VELO = self.fast_speed
                self.x_motor.VAL = self.Scan1.P1SP
                self.y_motor.VAL = self.Scan2.P1SP
                self.check_position()
                self.x_motor.VELO = self.scan_speed
                self.Scan1.EXSC = 1
                done = False
                while not done:
                    self.check_busy()
                    done = self.Scan1.EXSC == 0
                    print('scan is ongoing')
                    time.sleep(3.0)
        self.cleanup()
        print('Completeted. Congratulations!')

    #check pvs and update
    def update_ui(self):
        #check if devices are connected
        #try to set PV in linedit
        #get PV and update linedit
        #every X seconds update linedit
        pass

    #restore scan record from file
    def restore_settings(self):
        with open('saved_settings.pkl', 'rb') as f:
            loaded_list = pickle.load(f)
        self.Fscan1.restore_state(loaded_list[0])
        self.FscanH.restore_state(loaded_list[1])
        self.Scan1.restore_state(loaded_list[2])
        self.Scan2.restore_state(loaded_list[3])
        self.ScanH.restore_state(loaded_list[4])
        return

    #set detector triggers in scan records
    def init_scan_record(self):
        scan_type = "fly"
        if scan_type == "fly":
            self.FscanH.T1PV = ""
            self.FscanH.T2PV = ""
            self.FscanH.T3PV = ""
            self.FscanH.T4PV = ""
            self.Fscan1.T1PV = ""
            self.Fscan1.T2PV = ""
            self.Fscan1.T3PV = ""
            self.Fscan1.T4PV = ""

            self.FscanH.P1PV = self.delay_calc
            self.Fscan1.P1PV = self.y_motor._prefix.split(".")[0]

            if self.STRUCK is not None:
                self.FscanH.T1PV = self.STRUCK._prefix + "EraseStart"
            else:
                pass
            if self.XMAP is not None:
                self.FscanH.T2PV = self.XMAP._prefix + "netCDF1:Capture"
                self.FscanH.T3PV = self.XMAP._prefix + "EraseStart"
            else:
                pass
            if self.XSPRESS3 is not None:
                self.Fscan1.T1PV = self.XSPRESS3._prefix + "det1:ERASE"
                self.Fscan1.T2PV = self.XSPRESS3._prefix + "HDF1:Capture"
                self.FscanH.T2PV = self.XSPRESS3._prefix + "det1:Acquire"
                self.Fscan1.T4PV = self.FscanH._prefix + "EXSC"
                self.XSPRESS3.TriggerMode = 3   #3 = external, 1=internal
            else:
                pass

            if self.inner_before_wait is not None: self.FscanH.BSPV = self.inner_before_wait.pvname
            else: self.FscanH.BSPV = ""

            if self.inner_after_wait is not None: self.FscanH.ASPV = self.inner_after_wait.pvname
            else: self.FscanH.ASPV = ""

            if self.outer_after_wait is not None: self.Fscan1.ASPV = self.outer_after_wait.pvname
            else: self.Fscan1.ASPV = ""

            if self.outer_before_wait is not None: self.FscanH.BSPV = self.outer_before_wait.pvname
            else: self.Fscan1.BSPV = ""

        if scan_type == "step":

            if self.STRUCK is not None:
                self.ScanH.T1PV = self.STRUCK._prefix + "EraseStart"
            else:
                pass

            if self.XMAP is not None:
                self.ScanH.T2PV = self.XMAP._prefix + "netCDF1:Capture"
                self.ScanH.T3PV = self.XMAP._prefix + "EraseStart"
            else:
                pass

            if self.XSPRESS3 is not None:
                self.ScanH.T4PV = self.XSPRESS3._prefix + "HDF1:Capture"
                self.Scan1.T1PV = self.ScanH._prefix + "EXSC"
                self.Scan1.T2PV = self.XSPRESS3._prefix + "det1:Acquire"
                self.Scan1.T3PV = self.XSPRESS3._prefix + "det1:ERASE"
                self.XSPRESS3.TriggerMode = 3   #internal
            else:
                pass

    def init_pvs(self, scan):
        scan_type = "fly"
        unit_sf = 1/1000
        xcenter, ycenter, xwidth, ywidth, xstep, ystep, dwell = scan[0]*unit_sf, scan[1]*unit_sf, scan[2]*unit_sf, \
                                                                scan[3]*unit_sf, scan[4]*unit_sf, scan[5]*unit_sf, \
                                                                scan[6]/1000

        if scan_type == "fly":
            self.FscanH.NPTS = int(np.ceil(xwidth/xstep))           #set number of points
            self.FscanH.P1WD = xwidth                               #set width
            self.FscanH.P1CP = xcenter                              #set center

            self.Fscan1.NPTS = int(np.ceil(ywidth/ystep))
            self.Fscan1.P1WD = ywidth
            self.Fscan1.P1CP = ycenter
            self.Fscan1.PDLY = int(3)
            #TODO: increase calcrecord delay to 3-3.5 from 0.25 seconds.

            abort_PV = self.FscanH._prefix.split(":")[0]+":FAbortScans.PROC"
            epics.caput(abort_PV,1)
            time.sleep(0.1)
            epics.caput(abort_PV,1)
            time.sleep(0.1)
            epics.caput(abort_PV,1)

            if self.XSPRESS3 is not None:
                self.XSPRESS3.NumImages = self.FscanH.NPTS - 2
                self.XSPRESS3.AcquireTime = dwell

        if scan_type == "step":
            self.ScanH.P1CP = xcenter
            self.ScanH.P1WD = xwidth
            self.ScanH.NPTS = int(np.ceil(xwidth / xstep))

            self.Scan1.P1CP = ycenter
            self.Scan1.P1WD = ywidth
            self.Scan1.NPTS = int(np.ceil(ywidth / ystep))

            abort_PV = self.ScanH._prefix.split(":")[0]+":AbortScans.PROC"
            epics.caput(abort_PV,1)
            time.sleep(0.1)
            epics.caput(abort_PV,1)
            time.sleep(0.1)
            epics.caput(abort_PV,1)

            if self.XSPRESS3 is not None:
                self.XSPRESS3.NumImages = self.Scan2.NPTS
                self.XSPRESS3.AcquireTime = dwell

        else:
            #TODO: reserve for future scan types
            pass

        self.fast_speed = 5
        self.scan_speed = xstep/dwell

        return

    def check_busy(self):
        # if self.beamline == "2ide":
        #     self.beamline
        self.before_outer()
        self.before_inner()
        self.after_inner()
        self.after_outer()

    def check_position(self):
        print('checking whether motors are in position')
        ready = abs(self.x_motor.VAL - self.x_motor.RBV) < 0.1 and abs(self.y_motor.VAL - self.y_motor.RBV) < 0.1
        retry = 0
        while not ready or retry > 5:
            print('\t Motors are not ready')
            try:
                self.x_motor.put(self.x_motor.VAL)
                self.y_motor.put(self.x_motor.VAL)
                time.sleep(0.1)
                ready = abs(self.x_motor.VAL - self.x_motor.VAL) < 0.1 and abs(self.y_motor.VAL - self.y_motor.VAL) < 0.1
                retry += 1
            except:
                retry += 1
                if retry > 5:
                    print("cant get motor pos")
                    break
        if retry > 5:
            print("Motors not in position")
        else:
            print('Motors are ready now!')

        return True

    def check_struck(self):
        struck_retry = 0
        if self.STRUCK is not None:
            not_done = self.STRUCK.Acquiring
            while not_done:
                status = self.STRUCK.Acquiring
                time.sleep(0.1)
                struck_retry+=1
                if struck_retry >=0:
                    print("struc might not ready")
                    self.STRUCK.StopAll = 0
                    return False
                else:
                    return True
            return True

    def check_readout_system(self):
        xp3_retry = 0
        status = 0
        if self.XSPRESS3 is not None:
            acquiring = self.XSPRESS3.Acquire_RBV
            arr_cntr = self.XSPRESS3.ArrayCounter_RBV

            while acquiring == 1 and arr_cntr > 0:
                status = self.XSPRESS3.Acquire_RBV
                time.sleep(0.1)
                xp3_retry+=1
                if xp3_retry >=0:
                    print("detecotor might not ready")
                    self.XSPRESS3.stop()
                    return False
                else:
                    return True
            return True

        if self.XMAP is not None:
            status_dict = {
            0: "Done",
            1: "Acquiring"}
            status = self.XMAP.Acquiring
            retry = 0
            while status != 0:
                status = self.XMAP.Acquiring
                time.sleep(0.1)
                retry+=1

            if retry > 5:
                print("detector taking a while to ready: {} ".format(status_dict[int(status)]))
            else:
                print("detector ready")
            return True

    def setup_struck(self):
        innerScanNumPoints = self.FscanH.NPTS
        innerScanStepSize = self.FscanH.P1SI
        fastPositionerResolution = self.x_motor.MRES
        stepsPerPixel = np.floor(np.abs(innerScanStepSize / fastPositionerResolution) + 0.0001)
        self.STRUCK.PresetReal = 0.0
        self.STRUCK.NuseAll = innerScanNumPoints - 2
        self.STRUCK.Prescale = 1
        self.STRUCK.CurrentChannel = 0

    def setup_triggers(self):

        innerScanStartingPoint = self.FscanH.P1SP
        innerScanStepSize = self.FscanH.P1SI
        innerScanWidth = self.FscanH.P1WD
        innerScanNumPoints = self.FscanH.NPTS
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
        #TODO: sometimes scan is stuck and scan record never sets busy to 1.
        if val == 1:
            not_paused = (self.Fscan1.pause != 1 and self.FscanH.WCNT == 0 and self.Fscan1.WCNT == 0)
            detector_ready = self.check_readout_system()
            struck_ready = self.check_struck()
            ready = not_paused and detector_ready and struck_ready
            retry = 0
            while not ready:
                time.sleep(0.1)
                retry+=1
                if retry >=10:
                    self.STRUCK.StopAll= 0
                    self.XSPRESS3.stop()
                    time.sleep(3)
            self.x_motor.VELO = self.scan_speed
            self.outer_before_wait.value = 0
        else:
            print("before outer done")
        return

    def before_inner(self):
        val = self.inner_before_wait.value
        if val == 1:
            self.setup_struck()
            self.setup_triggers()
            in_position = self.check_position()
            #TODO: reset Struck current channel
            not_paused = (self.Fscan1.pause != 1 and self.FscanH.WCNT == 0 and self.Fscan1.WCNT == 0)
            detector_ready = self.check_readout_system()
            struck_ready = self.check_struck()
            ready = not_paused and detector_ready and struck_ready and in_position
            retry = 0
            while not ready:
                time.sleep(0.1)
                retry+=1
                if retry >=10:
                    self.STRUCK.StopAll= 0
                    self.XSPRESS3.stop()
                    time.sleep(3)
            self.x_motor.VELO = self.scan_speed
            self.inner_before_wait.value = 0
        else:
            print("before inner done")
        return

    def after_inner(self):
        val = self.inner_after_wait.value
        if val == 1:
            self.XSPRESS3.stop()
            self.XSPRESS3.ERASE = 1
            self.STRUCK.StopAll = 1
            self.STRUCK.NuseAll = 0
            self.x_motor.VELO = self.fast_speed
            self.x_motor.VAL = self.FscanH.P1SP
            self.inner_after_wait.value = 0
        else:
            print("after inner done")
        return

    def after_outer(self):
        val = self.outer_after_wait.value
        if val == 1:
            self.reset_detector()
            self.outer_after_wait.value = 0
        else:
            print("after outer done")
        return

    def pause_scan(sefl, **kwargs):
        print(kwargs)

        if kwargs['value'] == 1:
            #TODO: Add wait to inner loop.
            #pause execution
            pass
        else:
            print("pause pressed, but scan unable to pause?")
        return

    def abort_scan(self, *value):

        if value == 1:
            abort_PV = self.FscanH._prefix.split(":")[0]+":FAbortScans.PROC"
            epics.caput(abort_PV,1)
            time.sleep(0.1)
            epics.caput(abort_PV,1)
            time.sleep(0.1)
            epics.caput(abort_PV,1)
            self.reset_detector()
        return

    def reset_detector(self):
        if self.XSPRESS3 is not None:
            self.XSPRESS3.stop()
            self.XSPRESS3.ERASE = 1

        if self.STRUCK is not None:
            self.STRUCK.StopAll = 1
            self.STRUCK.NuseAll = 0

        if self.XMAP is not None:
            # TODO: get XMAP stop PV
            # self.XMAP.StopAll == 1
            pass
        return

    def cleanup(self):
        self.restore_settings()
        self.reset_detector()
        return

batchscan = BatchSetup()
batchscan.init_scan_record()

'''
please enter the FLYSCAN prameters below:
scans [x-center(um), y-center.(um), x-width.(um), y-width.(um), x-stepsize.(um), Y-stepsize.(um), dwell.(ms)]
'''
#
# scans = [
# [1200,  0,    1800,     1800,     20,    20,    100],
# [1200,  0,    1800,     1800,     20,    20,    100],
# ]
# batchscan.run_scans(scans)
