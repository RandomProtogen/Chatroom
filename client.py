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

from PySide6.QtCore import QSize, Qt, QThread
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtCore import *
import _thread, sys, time, threading, json
import socket as s

# networking part
# start of gui creation, oh boy

class UISignals():
    log = Signal(str)
    userlst = Signal(str)

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
        userListTitle.setStyleSheet("font-weight: bold; font-size: 16px;")
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
        self.ipEntry.setText(s.gethostbyname(s.gethostname()))
        infoColumnnew.addLayout(serverIPMain)

        # Port (pretty much copy and paste of IP)

        serverPortMain = QHBoxLayout()
        portTitle = QLabel("Port: ")
        serverPortMain.addWidget(portTitle)
        self.portEntry = QLineEdit()
        self.portEntry.setMaxLength(5)
        self.portEntry.setValidator(QIntValidator(0,65535))
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
        # also change button purpose to be disconnect
        if self.connected == False:
            if len(self.usernameEntry.text()) <= 2 or len(self.usernameEntry.text()) >= 16:
                self.messagesdisplay.append("Username must be no greater than 12 characters and at least 2 characters long")
                return

            elif self.establishConnection() == "error":
                self.messagesdisplay.append("Server Not Found")
                return
            self.connectButton.setText("Disconnect")
            #holy fuck this shit is wack, if this comment is still in my man is a vibe coder, but his vibes suck
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
            self.abandonConnection()
    
    def sendMessage(self):
        message = self.messageEntry.text()

        if self.messageEntry.text() == "":
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
                "content": message,
                "colour": "" # placeholder might add or remove
            }
            print("sent")
            # This is where the message will be then sent as a dictionary
            #self.messagesdisplay.append(f"<{self.messageinfo['username']}> {self.messageinfo['content']}") # change this to be parts of the json stuff
            self.sock.send(json.dumps(self.messageinfo).encode())
            self.messageEntry.setText("")

    def closeEvent(self, event: QCloseEvent):
        print("dead")
        self.abandonConnection()
        #if self.connected():
        self.sock.close()

    def establishConnection(self):
        self.ip = str(self.ipEntry.text()) or "127.0.0.1"
        self.port = int(self.portEntry.text()) or 42069
        self.callsign = self.usernameEntry.text() or "placeholder"
        self.sock = s.socket(s.AF_INET, s.SOCK_STREAM) # creates an instance of socket, SOCK_STREAM makes it tcp/ip
        try:
            self.sock.connect((self.ip, self.port))
            #self.sock.send(self.callsign.encode())
        except WindowsError as e:
            return "error"
        
        self.recvThread = threading.Thread(target=self.receiveThread, args=(self.sock,)) 
        self.recvThread.start()

        self.callsign = str(self.usernameEntry.text())
        try:
            self.sock.send(self.callsign.encode())
        except Exception as e:
            print(e)
            return "error"
    

    def receiveThread(self, sock):        
        while True:
            try:
                receivedMessagejson = sock.recv(4096).decode()
                receivedMessage = json.loads(receivedMessagejson)
                #receivedMessage = receivedMessage.strip()
                if receivedMessage['type'] == 'message':
                    self.messagesdisplay.append(f'<{receivedMessage['username']}> {receivedMessage['content']}') 
                elif receivedMessage["type"] == "timeout":     
                    self.messagesdisplay.append(f'{receivedMessage['msg']}') 
                    print(receivedMessage)
                elif receivedMessage["type"] == "welcome" or "join" or "leave":
                    self.messagesdisplay.append(receivedMessage["content"])
                    #self.userList.setPlainText("")
                    for i in receivedMessage["users"]:
                        self.userList.append(i)
                
            except WindowsError:
                self.messagesdisplay.append("Server has closed")
            except Exception as e:
                print(f"Error: {e}")
                self.messagesdisplay.append(f"Error: {e}")
                sock.close()
    
    def abandonConnection(self):
        self.sock.close()
        print("placeholder")
        
if __name__ == "__main__": # checks if this file is being run
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show() # actually shows the window wow
    
    app.exec()



