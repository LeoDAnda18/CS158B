import click
import socket
import threading


class ClientThread (threading.Thread):
    def __init__(self, cli, username):
        threading.Thread.__init__(self)
        self.cli = cli
        self.username = username

    def run(self):  # 3) clientThread will run.
        broadcast("joined: " + self.username)  # 4) Broadcast new user joined.
        self.cli.settimeout(30)  # 5) set it so that if client sent no message for 30 seconds, kick.
        try:
            while True:
                message = self.cli.recv(1024).decode('utf-8')  # 6) Listen indefinitely for a client message.
                if not message:
                    continue
                else:
                    determine_message(message, self.username)  # 7) determine type of message received.
        except socket.timeout:  # 9) handle disconnects and send 'username left' message.
            print('no message from ' + self.username + '. Disconnecting ' + self.username + '.')
            remove_client(self.username)
            broadcast("left: " + self.username)
            self.cli.close()
        except ConnectionResetError:
            print('Client ' + self.username + ' disconnected.')
            remove_client(self.username)
            broadcast("left: " + self.username)
            self.cli.close()

    def send(self, data):
        self.cli.sendall(data.encode('utf-8'))


clients = set()
usernames = set()


def clean_message(mess, username):  # cleanup function. replaces mess: with mess-username:
    new = mess.split(' ')
    new[0] = "mess-" + username + ": "  # replace mess with mess-name:
    temp = " ".join(new)
    return temp.replace(' ', '', 1)  # replace removes the beginning space added when doing " ".join(new).


# 8) determining the type of message.
def determine_message(mess, username):
    if "mess:" in mess:
        new_message = clean_message(mess, username)
        broadcast(new_message)
    elif "whoisthere:" in mess:
        send_list(username)
    elif "alive:" in mess:
        ack_alive(username)
    else:  # message type not supported.
        for client in clients:
            if client.username != username:
                continue
            else:
                client.send("Message not supported")


# 8a) Broadcasting the received message to all clients.
def broadcast(mess):
    for client in clients:
        client.send(mess)


# 8b) sending a list of connected clients to asking client.
def send_list(username):
    for client in clients:
        if client.username != username:
            continue
        else:
            for user in usernames:
                client.send("present: " + user + "\n")
            client.send("present:")


# 8c) sending ack of alive message.
def ack_alive(username):
    for client in clients:
        if client.username != username:
            continue
        else:
            client.send("alive:")


# 9) removes client and respective username from the sets containing clients and user names.
def remove_client(username):
    for client in clients:
        if client.username != username:
            continue
        else:
            clients.remove(client)
            usernames.remove(username)
            return


@click.command()
@click.argument('port', type=click.INT)
def do_server(port):  # 1 Set up server and wait for clients to connect.
    'simple program to listen on a socket and start a thread'
    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serv.bind(("", port))
    serv.listen(10)
    while True:  # 2 once client connects, add client and username to their respective set and start clientThread.
        cli, caddr = serv.accept()
        username = cli.recv(24).decode('utf-8')
        ct = ClientThread(cli, username)
        clients.add(ct)
        usernames.add(username)
        ct.start()


if __name__ == '__main__':
    do_server()
