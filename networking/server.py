"""
Code to launch the tcp socket server that will both manage streaming and
send image processing results to the roborio
"""

import select
import socket
import threading
import time

HOST = '0.0.0.0' # For accepting connections from any device
PORT = 6000
BACKLOG = 5 # Maximum number of clients
SIZE = 1024 # Maximum message size

def create_socket_and_client_list():
    """
    Creates a socket that listens on the port and host specified as
    constants then returns the socket and an arrray for clients.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(BACKLOG)
    clients = [s]
    return (s, clients)

def broadcast(server_socket, clients, message):
    """
    Sends a message to all given clients.
    """
    for i in clients:
        if i is not server_socket:
            i.send(message.encode('utf-8'))

def AcceptClients(server_socket, clients, on_new_message):
    """
    Accepts connections from clients, calling a given function when a
    new message is received. This function should take two parameters -
    the socket that sent the data and the data that was sent.

    This function has a side effect of modifying the client array as new
    clients connect.
    """
    while True:
        # See if there is any activity
        inputReady, _, _ = select.select(clients, [], [])
        for x in inputReady:
            if x == server_socket:
                # Client has connected to the server
                client_socket, _ = server_socket.accept() # 2nd arg is address
                clients.append(client_socket)
            else:
                # A client did something
                data = x.recv(SIZE)
                if data:
                    # Client has sent something
                    on_new_message(x, data.decode('utf-8'))
                else:
                    # Client has disconnected
                    x.close()
                    clients.remove(x)

if __name__ == '__main__':
    sock, clis = create_socket_and_client_list()

    def new_message(_, data):
        print('Got {}'.format(data))
        broadcast(sock, clis, data)

    acceptThread = threading.Thread(target=AcceptClients,
                                    args=[sock, clis, new_message])
    acceptThread.start()

    try:
        while True:
            broadcast(sock, clis, 'hi\n')
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()
