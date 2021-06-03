import socket
import threading

# default messages.
DISCONNECT = '!DISCONNECT'
CONNECTED = "!CONNECTED"

# triggers
CallOnResponse = "CallOnResponse"


class Client:
    def __init__(self):
        # for internal use of client.
        self.PORT = 5555
        self.HEADER = 64
        self.FORMAT = "utf-8"

        self.Client = None
        self.connectionStatus = False

        # to store all received response.
        self.response = []  # but this this store response when CallOnResponse trigger is not set.

        # CallOnResponse trigger
        self.CallOnResponse = None  # if trigger is set client well call the trigger at each response.

    def getResponse(self):
        if len(self.response) > 0:
            return self.response.pop(0)

    def responseReceiver(self):
        pass

    def connect(self):
        pass

    def closeConnection(self):
        pass

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



class Client:
    def __init__(self):
        self.PORT = 5555
        self.ADDR = None
        self.HEADER = 64
        self.FORMATE = "utf-8"
        self.connection_status = False
        self.client = None
        self.received_response = []
        self.current_player_name = None
        self.receiver_thread_status = True

    def close_connection(self):
        try:
            self.client.close()
            self.client.shutdown(1)
            self.receiver_thread_status = False
            self.current_player_name = None
            self.received_response = []
            self.connection_status = False
            self.client = None
        except:
            return

    def getResponse(self):
        try:
            return self.received_response.pop()
        except IndexError:
            return None

    def connect(self, name, user_id, password):
        self.ADDR = (decode(user_id.upper()), self.PORT)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect(self.ADDR)
            print("Connected with server")
            self.connection_status = True
            receiver_thread = threading.Thread(target=self.receiver_thread)
            receiver_thread.start()
        except:
            self.connection_status = False
            print("Fail to connect with server")
            return
        self.send_data({'auth': password, 'name': name})

    def receiver_thread(self):
        while self.receiver_thread_status:
            try:
                data = receive_msg(self.client)
            except:
                print("Stoped receving")
                return
            if type(data) == dict:
                self.received_response.append(data)

    def send_data(self, data):
        try:
            send_message(self.client, data)
        except:
            print("Fail to send message.")
            return
        print("Message sended.")
