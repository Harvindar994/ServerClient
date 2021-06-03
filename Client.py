import socket
import threading

# default messages.
DISCONNECT = '!DISCONNECT'
CONNECTED = "!CONNECTED"

# triggers
CallOnResponse = "CallOnResponse"


class Client:
    def __init__(self, retryOnDisconnect=2):
        # info required to connect to server.
        self.PORT = 5555
        self.IpAddress = None
        self.auth = None

        # for internal use of client.
        self.retryOnDisconnect = retryOnDisconnect
        self.name = socket.gethostname()
        self.HEADER = 64
        self.FORMAT = "utf-8"

        self.Client = None
        self.connectionStatus = False
        self.receiverRunningStatus = False

        # to store all received response.
        self.response = []  # but this this store response when CallOnResponse trigger is not set.

        # CallOnResponse trigger
        self.CallOnResponse = None  # if trigger is set client well call the trigger at each response.

    def getResponse(self):
        if len(self.response) > 0:
            return self.response.pop(0)

    def connectAgain(self, IpAddress, Port=5555):
        address = (IpAddress, Port)
        self.Client.connect(address)

    def responseReceiver(self):
        """
        this function will perform in different thread
        :return: Nothing.
        """
        self.receiverRunningStatus = True
        while self.connectionStatus:
            message = self.receiveMessage()
            if type(message) == str:
                if message == DISCONNECT:
                    self.receiverRunningStatus = False
                    self.connectionStatus = False
                    if self.retryOnDisconnect > 0:
                        self.retryOnDisconnect -= 1
                        self.connectAgain(self.IpAddress, self.PORT)
                    return
                elif message == CONNECTED:
                    self.receiverRunningStatus = True
                    self.connectionStatus = True
                    print("Connected with server")
            elif type(message) == dict:
                if 'auth' in message:
                    if message['auth'] == 'yes':
                        self.sendMessage({'auth': self.auth, 'name': self.name})
                    elif message['auth'] == 'no':
                        self.sendMessage({'name': self.name})
            if self.connectionStatus:
                if self.CallOnResponse is not None:
                    self.CallOnResponse(message)
                else:
                    self.response.append(message)

    def connect(self, ipAddress, auth=None, Port=5555):
        self.auth = auth
        self.PORT = Port
        self.IpAddress = ipAddress
        address = (ipAddress, self.PORT)
        self.Client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.Client.connect(address)
            receiverThread = threading.Thread(target=self.responseReceiver)
            receiverThread.start()
            self.receiverRunningStatus = True
            return True
        except:
            self.connectionStatus = False
            print("Fail to connect with server")
            return False

    def closeConnection(self):
        self.sendMessage(DISCONNECT)
        self.connectionStatus = False
        self.response = []
        self.receiverRunningStatus = False
        self.Client.close_connection()
        self.Client = None

    def setCallOnResponse(self, trigger):
        self.CallOnResponse = trigger

    def receiveMessage(self):
        try:
            msg_length = self.Client.recv(self.HEADER).decode(self.FORMAT)
        except ConnectionResetError:
            return False
        if msg_length:
            try:
                msg_length = int(msg_length)
            except:
                return False
            msg = self.Client.recv(msg_length)
            try:
                message = msg.decode(self.FORMAT)
            except UnicodeDecodeError:
                message = pickle.loads(msg)
            return message

    def sendMessage(self, msg):
        if type(msg) == str:
            message = msg.encode(self.FORMAT)
        else:
            message = pickle.dumps(msg)
        msg_length = len(message)
        send_length = str(msg_length).encode(self.FORMAT)
        send_length += b" " * (self.HEADER - len(send_length))
        self.Client.send(send_length)
        self.Client.send(message)
