import socket
import threading
import pickle
import time

# default messages.
DISCONNECT = '!DISCONNECT'
CONNECTED = "!CONNECTED"
REFRESH = "!REFRESH"
DONE = "!DONE"
AUTHENTICATION = "!AUTH"


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

    def connectAgain(self):
        if self.Client is not None:
            self.Client.close()
        address = (self.IpAddress, self.PORT)
        self.Client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.Client.connect(address)
            return True
        except:
            self.connectionStatus = False
            print("Retry: Fail to connect with server")
            return False

    def responseReceiver(self):
        """
        this function will perform in different thread
        :return: Nothing.
        """
        counter = 0
        authFlag = False
        while self.receiverRunningStatus:
            try:
                message = self.receiveMessage()
                print(message)
                # Non-Dict message is only for server use.
                if type(message) == str or type(message) == bool:
                    if message == DISCONNECT:
                        self.receiverRunningStatus = False
                        self.Client.close()
                        self.connectionStatus = False

                    elif message == CONNECTED:
                        self.receiverRunningStatus = True
                        self.connectionStatus = True
                        authFlag = False
                        print("Connected with server")

                    elif message == REFRESH:
                        self.sendMessage(DONE)

                    elif not message:
                        if counter < 3:
                            counter += 1
                        else:
                            self.connectionStatus = False

                    elif message == AUTHENTICATION:
                        authFlag = True

                    else:
                        counter = 0

                elif type(message) == dict:
                    if authFlag:
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

            except:
                self.connectionStatus = False

            if not self.connectionStatus and not authFlag:
                if self.retryOnDisconnect > 0:
                    self.retryOnDisconnect -= 1
                    self.connectAgain()
                else:
                    self.receiverRunningStatus = False
                    self.Client.close()
                    self.connectionStatus = False

    def connect(self, ipAddress, auth=None, Port=5555):
        if self.receiverRunningStatus:
            return
        self.auth = auth
        self.PORT = Port
        self.IpAddress = ipAddress
        address = (ipAddress, self.PORT)
        self.Client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.Client.connect(address)
            self.receiverRunningStatus = True
            receiverThread = threading.Thread(target=self.responseReceiver)
            receiverThread.start()
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


client = Client()
while True:
    print("----------------- Client Menu -----------------")
    print("1. Connect")
    print("2. Send Message")
    print("3. Get Response")
    print("4. View all response")
    print("5. Status")
    print("6. Exit")
    choice = input()
    if choice == '1':
        client.connect('192.168.43.188', {'user': 'harvindar994', 'password': 12345678})
    elif choice == '2':
        message = input()
        client.sendMessage({'message': message})
    elif choice == '3':
        print(client.getResponse())
    elif choice == '4':
        for response in Client.response:
            print(response)
    elif choice == '5':
        print('Connection Status: ', client.connectionStatus, ", receiver Status: ",client.receiverRunningStatus)
    elif choice == '6':
        exit(0)
