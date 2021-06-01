import socket


class Server:
    def __init__(self, name, auth=None, maxConn=1, maxConnReachTrigger=None):
        if auth is not None:
            self.username = auth['username']
            self.password = auth['password']
        self.name = name
        if maxConn > 1:
            self.maxConn = maxConn
        else:
            self.maxConn = 1

        self.trigger = maxConnReachTrigger

        # for storing all the connection data.
        self.connections = []

        # it will store response of main connection.
        # in this server we can set only one connection as main connection that when we will fetch response we can
        # in so easy way. just by calling function getMainCoonResponse().
        self.mainConnResponse = None


    def createConnData(self, name, conn, addr):
        return {'name': name, 'conn': conn, 'addr': addr, 'response': []}

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
