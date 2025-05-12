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



class MainWindow(QMainWindow):
    
    def __init__(self): # when initialised
        super().__init__() # it was in the tutorial -_- canon event fr
        self.receivedMessage = {}
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

        # Sample button for testing purposes
        '''
        self.testButton = QPushButton("Test")
        self.testButton.clicked.connect(self.setText)
        '''
        

        # Messages area
        self.messagesdisplay = QTextEdit() #creates log text box
        self.messagesdisplay.setReadOnly(True) #makes it so you cant edit
        messageColumn.addWidget(self.messagesdisplay)
        
        # messageEntry
        messageEntryMain = QHBoxLayout()
        self.messageEntry = QLineEdit()
        self.messageEntry.setPlaceholderText('Enter Message')
        self.messageEntry.returnPressed.connect(self.sendMessage)
        self.messageEntry.setEnabled(True)
        messageEntryMain.addWidget(self.messageEntry)
        self.sendButton = QPushButton("Send")
        self.sendButton.clicked.connect(self.sendMessage)
        self.sendButton.setEnabled(True)
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

    def setText(self):
        users = self.userList.toPlainText()
        users = users.replace("Ian", "")
        users = users.replace("\n\n","\n")
        print(users)
        self.userList.setText(f"{users}\n")


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
            print("sent")
            # This is where the message will be then sent as a dictionary
            self.sock.send(json.dumps({"type": "message", "username": self.usernameEntry.text(), "content": message, "colour": ""}).encode())
            #self.messagesdisplay.append(f"<{self.messageinfo['username']}> {self.messageinfo['content']}") # change this to be parts of the json stuff
            self.messageEntry.setText("")



    def closeEvent(self, event: QCloseEvent):
        print("dead")
        self.abandonConnection()
        if self.connected:
            print("you stupid idiot mf")
            self.sock.close()


    def establishConnection(self):
        self.ip = str(self.ipEntry.text()) or "127.0.0.1"
        self.port = int(self.portEntry.text()) or 42069
        self.username = self.usernameEntry.text() or "placeholder"
        self.sock = s.socket(s.AF_INET, s.SOCK_STREAM) # creates an instance of socket, SOCK_STREAM makes it tcp/ip
        try:
            self.sock.connect((self.ip, self.port))
            # self.sock.send(json.dumps({"type":"join", "username":self.username}).encode())  FOR WHEN IAN UPDATES THIS
            self.sock.send(self.username.encode())
        except WindowsError as e:
            print(e)
            return "error"
        
        
        self.recvThread = threading.Thread(target=self.receiveThread, args=(self.sock,)) 
        self.recvThread.start()

        self.callsign = str(self.usernameEntry.text())
    

    def receiveThread(self, sock):
        
        while True:
            
            try:
                receivedMessagejson = sock.recv(4096).decode()
                self.receivedMessage = json.loads(receivedMessagejson)
                print("Raw Input:", self.receivedMessage)
                #self.receivedMessage = self.receivedMessage.strip()
                
            except WindowsError:
                self.messagesdisplay.append("Server has closed")
                
            except Exception as e:
                print("Error")
                print(e)
                self.messagesdisplay.append(f"Error: {e}")
                print("you stupid idiot mf 2")
                time.sleep(1)
                sock.close()
            
            try:
                if not isinstance(self.receivedMessage, dict) or "type" not in self.receivedMessage:
                    self.messagesdisplay.append("Error receiving message from server")
                    print("Error Receiving:", self.receivedMessage)
                    continue
                elif self.receivedMessage.get("type") == "timeout":
                    self.messagesdisplay.append(self.receivedMessage.get("content"))
                    self.timeoutThread = threading.Thread(target=self.timeout)
                    self.timeoutThread.start()

                elif self.receivedMessage.get("type") == "welcome":
                    userListString = "" 
                    for i in self.receivedMessage.get("users"):
                        userListString = userListString+"\n"+i
                    self.userList.setText(userListString)
                    self.messagesdisplay.append(self.receivedMessage.get("content"))
                
                elif self.receivedMessage.get("type") == "kick":
                    self.messagesdisplay.append()
                    self.messagesdisplay.append(self.receivedMessage.get("content"))
                    

                elif self.receivedMessage.get("type") == "join":
                    self.userList.append(self.receivedMessage.get("user"))
                    self.messagesdisplay.append(self.receivedMessage.get("content"))
                
                elif self.receivedMessage.get("type") == "leave":
                    users = self.userList.toPlainText()
                    users.replace(f"\n{self.receivedMessage.get("user")}", "")
                    users = users.replace("\n\n","\n") # removes whitespace .strip() didnt work for some reason
                    self.userList.setText(f"{users}\n")

                    self.messagesdisplay.append(self.receivedMessage.get("content"))


                elif self.receivedMessage.get("type") == "message":
                    self.messagesdisplay.append(f"<{self.receivedMessage.get("user")} {self.receivedMessage.get("content")}")
                
                elif self.receivedMessage.get("type") == "whisper":
                    self.messagesdisplay.append(f"<i>{self.receivedMessage.get("user")} whispers to you: {self.receivedMessage.get("content")}")

            
            except Exception as e:
                print(e)
                try:
                    #self.messagesdisplay.append(self.receivedMessage)
                    print()
                except Exception as e:
                    print(e)
                    self.messagesdisplay.append("Error receiving message.")
    
    def timeout(self, minutes):
        self.messageEntry.setEnabled(False)
        self.sendButton.setEnabled(False)
        try:
            time.sleep(int(minutes)*60) # minutes are given by the server but time.sleep works in seconds so it needs to be multiplied by 60
        except:
            self.messagesdisplay.append("huh there was an error timing you out, funny that")
        self.messageEntry.setEnabled(True)
        self.sendButton.setEnabled(True)


    def abandonConnection(self):
        print()
        #self.sock.close()

        


if __name__ == "__main__": # checks if this file is being run
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show() # actually shows the window wow
    
    app.exec()



"""
stuff to test:

Buffer in receive thread:



def receiveThread(self, sock):
    buffer = ""
    while True:
        try:
            data = sock.recv(4096).decode()
            if not data:
                self.messagesdisplay.append("Server closed the connection.")
                break

            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                try:
                    self.receivedMessage = json.loads(line)
                    print("Raw Input:", self.receivedMessage)
                except json.JSONDecodeError as e:
                    print("JSON decode error:", e)
                    continue

                if not isinstance(self.receivedMessage, dict) or "type" not in self.receivedMessage:
                    self.messagesdisplay.append("Error receiving message from server")
                    continue

                # Handle the message here as before...
                # e.g., self.messagesdisplay.append(self.receivedMessage.get('content'))

        except Exception as e:
            print("Receive thread error:", e)
            self.messagesdisplay.append(f"Error: {e}")
            sock.close()
            break

"""
