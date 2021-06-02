import socket
import threading


class Server:
    def __init__(self, name, auth=None, maxConn=120, maxConnReachTrigger=None):
        self.auth = auth
        self.name = name
        if maxConn > 1:
            self.maxConn = maxConn
        else:
            self.maxConn = 1

        self.trigger = maxConnReachTrigger

        # for storing all the connection data.
        self.connections = []

        # it will store response of main connection.
        # in this server, we can set only one connection as the main connection when we will fetch a response
        # we can fetch it in so easy way. just by calling function getMainCoonResponse().
        self.mainConnResponse = None

        # the final connection from which the user fetched the response.
        self.lastActivityConn = None

        # for internal use of server.
        self.PORT = 5555
        self.HEADER = 64
        self.FORMAT = "utf-8"
        self.IpAddress = None
        self.runningStatus = False

        # Server is listening for new connection or not is on the server it will decide on the basic on maxConn.
        self.serverListeningStatus = False

        # server socket, it will store the socket object that we create with the help os socket.
        self.server = None

    @staticmethod
    def createConnData(conn, addr, name=None, status=True):
        return {'name': name, 'conn': conn, 'addr': addr, 'response': [], status:status}

    def setTriggerOnMaxConnReach(self, trigger):
        self.trigger = maxConnReachTrigger

    def setAsMainConnection(self, name):
        for conn in self.connections:
            if name in conn:
                self.mainConnResponse = conn['response']
                return True
        return False

    def getMainConnResponse(self):
        return self.mainConnResponse.pop()

    def getResponse(self, name):
        for conn in self.connections:
            if name in conn:
                self.lastActivityConn = conn['response']
                return conn['response'].pop()
        return None

    def startServer(self):
        try:
            self.IpAddress = socket.gethostbyname(socket.gethostname())
            address = (self.IP_ADDRESS, self.PORT)
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind(address)
            connectionListenerThread = threading.Thread(target=self.connection_listener)
            connectionListenerThread.start()
        except:
            self.runningStatus = False
            return False
        self.runningStatus = True
        self.serverListeningStatus = True
        return True

    def connectionListener(self):
        self.server.listen()
        while self.serverListeningStatus and self.runningStatus:
            try:
                conn, addr = self.server.accept()
                connectionThread = threading.Thread(target=self.connectionHandler, args=(self.createConnData(conn, addr),))
                connectionThread.start()
            except:
                continue

    def connectionHandler(self, connData):
        connection = connData['conn']
        if self.auth is None:
            self.sendMessage(connection, {'auth': 'yes'})
        else:
            self.sendMessage(connection, {'auth': 'not'})
        while True:


    def receiveMessage(self, conn):
        try:
            msg_length = conn.recv(self.HEADER).decode(self.FORMAT)
        except ConnectionResetError:
            return False
        if msg_length:
            try:
                msg_length = int(msg_length)
            except:
                return False
            msg = conn.recv(msg_length)
            try:
                message = msg.decode(self.FORMAT)
            except UnicodeDecodeError:
                message = pickle.loads(msg)
            return message

    def sendMessage(self, conn, msg):
        if type(msg) == str:
            message = msg.encode(self.FORMAT)
        else:
            message = pickle.dumps(msg)
        msg_length = len(message)
        send_length = str(msg_length).encode(self.FORMAT)
        send_length += b" " * (self.HEADER - len(send_length))
        conn.send(send_length)
        conn.send(message)


class Server:
    connection = []

    def __init__(self, name, password):
        self.password = password
        self.name = name
        self.PORT = 5555
        self.HEADER = 64
        self.FORMATE = "utf-8"

        # creating a socket to make a server.
        self.IP_ADDRESS = socket.gethostbyname(socket.gethostname())
        self.ADDR = (self.IP_ADDRESS, self.PORT)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(self.ADDR)

        # variable to control thread.
        self.Server_Listen = True
        self.current_player = None
        self.current_player_name = None

        # creating an variable to store received message.
        self.received_response = []

        self.server_status = False

    def response(self):
        try:
            return self.received_response.pop()
        except IndexError:
            return None

    def connection_listener(self):
        self.server.listen()
        while self.Server_Listen and self.server_status:
            try:
                conn, addr = self.server.accept()
                print(f"Connection: {conn, addr}")
                new_connection = threading.Thread(target=self.handle_connection, args=(conn, addr))
                new_connection.start()
            except:
                return

    def stop(self):
        self.server_status = False
        self.server.close()
        # self.server.shutdown(1)
        self.connection.clear()

    def start(self):
        self.server_status = True
        self.IP_ADDRESS = socket.gethostbyname(socket.gethostname())
        self.ADDR = (self.IP_ADDRESS, self.PORT)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(self.ADDR)
        listener_thread = threading.Thread(target=self.connection_listener)
        listener_thread.start()

    def handle_connection(self, conn, addr):
        connection_data = self.createConnectionData(conn, addr)
        self.add_connection(connection_data)
        while connection_data['status'] and self.server_status:
            message = receive_msg(conn)
            print(message)
            if self.current_player != None:
                return
            if 'auth' in message:
                if self.auth_user(message['auth']):
                    if self.current_player == None:
                        self.current_player = connection_data
                        self.current_player_name = message['name']
                        self.remove_connection(connection_data)
                        self.close_all_temp_connection()
                        send_message(conn, {'response': 'accepted', 'name': self.name})
                    else:
                        send_message(conn, {'response': 'already_playing'})
                        self.remove_connection(connection_data)
                        return
            elif conn == self.current_player['conn']:
                self.received_response.append(message)
            else:
                self.remove_connection(connection_data)
                return

    def close_all_temp_connection(self):
        for connection in self.connection:
            connection['status'] = False

    def auth_user(self, password):
        if self.password == password:
            return True
        else:
            return False

    def createConnectionData(self, conn, addr):
        conn_data = {'conn': conn, 'ip': addr[0], 'port': addr[1], 'status': True}
        return conn_data

    def add_connection(self, data):
        self.connection.append(data)

    def remove_connection(self, data):
        try:
            self.connection.remove(data)
            return True
        except ValueError:
            return False

    def send_data(self, message):
        try:
            send_message(self.current_player['conn'], message)
        except:
            print("Fail to send data")
