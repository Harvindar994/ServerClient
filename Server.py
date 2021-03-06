import socket
import threading
import time
import pickle

# default messages.
DISCONNECT = '!DISCONNECT'
CONNECTED = "!CONNECTED"
REFRESH = "!REFRESH"
DONE = "!DONE"
AUTHENTICATION = "!AUTH"

# triggers
CallOnResponse = "CallOnResponse"


class Server:
    def __init__(self, Name, auth=None, maxConn=120, maxConnReachTrigger=None, connectionRefreshTime=5):
        self.auth = auth
        self.name = Name
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
        self.mainConnection = None

        # the final connection from which the user fetched the response.
        self.lastActivityConn = None

        # for internal use of server.
        self.PORT = 5555
        self.HEADER = 64
        self.FORMAT = "utf-8"
        self.IpAddress = None
        self.runningStatus = False

        # connection refresh time can't be less then 5 sec
        if type(connectionRefreshTime) == int:
            if connectionRefreshTime < 5:
                self.connectionRefreshTime = 5
            else:
                self.connectionRefreshTime = connectionRefreshTime
        else:
            self.connectionRefreshTime = 5

        # Server is listening for new connection or not is on the server it will decide on the basic on maxConn.
        self.serverListeningStatus = False

        # server socket, it will store the socket object that we create with the help os socket.
        self.server = None

    @staticmethod
    def createConnData(conn, addr, name=None, status=True):
        return {'name': name, 'conn': conn, 'addr': addr, 'response': [], 'status': status}
        # if in case this connection having 'CallOnResponse' trigger then instead of storing response in the response
        # list it will call trigger and pass the received response in the trigger.

    def setTriggerOnMaxConnReach(self, trigger):
        self.trigger = maxConnReachTrigger

    def setAsMainConnection(self, name, ipAddress):
        for conn in self.connections:
            if name in conn:
                self.mainConnection = conn
                return True
        return False

    def getMainConnResponse(self):
        if self.mainConnection is not None:
            if len(self.mainConnection['response']) > 0:
                return self.mainConnection['response'].pop(0)

    def getResponse(self, name, ipAddress):
        if self.lastActivityConn is not None:
            if self.lastActivityConn['name'] == name and self.getConnectionIp(self.lastActivityConn) == ipAddress:
                print("From Last Active Connection: ")
                if len(self.lastActivityConn['response']) > 0:
                    return self.lastActivityConn['response'].pop(0)
        for conn in self.connections:
            if conn['name'] == name and self.getConnectionIp(conn) == ipAddress:
                self.lastActivityConn = conn
                print("Through itration")
                if len(conn['response']) > 0:
                    return conn['response'].pop(0)
        return None

    def authentication(self, auth):
        if auth is not None:
            if self.auth['user'] == auth['user'] and self.auth['password'] == auth['password']:
                return True
        return False

    @staticmethod
    def setCallOnResponse(connectionData, trigger):
        # For adding new trigger. if in case this function already having a trigger and user called this function again
        # in this case old trigger well get replaced with new one.
        connectionData[CallOnResponse] = trigger

    @staticmethod
    def removeCallOnResponse(connectionData):
        connectionData.pop(CallOnResponse)

    def startServer(self):
        try:
            self.IpAddress = socket.gethostbyname(socket.gethostname())
            address = (self.IpAddress, self.PORT)
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind(address)
            connectionListenerThread = threading.Thread(target=self.connectionListener)
            connectionListenerThread.start()
        except:
            self.runningStatus = False
            return False
        self.runningStatus = True
        self.serverListeningStatus = True
        return True

    def getTotalConnection(self):
        return len(self.connections)

    def checkForListening(self):
        if self.runningStatus:
            if self.getTotalConnection() < self.maxConn:
                if not self.serverListeningStatus:
                    connectionListenerThread = threading.Thread(target=self.connection_listener)
                    connectionListenerThread.start()
                    return True
                else:
                    return True
            else:
                self.serverListeningStatus = False
                return False
        else:
            self.serverListeningStatus = False

    def connectionListener(self):
        self.server.listen()
        while self.serverListeningStatus and self.runningStatus:
            try:
                conn, addr = self.server.accept()
                connectionThread = threading.Thread(target=self.connectionHandler,
                                                    args=(self.createConnData(conn, addr),))
                print(addr)
                if self.checkForListening():
                    connectionThread.start()
            except:
                continue

    def connectionHandler(self, connData):
        connection = connData['conn']
        time.sleep(2)
        # authentication confirmation if it's required.
        authRetryCounter = 3
        connection.settimeout(self.connectionRefreshTime)
        while authRetryCounter:
            try:
                self.sendMessage(connection, AUTHENTICATION)
                if self.auth is not None:
                    self.sendMessage(connection, {'auth': 'yes'})
                    message = self.receiveMessage(connection)
                    if not message:
                        return
                    if 'auth' not in message:
                        self.sendMessage(connection, DISCONNECT)
                        connection.close()
                        return
                    else:
                        if 'name' not in message:
                            self.sendMessage(connection, DISCONNECT)
                            connection.close()
                            return
                        else:
                            if not self.authentication(message['auth']):
                                self.sendMessage(connection, DISCONNECT)
                                connection.close()
                                return
                            else:
                                connData['name'] = message['name']
                else:
                    self.sendMessage(connection, {'auth': 'not'})
                    message = self.receiveMessage(connection)
                    if 'name' not in message:
                        self.sendMessage(connection, DISCONNECT)
                        connection.close()
                        return
                    connData['name'] = message['name']
            except socket.timeout:
                authRetryCounter -= 1
                continue
            break

        if not authRetryCounter:
            self.sendMessage(connection, DISCONNECT)
            connection.close()
            return

        # After authentication adding new entry of new connection. but it will not add any duplicate entry.
        if not self.addNewConnection(connData):
            self.sendMessage(connection, DISCONNECT)
            connection.close()
            self.checkForListening()
            return

        # Sending confirmation message to the client. Now Connection established.
        self.sendMessage(connection, CONNECTED)

        # Setting connection Refreshment time. if server is not receiving any message it will send a refresh message.
        refreshFlag = False
        counter = 0
        while self.runningStatus and connData['status']:
            try:
                message = self.receiveMessage(connection)
                # Non-Dict message is only for server use.
                if type(message) != dict:
                    # Here checking for some default message like triggers for the server or some special response.
                    if message == DONE and refreshFlag:
                        refreshFlag = False

                    """
                    if server received False message continuously for 3 time then the 
                    server will close the connection.
                    """
                    if counter < 3:
                        if not message:
                            counter += 1
                        else:
                            counter = 0
                    else:
                        connData['status'] = False
                        continue
                else:
                    """
                        Here managing the all response which is useful for the user.
                        if the CallOnResponse is available the it will call the trigger and pass the response in the 
                        trigger. otherwise the response will get append in the response list which is available in 
                        the connection data.
                        structure of connection data: 
                        case 1: {'name': name, 'conn': conn, 'addr': addr, 'response': [], 'status': status} in this 
                                the server append the received response in the response list which is in this dict.
                        case 2: {'name': name, 'conn': conn, 'addr': addr, 'response': [], 'status': status,
                                  'CallOnResponse': trigger}
                                in this case server will call the trigger and pass the received response in the trigger.
                                like: connData[CallOnResponse](message)
                    """
                    if CallOnResponse in connData:
                        connData[CallOnResponse](message)
                        continue
                    else:
                        connData['response'].append(message)

            except socket.timeout:
                if refreshFlag:
                    connData['status'] = False
                    continue
                else:
                    self.sendMessage(connection, REFRESH)
            except:
                connData['status'] = False
                continue

        self.removeConnection(self.getConnectionIp(connData), connData['name'])
        self.checkForListening()

    def addNewConnection(self, connectionData):
        if self.getTotalConnection() < self.maxConn:
            self.connections.append(connectionData)
            return True
        else:
            return False

    @staticmethod
    def getConnectionIp(connectionData):
        return connectionData['addr'][0]

    def removeConnection(self, connectionIp, name):
        for conn in self.connections:
            if self.getConnectionIp(conn) == connectionIp and conn['name'] == name:
                conn['status'] = False
                self.connections.remove(conn)
                try:
                    self.sendMessage(conn['conn'], DISCONNECT)
                    conn['conn'].close()
                except:
                    pass
                return True
        return False

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
        return conn.send(message)


def allDeviceConnected():
    print("Max Connection Limit Reached")


server = Server('Harvindar Singh', {'user': 'harvindar994', 'password': 12345678}, 4, allDeviceConnected, 5)
print(server.startServer())

while True:
    print("------------ Server Menu ------------")
    print("Server Running On: ", server.IpAddress, "Port: ", server.PORT)
    print("-------------------------------------")
    print("1. View All The Connection")
    print("2. Total Connected Device")
    print("3. Check All Status")
    print("4. View All Connected Device and IpAddress")
    print("5. Check Response Received From Device")
    print("6. Set A Connection As  Main Connection")
    print("7. Send message")
    print("8. total thread Running")
    print("9. Exit")
    print("Enter the choice: ")
    choice = input()
    if choice == '1':
        print("------------------ List of All Connections ---------------------")
        for conn in server.connections:
            print(conn)
        print("------------ List of All Connections Ended Here -----------------")
    elif choice == '2':
        print("Total Connection: ",server.getTotalConnection())
    elif choice == '3':
        print("Server Running Status: ", server.runningStatus)
        print("Server Listening Status: ", server.serverListeningStatus)
    elif choice == '4':
        print("------------------------ List of All Connected Devices --------------------------")
        for conn in server.connections:
            print("Device Name: ",conn['name'], "Device IpAddress: ",server.getConnectionIp(conn))
        print("------------------ List of All Connected Devices End's Here ---------------------")
    elif choice == '5':
        ip = input("Enter the IpAddress : ")
        name = input("Enter the name: ")
        print(server.getResponse(name, ip))
    elif choice == '6':
        ip = input("Enter the IpAddress : ")
        name = input("Enter the name: ")
        server.setAsMainConnection(name, ip)
    elif choice == '9':
        exit(0)

    elif choice == '7':
        ip = input("Enter the IpAddress : ")
        name = input("Enter the name: ")
        msg = input("Enter the message: ")
        for conn in server.connections:
            if conn['addr'][0] == ip and conn['name'] == name:
                server.sendMessage(conn['conn'], msg)
                break
    elif choice == '8':
        print("Total running thread: ", threading.active_count())
