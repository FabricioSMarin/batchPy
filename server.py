import socket
from threading import Thread
import pickle
import os
import multiprocessing
import batch_backend
from datetime import datetime, timedelta


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




