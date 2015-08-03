# Tcp Chat server

import socket, select, os


def broadcast_data(message):
    for socket in CONNECTION_LIST:
        if socket != server_socket:
            try:
                socket.send(message)
            except:
                socket.close()


if __name__ == "__main__":
    RECV_BUFFER = 4096
    PORT = 8027

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", PORT))
    server_socket.listen(10)

    CONNECTION_LIST = {server_socket: 'server', }

    print "Chat started on port " + str(PORT)

    try:
        while 1:
            read_sockets, write_sockets, error_sockets = select.select(CONNECTION_LIST, [], [])
            for sock in read_sockets:
                if sock == server_socket:
                    sock_new, addr = server_socket.accept()
                    sock_new.send('Your name: ')
                    name = sock_new.recv(1024)[:-2]
                    CONNECTION_LIST[sock_new] = name
                    print "Client (%s, %s) connected" % addr

                    broadcast_data("%s entered room\n" % name)
                else:
                    data = sock.recv(RECV_BUFFER)
                    if data:
                        broadcast_data("\r" + str(CONNECTION_LIST[sock]) + ': ' + data)
    except KeyboardInterrupt:
        server_socket.close()
