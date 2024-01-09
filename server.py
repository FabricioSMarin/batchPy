import socket
from threading import Thread


# TODO: problems/challenges
#  check if server still listening
#  establish client/server connection
#  establish client/server connection from new client
#  re-establish connection after client disconnects
#  startup server remotely
#  server check when client disconnects.

#TODO:
# DONE establish connection
# DONE re-establish connection
# DONE check number of clients connected in threads list
# DONE connect from client computer
# check if clients still connected by having client regularly send ping request as a heartbeat,
#   if no heartbeat received after X seconds, close that connection, terminate that thread, and remove thread from threads

class BatchServer(object):
    #get pv names from gui and check pvs are connected
    def __init__(self):
        self.stop = False
        self.threads = []

    def on_new_client(self, clientsocket, addr):
        global stop_server
        print('Got connection from', addr, flush=True)
        while True:
            try:
                msg = clientsocket.recv(1024).decode('utf-8')
                if msg == "close":
                    clientsocket.close()
                    self.threads.remove(addr[0])
                    break
                if msg == "stop":
                    self.stop = True
                    break
                print(addr, ' >> ', msg, flush=True)
                msg = "message received: {}".format(msg)
                clientsocket.send(bytes(msg, 'utf-8'))
            except Exception as error:
                print(error)
                break

    def start_server(self):
        hostname = socket.gethostname()
        self.host = socket.gethostbyname(hostname)
        self.s = socket.socket()  # Create a socket object
        print(self.host)
        port = 22262  # Reserve a port for your service.
        print('Server started!')
        print('Waiting for clients...')
        self.s.bind((self.host, port))  # Bind to the port
        self.s.listen(5)  # Now wait for client connection.
        while True:
            c, addr = self.s.accept()  # Establish connection with client.
            if len(self.threads) < 5 and addr[0] not in [x.name for x in self.threads]:
                t = Thread(target=self.on_new_client, args=(c, addr))
                t.name = addr[0]
                t.start()
                self.threads.append(t)
            elif len(self.threads) == 5:
                print("maximum number of clients reached. Close some clients and before trying to reconnect ")
            else:
                print("address already in list of threads, reconnecting instead.")
            if self.stop:
                break
            print("number of clients connected: ", len(self.threads))
        self.stop_server()
    def stop_server(self):
        self.s.close()
        return




