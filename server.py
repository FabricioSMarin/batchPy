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


def on_new_client(clientsocket,addr):
    global stop_server
    print('Got connection from', addr, flush=True)
    while True:
        try:
            msg = clientsocket.recv(1024).decode('utf-8')
            if msg == "close":
                clientsocket.close()
                threads.remove(addr[0])
                break
            if msg == "stop":
                stop_server = True
                break
            print(addr, ' >> ', msg, flush=True)
            msg = "message received: {}".format(msg)
            clientsocket.send(bytes(msg, 'utf-8'))
        except Exception as error:
            print(error)
            break

global stop_server
hostname = socket.gethostname()
host = socket.gethostbyname(hostname)
s = socket.socket()         # Create a socket object
print(host)
port = 22262                # Reserve a port for your service.
print('Server started!')
print('Waiting for clients...')
stop_server = False
s.bind((host, port))        # Bind to the port
s.listen(5)                 # Now wait for client connection.
threads = []

while True:
    c, addr = s.accept()     # Establish connection with client.
    if len(threads) <5 and addr[0] not in [x.name for x in threads]:
        t = Thread(target=on_new_client, args=(c, addr))
        t.name = addr[0]
        t.start()
        threads.append(t)
    elif len(threads) == 5:
        print("maximum number of clients reached. Close some clients and before trying to reconnect ")
    else:
        print("address already in list of threads, reconnecting instead.")
    if stop_server:
        break
    print("number of clients connected: ", len(threads))

s.close()

