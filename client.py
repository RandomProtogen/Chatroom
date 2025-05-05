"""
to do:
make gui DONE
when exit signal is called; cleanly closes connections
make showing server info toggleable
implement json for messages [date/time, username, username colour, message content] pretty much done
add users who are typing when input.text.changed input != ""
sort of account creation (create username, colour)
colour for usernames
user list
/ commands (whispering, help, cls, possible admin commands)
connect to server
spam limit
client based profanity filtering
add image support (pls dear god no)
"""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import *
import socket, _thread, sys, time, threading

# start of gui creation, oh boy

class MainWindow(QMainWindow):
    
    def __init__(self): # when initialised
        super().__init__() # it was in the tutorial -_- canon event fr
        
        self.setWindowTitle("Rizzcord for Nerds") # Sets window title
        self.setMinimumSize(1200,600)

        my_icon = QIcon()
        my_icon.addFile('images\\image.png')
        self.setWindowIcon(my_icon) # sets window icon
        self.initialiseWidgets()


    def initialiseWidgets(self): # new function just to seperate the creation and initialization of widgets
        
        mainlayoutnew = QHBoxLayout()
        mainlayout = QGridLayout() # main layout that is the root of everything
        infoColumnnew = QVBoxLayout() # created so that columns dont overlap
        messageColumnnew = QVBoxLayout() # created for same reason
        infoColumn = QGridLayout() # creates 2 main columns for the gui
        messageColumn = QGridLayout()

        # User List widget
        userListMain = QVBoxLayout()
        userListTitle = QLabel("Users:") # creates the title
        userListMain.addWidget(userListTitle)
        self.userList = QTextEdit() #creates log text box
        self.userList.setReadOnly(True)
        #self.userList = QLabel("User1\nUser2\nStupid Idiot mf udawgduahiodwjhaodjhwaoidjwaoidwa") # creates a larger text box 
        # User list should update when users change

        userListMain.addWidget(self.userList)
        infoColumnnew.addLayout(userListMain)


        # Server/User info

        # IP
        serverIPMain = QHBoxLayout()
        ipTitle = QLabel("Server IP: ")
        serverIPMain.addWidget(ipTitle)
        self.ipEntry = QLineEdit()
        serverIPMain.addWidget(self.ipEntry)
        self.ipEntry.setText("127.0.0.1")
        infoColumnnew.addLayout(serverIPMain)

        # Port (pretty much copy and paste of IP)

        serverPortMain = QHBoxLayout()
        portTitle = QLabel("Port: ")
        serverPortMain.addWidget(portTitle)
        self.portEntry = QLineEdit()
        serverPortMain.addWidget(self.portEntry)
        self.portEntry.setText("42069")
        infoColumnnew.addLayout(serverPortMain)

        # Username
        usernameMain = QHBoxLayout()
        usernameTitle = QLabel("Username: ")
        usernameMain.addWidget(usernameTitle)
        self.usernameEntry = QLineEdit()
        usernameMain.addWidget(self.usernameEntry)
        infoColumnnew.addLayout(usernameMain)

        # Colour

        coloursMain = QHBoxLayout()
        coloursTitle = QLabel("Colours: ")
        coloursMain.addWidget(coloursTitle)
        self.coloursOptions = QComboBox()
        self.coloursOptions.addItems(["Red", "Blue", "1", "2", "3"])
        coloursMain.addWidget(self.coloursOptions)
        infoColumnnew.addLayout(coloursMain)

        # Connect
        self.connected = False
        self.connectButton = QPushButton("Connect")
        self.connectButton.clicked.connect(self.connectToServer)
        infoColumnnew.addWidget(self.connectButton)



        # Messages area
        self.messagesdisplay = QTextEdit() #creates log text box
        self.messagesdisplay.setReadOnly(True) #makes it so you cant edit
        messageColumn.addWidget(self.messagesdisplay)
        
        # messageEntry
        messageEntryMain = QHBoxLayout()
        self.messageEntry = QLineEdit()
        self.messageEntry.setPlaceholderText('Enter Message')
        self.messageEntry.returnPressed.connect(self.sendMessage)
        self.messageEntry.setEnabled(False)
        messageEntryMain.addWidget(self.messageEntry)
        self.sendButton = QPushButton("Send")
        self.sendButton.clicked.connect(self.sendMessage)
        self.sendButton.setEnabled(False)
        messageEntryMain.addWidget(self.sendButton)
        messageColumn.addLayout(messageEntryMain, 1, 0)



        # places the two main columns

        infoColumnnew.addLayout(infoColumn)
        messageColumnnew.addLayout(messageColumn)
        

        
        mainlayoutnew.addLayout(infoColumnnew, 1)
        mainlayoutnew.addLayout(messageColumnnew, 4)
        
        #mainlayout.addLayout(messageColumnnew, 0, 1, 0, 3) # Adds a  column for messages (sending and receiving) that spans 4 columns
        #mainlayout.addLayout(infoColumnnew, 0, 0, 0, 0) # Adds a column for info that spans 1 column 
        

        # finally places the mainlayout
        centralWidget = QWidget() #empty widget to put grid into, code breaks if this isnt done
        centralWidget.setLayout(mainlayoutnew)
        #centralWidget.setLayout(mainlayout)
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
            self.ipEntry.setEnabled(False)
            self.portEntry.setEnabled(False)
            self.usernameEntry.setEnabled(False)
            self.coloursOptions.setEnabled(False)
            self.messageEntry.setEnabled(True)
            self.sendButton.setEnabled(True)
        else:
            self.connectButton.setText("Connect")
            self.connected = False
            self.ipEntry.setEnabled(True)
            self.portEntry.setEnabled(True)
            self.usernameEntry.setEnabled(True)
            self.coloursOptions.setEnabled(True)
            self.messageEntry.setEnabled(False)
            self.sendButton.setEnabled(False)
    
    def sendMessage(self):
        message = self.messageEntry.text()
        if self.usernameEntry.text() == "":
            self.messagesdisplay.append("<Please enter a Username>")
            return
        elif self.messageEntry.text() == "":
            return
        elif message[0] == "/":
            self.messageEntry.setText("")
            if message == "/help":
                self.messagesdisplay.append("Commands are:\n/help - Brings up this list\n/whisper or /w - privately message a user\n/clear - Clears the message log\n/profanity add/remove/toggle - Adds to or removes from the profanity or toggles it on or off\n/disconnect - If you can't manage to find the button yourself")
            else:
                self.messagesdisplay.append(f"'{message}' not found")

        else:
            
            self.messageinfo = {
                "type": "message",
                "username": self.usernameEntry.text(),
                "message": message
            }
            print("sent")
            # This is where the message will be then sent as a dictionary
            self.messagesdisplay.append(f"<{self.messageinfo["username"]}> {self.messageinfo["message"]}") # change this to be parts of the json stuff
            self.messageEntry.setText("")

    def windowClosed(self, event: QCloseEvent):
        print("window closed") # add ability to cleanly close connection when window closed


        


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
    app = QApplication(sys.argv)
    window = QWidget()
    window.show()
    app.exec()

    
    
    host = socket.gethostbyname(socket.gethostname())
    port = int(input("Enter server port (default 42069): ") or 42069)
    
    client = ChatClient(host, port)
    client.connect()

'''




























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
