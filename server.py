import socket
from threading import Thread
import pickle
import os
import multiprocessing
import batch_backend
from datetime import datetime, timedelta
import numpy as np

#TODO:
# check if clients still connected by having client regularly send ping request as a heartbeat,
#   if no heartbeat received after X seconds, close that connection, terminate that thread, and remove thread from threads
#  startup server remotely
#  server check when client disconnects.

class BatchServer(object):
    def __init__(self):
        # self.stop = False
        self.threads = {}
        self.pid = None
        self.stop = False
        self.backend = batch_backend.BatchScan()

    def on_new_client(self, clientsocket, addr):
        print('Got connection from', addr, flush=True)
        while True:
            try:
                msg = clientsocket.recv(1024)
                msg = pickle.loads(msg)
                print(msg, flush=True)
                if msg == "close_connection":
                    self.disconnect_client(clientsocket, addr)
                    break
                elif msg == "stop_server":
                    self.stop_server(clientsocket)
                    break
                elif msg == "open_session":
                    pass
                elif msg == "save_session":
                    pass
                elif msg == "start_scan":
                    pass
                elif msg == "pause_scan":
                    pass
                elif msg == "abort_scan":
                    pass
                elif msg == "get_scan_status":
                    pass
                elif msg == "get_motor_limits":
                    pass
                elif msg == "get_scan_list":
                    pass
                elif msg == "get_eta":
                    pass
                elif msg == "get_settings":
                    pass
                elif msg == "get_Scan_progress":
                    pass
                elif msg == "update_settings":
                    pass
                elif msg == "update_scan_list":
                    pass
                elif msg == "connect_scan_record":
                    pass
                elif msg == "connect_xmap":
                    pass
                elif msg == "connect_xspress3":
                    pass
                elif msg == "connect_eiger":
                    pass
                elif msg == "connect_struck":
                    pass
                elif msg == "connect_profile_move":
                    pass
                elif msg == "connect_tetramm":
                    pass
                elif msg == "connect_softgluezynq":
                    pass
                elif msg == "setup_scan_record":
                    pass
                elif msg == "setup_xmap":
                    pass
                elif msg == "setup_xspress3":
                    pass
                elif msg == "setup_eiger":
                    pass
                elif msg == "setup_struck":
                    pass
                elif msg == "setup_profile_move":
                    pass
                elif msg == "setup_tetramm":
                    pass
                elif msg == "setups_softgluezynq":
                    pass
                elif msg == "get_test_array":
                    self.send_test_array(clientsocket)
                elif msg == "get_test_dict":
                    self.send_test_dict(clientsocket)
                    pass
                else:
                    msg = "unknown command: {}".format(msg)
                    print(msg)
                    msg = pickle.dumps(msg)
                    clientsocket.send(msg)

            except Exception as error:
                # if self.stop:
                #     break
                print("error with server")
                print(error)
                break
        return

    def start_server(self, host_addr):
        self.pid = os.getpid()
        print("server PID: {}".format(str(self.pid)))
        self.host = host_addr
        self.s = socket.socket()  # Create a socket object
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print(self.host)
        port = 22262  # Reserve a port for your service.
        print('Server started!')
        print('Waiting for clients...')
        try:
            self.s.bind((self.host, port))  # Bind to the port
            self.s.listen(5)  # Now wait for client connection.

        except Exception as error:
            print(error)
            print("trying again")
            # self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.shutdown(True)
            self.s.close()
            self.s = socket.socket()
            self.s.bind((self.host, port))
            self.s.listen(5)
            return
        while True:
            if self.stop:
                try:
                    self.s.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                break
            print("here")
            caddr = ThreadWithReturnValue(target=self.s.accept)
            caddr.start()
            c, addr = caddr.join()
            print(addr)
            # c, addr = self.s.accept()  # Establish connection with client.
            if len(self.threads) < 5 and addr[0] not in self.threads.keys():
                t = Thread(target=self.on_new_client, args=(c, addr))
                # t = multiprocessing.Process(target=self.on_new_client, args=(c, addr))
                t.start()
                self.threads[addr[0]] = t
                t.join()
            elif len(self.threads) == 5:
                print("maximum number of clients reached. Close some clients and before trying to reconnect ")
            else:
                print("address already in list of threads, reconnecting instead.")
                self.threads[addr[0]]._target(c, addr)
            print("number of clients connected: ", len(self.threads))


    def open_session(self):
        # #open all pkl files in cwd, set "last opened" status to 0 for all except current file.
        # current_dir = os.path.dirname(os.path.abspath(__file__))+"/"
        # file = QtWidgets.QFileDialog.getOpenFileName(self, "Open .pkl", current_dir, "*.pkl")
        # if file[0] == '':
        #     return
        # try:
        #     with open(current_dir+self.session_file,'rb') as f:
        #         contents = pickle.load(f)
        #         settings = contents[2]
        #         for line in lines:
        #             for item in settings[line]:
        #                 widget = item[0]
        #                 value = item[1]
        #                 if isinstance(vars(vars(self)[line])[widget], QtWidgets.QRadioButton):
        #                     vars(vars(self)[line])[widget].setChecked(value)
        #                 if isinstance(vars(vars(self)[line])[widget], QtWidgets.QPushButton):
        #                     vars(vars(self)[line])[widget].setChecked(value)
        #                 if isinstance(vars(vars(self)[line])[widget], QtWidgets.QComboBox):
        #                     vars(vars(self)[line])[widget].setCurrentIndex(value)
        #                 if isinstance(vars(vars(self)[line])[widget], QtWidgets.QLineEdit):
        #                     vars(vars(self)[line])[widget].setText(value)
        #                 if isinstance(vars(vars(self)[line])[widget], QtWidgets.QLabel):
        #                     vars(vars(self)[line])[widget].setText(value)
        #     f.close()
        #     return
        # except:
        #     print("cannot autoload session, or file not found")
        # return
        pass

    def save_session(self):
        # try:
        #     # print("autosaving session")
        #     cwd = os.path.dirname(os.path.abspath(__file__))+"/"
        #     file = self.session_file
        #     save_list = []
        #     lines = self.get_lines()
        #     params = self.get_params()
        #     settings = {}
        #     for param in params:
        #         settings[param] = []
        #
        #     for line in lines:
        #         for widget in line.keys():
        #             if isinstance(line[widget], QtWidgets.QRadioButton):
        #                 settings[widget].append(line[widget].isChecked())
        #             if isinstance(line[widget], QtWidgets.QPushButton):
        #                 if line[widget].isCheckable():
        #                     settings[widget].append(line[widget].isChecked())
        #             if isinstance(line[widget], QtWidgets.QComboBox):
        #                 settings[widget].append(line[widget].currentIndex())
        #             if isinstance(line[widget], QtWidgets.QLineEdit):
        #                 settings[widget].append(line[widget].text())
        #             if isinstance(line[widget], QtWidgets.QLabel):
        #                 settings[widget].append(line[widget].text())
        #
        #     with open(cwd+file, 'wb') as f:
        #         pickle.dump(["session",datetime.now(),settings], f)
        #         f.close()
        #
        # except IOError as e:
        #     print(e)
        #     print("cannot autosave upon close")
        pass

    def validate_motor_limits(self, scan_id):
        #TODO:
        # x_hlm = self.x_hlm
        # x_llm = self.x_llm
        # x_vmax = self.x_vmax
        # x_vmin = self.x_vmin
        # x_res = self.x_res
        # y_hlm = self.y_hlm
        # y_llm = self.y_llm
        # y_res = self.y_res
        # r_hlm = self.r_hlm
        # r_llm = self.r_llm
        # x_center = eval(self.x_center.text())
        # y_center = eval(self.y_center.text())
        # r_center = eval(self.r_center.text())
        # x_width = eval(self.x_width.text())
        # y_width = eval(self.y_width.text())
        # r_width = eval(self.r_width.text())
        # x_points = eval(self.x_points.text())
        # y_points = eval(self.y_points.text())
        # r_points = eval(self.r_points.text())
        # dwell_time = eval(self.dwell_time.text())
        #
        # velocity_violation = False
        # scan = [self.x_center, self.y_center, self.x_width, self.y_width, self.x_points, self.y_points, self.dwell_time]
        #
        # try:
        #     x_step = abs(x_width/x_points)
        #     y_step = abs(y_width/y_points)
        #     if x_vmax == 0:
        #         velocity_violation = False
        #     elif x_step/(dwell_time/1000) > x_vmax:
        #         velocity_violation = True
        #
        #     if x_step < x_res:
        #         print("step size smaller than x_motor resolution, cannot run scan. ")
        #         return False
        #
        #     if y_step < y_res:
        #         print("step size smaller than y_motor resolution, cannot run scan. ")
        #         return False
        # except ZeroDivisionError:
        #     velocity_violation = True
        #     pass
        #
        # if (x_center - abs(x_width)/2) <= x_llm or (x_center + abs(x_width)/2) >= x_hlm or (y_center - abs(y_width)/2) <= y_llm or (y_center + abs(y_width)/2) >= y_hlm:
        #     print((x_center - abs(x_width)/2), x_llm, (x_center + abs(x_width)/2), x_hlm, (y_center - abs(y_width)/2), y_llm, (y_center + abs(y_width)/2), y_hlm)
        #     print("scan outside motor limits")
        #     #TODO: Figure out how to add r_motor logic.
        #     #(r_center - r_width / 2) <= r_llm or (r_center + r_width / 2) >= r_hlm:
        #     return False
        #
        # if velocity_violation:
        #     print("step size / dwell time exceeds positioner velocity")
        #     return False
        # else:
        #     return True
        pass

    def disconnect_client(self,clientsocket, addr):
        msg = pickle.dumps("disconnecting client")
        clientsocket.send(msg)
        clientsocket.close()
        self.threads.pop(addr[0])
        return

    def stop_server(self, clientsocket):
        print("closing server")
        self.stop = True
        msg = pickle.dumps("stopping server")
        clientsocket.send(msg)
        clientsocket.close()

    def send_test_array(self,clientsocket):
        arr = ([1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 6])
        data = pickle.dumps(arr)
        clientsocket.send(data)
        #TODO: sending data over python socket of unknown size, setup a protocol.
        # https://stackoverflow.com/questions/24423162/how-to-send-an-array-over-a-socket-in-python

    def is_server_alive(self, host, port):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((host, port))
            return True
        except socket.error:
            return False
        finally:
            s.close()

    def save_log(self):
        pass

    def save_queue(self):
        pass

    def get_eta(self):
        pass

    def get_trajectory(self,scan_id):
        line, scan_id = self.get_checked_line()
        if line == None:
            return

        scan = self.get_scan(scan_id)
        #TODO: change list type to object type: line.x_center, line.x_width, etc
        # scan_type, x_center, x_width, x_npts, y_center, y_width, y_npts, dwell, r_center, r_width, r_npts
        try:
            if line["trajectory"].currentText() == "raster":
                x_line = np.arange(line[1] - abs(scan[2])/2, scan[1] + abs(scan[2])/2, abs(scan[2])/scan[3])
                x_coords = np.zeros((scan[6],scan[3]))
                for i in range(scan[6]):
                    x_coords[i] = x_line
                x_coords = np.ndarray.flatten(x_coords)

                y_line = np.arange(scan[4] - abs(scan[5])/2, scan[4] + abs(scan[5])/2, abs(scan[5])/scan[6])
                y_coords = np.zeros((scan[6], scan[3]))
                for i in range(scan[6]):
                    y_coords[i] = np.ones(scan[3])*y_line[i]
                y_coords = np.ndarray.flatten(y_coords)
                return x_coords, y_coords

            elif line["trajectory"].currentText() == "snake":
                x_line = np.arange(scan[1] - scan[2] / 2, scan[1] + scan[2] / 2, scan[2] / scan[3])
                x_coords = np.zeros((scan[6], scan[3]))
                for i in range(scan[6]):
                    if i%2 == 1:
                        x_coords[:i] = np.fliplr(x_line)
                    else:
                        x_coords[:i] = x_line
                x_coords = np.ndarray.flatten(x_coords)

                y_line = np.arange(scan[4] - scan[5] / 2, scan[4] + scan[5] / 2, scan[4] / scan[6])
                y_coords = np.zeros((scan[6], scan[3]))
                for i in range(scan[6]):
                    y_coords[:i] = np.ones(scan[3]) * y_line[i]
                y_coords = np.ndarray.flatten(y_coords)
                return x_coords, y_coords
            else:
                return
        except:
            return

    def get_scan_progress(self):
        try:
            x_pos = self.backend.x_motor.RBV
            start = self.backend.inner.P1SP
            end = self.backend.inner.P1EP
            width = self.backend.inner.P1WD
            points = self.backend.inner.NPTS
            faze = self.backend.inner.FAZE
            if faze == 8:
                current_x_pos = int(points)
            else:
                current_x_pos = int(points*(x_pos - start)/(width))
            current_y_pos = self.backend.outer.CPT
            return current_x_pos, current_y_pos
        except:
            return

    def get_datetime(self):
        now = datetime.now()
        day = now.strftime("%a")
        cal_day = now.day
        month = now.month
        year = now.year
        time = datetime.today().time()
        hour = time.hour
        minute = time.minute
        second = time.second
        formatted = "{} {}-{}-{} {}:{}:{}".format(day, month, cal_day, year, hour, minute, second)
        return formatted

class ThreadWithReturnValue(Thread):

    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args,
                                        **self._kwargs)

    def join(self, *args):
        Thread.join(self, *args)
        return self._return
#

# import server
# s = BatchServer()
# hostname = socket.gethostname()
# host = socket.gethostbyname(hostname)
# s.start_server(host)
# print("done")
# t = Thread(target=s.start_server, args=(host))

##get PID from terminal
# ps -ef | grep "python server.py"




