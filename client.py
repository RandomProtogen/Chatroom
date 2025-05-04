import socket
import threading

"""
to do:
make gui
when exit signal is called; cleanly closes connections
implement json for messages [date/time, username, username colour, message content]
sort of account creation (create username, colour)
colour for usernames
user list
/ commands (whispering, help, cls, possible admin commands)
connect to server
spam limit
client based profanity filtering
add image support (pls dear god no)
"""

# start of gui creation, oh boy
#class ClientApp(QMainWindow):
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import *
import socket, _thread, sys, time

"""
to do:
make gui 
make showing server info toggleable 
add users who are typing when input.text.changed input != ""
when exit signal is called; cleanly closes connections
implement json for messages [date/time, username, username colour, message content, first time join?]
sort of account creation (create username, colour)
colour for usernames
user list
/ commands (whispering, help, cls, possible admin commands)
connect to server
spam limit
client based profanity filtering
add image support (pls dear god no)
"""
colours = ["Red", "Blue"]

# start of gui creation, oh boy

class MainWindow(QMainWindow):
    
    def __init__(self): # when initialised
        super().__init__() # it was in the tutorial -_- canon event fr
        
        self.setWindowTitle("Rizzcord for Nerds") # Sets window title
        self.setMinimumSize(1200,800)

        my_icon = QIcon()
        my_icon.addFile('images\\image.png')
        self.setWindowIcon(my_icon) # sets window icon
        self.initialiseWidgets()


    def initialiseWidgets(self): # new function just to seperate the creation and initialization of widgets
        
        mainlayout = QGridLayout() # main layout that is the root of everything
        infoColumnnew = QVBoxLayout() # created so that columns dont overlap
        messageColumnnew = QVBoxLayout() # created for same reason
        infoColumn = QGridLayout() # creates 2 main columns for the gui
        messageColumn = QGridLayout()

        # User List widget
        userListMain = QVBoxLayout()
        userListTitle = QLabel("Users:") # creates the title
        userListMain.addWidget(userListTitle)
        self.userList = QLabel("User1\nUser2\nStupid Idiot mf udawgduahiodwjhaodjhwaoidjwaoidwa") # creates a larger text box 
        # User list should update when users change

        userListMain.addWidget(self.userList)
        infoColumn.addLayout(userListMain, 0, 0, 5, 0)


        # Server/User info

        # IP
        serverIPMain = QHBoxLayout()
        ipTitle = QLabel("Server IP: ")
        serverIPMain.addWidget(ipTitle)
        ipEntry = QLineEdit()
        serverIPMain.addWidget(ipEntry)
        infoColumn.addLayout(serverIPMain, 6, 0, 1, 0)

        # Port (pretty much copy and paste of IP)

        serverPortMain = QHBoxLayout()
        portTitle = QLabel("Port: ")
        serverPortMain.addWidget(portTitle)
        portEntry = QLineEdit()
        serverPortMain.addWidget(portEntry)
        infoColumn.addLayout(serverPortMain, 7, 0, 1, 0)

        # Username
        usernameMain = QHBoxLayout()
        usernameTitle = QLabel("Username: ")
        usernameMain.addWidget(usernameTitle)
        usernameEntry = QLineEdit()
        usernameMain.addWidget(usernameEntry)
        infoColumn.addLayout(usernameMain, 8, 0, 1, 0)

        # Colour

        coloursMain = QHBoxLayout()
        coloursTitle = QLabel("Colours: ")
        coloursMain.addWidget(coloursTitle)
        coloursOptions = QComboBox()
        coloursOptions.addItems(["Red", "Blue", "1", "2", "3"])
        coloursMain.addWidget(coloursOptions)
        infoColumn.addLayout(coloursMain, 9, 0, 1, 0)

        # Connect
        self.connected = False
        self.connectButton = QPushButton("Connect")
        self.connectButton.clicked.connect(self.connectToServer)
        infoColumn.addWidget(self.connectButton, 10, 0, 1, 0)



        # Messages area
        self.messagesdisplay = QTextEdit() #creates log text box
        self.messagesdisplay.setReadOnly(True) #makes it so you cant edit
        messageColumn.addWidget(self.messagesdisplay)
        
        # messageEntry
        messageEntryMain = QHBoxLayout()
        self.messageEntry = QLineEdit()
        self.messageEntry.setPlaceholderText('Enter Message                                       ')
        messageEntryMain.addWidget(self.messageEntry)
        sendButton = QPushButton("Send")
        messageEntryMain.addWidget(sendButton)
        messageColumn.addLayout(messageEntryMain, 1, 0)



        # places the two main columns
        messageColumnnew.addLayout(messageColumn)
        infoColumnnew.addLayout(infoColumn)

        
        
        mainlayout.addLayout(infoColumnnew, 0, 0, 0, 0) # Adds a column for info that spans 1 column 
        mainlayout.addLayout(messageColumnnew, 0, 1, 0, 3) # Adds a  column for messages (sending and receiving) that spans 4 columns

        # finally places the mainlayout
        centralWidget = QWidget() #empty widget to put grid into, code breaks if this isnt done
        centralWidget.setLayout(mainlayout)
        self.setCentralWidget(centralWidget)


    def usersChanged(self):
        
        # get the user list from server OR have a variable that gets updated when user join/leave
        self.userList.setText("data from server")
    
    def connectToServer(self):
        print("test")
        self.messagesdisplay.append("test")
        # also change button purpose to be disconnect
        if self.connected == False:
            self.connectButton.setText("Disconnect")
            self.connected = True
        else:
            self.connectButton.setText("Connect")
            self.connected = False
        
        

'''
if __name__ == "__main__": # checks if this file is being run
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show() # actually shows the window wow
    
    app.exec()
'''

class ChatClient:
    def __init__(self, host, port):
        self.server_address = (host, port)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.username = None
        self.is_running = True

    def connect(self):
        try:
            self.client_socket.connect(self.server_address)
            print("Connected to the server.")
            self.username = input("Enter your username: ")
            self.client_socket.send(self.username.encode())
            print("Welcome to the chatroom!")
            threading.Thread(target=self.receive_messages, daemon=True).start()
            self.send_messages()
        except Exception as e:
            print(f"Error connecting to server: {e}")
            self.client_socket.close()

    def receive_messages(self):
        while self.is_running:
            try:
                message = self.client_socket.recv(2048).decode()
                if message:
                    print(message)
                else:
                    print("Disconnected from server.")
                    self.is_running = False
                    self.client_socket.close()
            except Exception as e:
                print(f"Error receiving message: {e}")
                self.is_running = False
                self.client_socket.close()

    def send_messages(self):
        while self.is_running:
            message = input()
            if message.lower() == 'exit':
                self.is_running = False
                self.client_socket.close()
                print("Disconnected from the chat.")
                break
            self.client_socket.send(message.encode())

if __name__ == "__main__":
    host = socket.gethostbyname(socket.gethostname())
    port = int(input("Enter server port (default 42069): ") or 42069)
    
    client = ChatClient(host, port)
    client.connect()






























'''
def receive_messages(sock):
    while True:
        try:
            msg = sock.recv(2048).decode()
            if not msg:
                print("Connection closed by the server.")
                break
            print(msg)
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

def main():
    server_ip = input("Enter server IP address: ")#socket.gethostbyname(socket.gethostname())
    server_port = input("Enter port: ")
    
    try:
        server_port = int(server_port)
    except ValueError:
        print("Port must be an integer.")
        return

    callsign = input("Enter your username: ")
    if callsign == "":
        print("Please enter a username:")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((server_ip, server_port))
        print(f"Connected to server at {server_ip}:{server_port}")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    # Send the callsign to the server
    sock.send(callsign.encode())

    # Receive welcome message
    try:
        welcome = sock.recv(2048).decode()
        print(welcome)
    except Exception as e:
        print(f"Error receiving welcome message: {e}")
        sock.close()
        return

    # Start thread to listen for messages from server
    receive_thread = threading.Thread(target=receive_messages, args=(sock,), daemon=True)
    receive_thread.start()

    # Main loop to send messages
    try:
        while True:
            msg = input()
            if msg.lower() == "/quit":
                print("Disconnecting...")
                break
            if msg.strip() == "":
                continue
            sock.send(msg.encode())
    except KeyboardInterrupt:
        print("\nDisconnecting...")

    sock.close()

if __name__ == "__main__":
    main()
'''

