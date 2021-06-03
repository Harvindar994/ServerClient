import socket
import threading

# default messages.
DISCONNECT = '!DISCONNECT'
CONNECTED = "!CONNECTED"

# triggers
CallOnResponse = "CallOnResponse"


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
        return {'name': name, 'conn': conn, 'addr': addr, 'response': [], 'status': status}
        # if in case this connection having 'CallOnResponse' trigger then instead of storing response in the response
        # list it will call trigger and pass the received response in the trigger.

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

    def authentication(self, auth):
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
                if self.checkForListening():
                    connectionThread.start()
            except:
                continue

    def connectionHandler(self, connData):
        connection = connData['conn']
        if self.auth is None:
            self.sendMessage(connection, {'auth': 'yes'})
            message = self.receiveMessage(connection)
            if 'auth' not in message:
                return
            else:
                if 'name' not in message:
                    return
                else:
                    if not self.authentication(message['auth']):
                        return
                    else:
                        connData['name'] = message['name']
        else:
            self.sendMessage(connection, {'auth': 'not'})
            message = self.receiveMessage(connection)
            if 'name' not in message:
                return
            connData['name'] = message['name']
        if not self.addNewConnection(connData):
            self.checkForListening()
            return
        while self.runningStatus and connData['status']:
            try:
                message = self.receiveMessage(connection)
                print(message)
                if CallOnResponse in connData:
                    connData[CallOnResponse](message)
                    continue
                else:
                    connData['response'].append(message)
                # Here i Will add all the code related to the response.
            except:
                self.removeConnection(self.getConnectionIp(connData), connData['name'])
                self.checkForListening()
                return
        self.removeConnection(self.getConnectionIp(connData), connData['name'])
        self.checkForListening()

    def addNewConnection(self, connectionData):
        for conn in self.connections:
            if self.getConnectionIp(conn) == self.getConnectionIp(connectionData) and conn['name'] == connectionData[
                'name']:
                return False
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
                self.sendMessage(conn['conn'], DISCONNECT)
                conn['conn'].close()
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
        conn.send(message)


def allDeviceConnected():
    print("Max Connection Limit Reached")


server = Server('Harvindar Singh', {'user': 'harvindar994', 'password': 12345678}, 4, allDeviceConnected)
server.startServer()
